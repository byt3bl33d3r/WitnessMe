#! /usr/bin/env python3

import threading
import logging
import asyncio
import os
import argparse
import signal
import stats
import socket
import functools
import pyppeteer
from database import ScanDatabase
from datetime import datetime
from ipaddress import ip_address, ip_network, summarize_address_range
from asyncio import FIRST_COMPLETED
from argparse import ArgumentDefaultsHelpFormatter
from time import sleep
from urllib.parse import urlparse

#logging.getLogger('pyppeteer').setLevel(logging.ERROR)
logging.basicConfig(format="%(asctime)s [%(levelname)s] - %(filename)s: %(funcName)s - %(message)s", level=logging.INFO)

def patch_pyppeteer():
    """
    There's a bug in pyppeteer currently (https://github.com/miyakogi/pyppeteer/issues/62) which closes the websocket connection to Chromium after ~20s.
    This is a hack to fix that. Taken from https://github.com/miyakogi/pyppeteer/pull/160
    """
    import pyppeteer.connection
    original_method = pyppeteer.connection.websockets.client.connect

    def new_method(*args, **kwargs):
        kwargs['ping_interval'] = None
        kwargs['ping_timeout'] = None
        return original_method(*args, **kwargs)

    pyppeteer.connection.websockets.client.connect = new_method

def generate_urls(targets):
    for target in targets:
        for host in generate_targets(target):
            for port in args.ports:
                for scheme in ["http", "https"]:
                    yield f"{scheme}://{host}:{port}"

def generate_targets(target):
    try:
        if '-' in target:
            start_ip, end_ip = target.split('-')
            try:
                end_ip = ip_address(end_ip)
            except ValueError:
                first_three_octets = start_ip.split(".")[:-1]
                first_three_octets.append(end_ip)
                end_ip = ip_address(
                            ".".join(first_three_octets)
                        )

            for ip_range in summarize_address_range(ip_address(start_ip), end_ip):
                for ip in ip_range:
                    yield str(ip)
        else:
            for ip in ip_network(target, strict=False): yield str(ip)
    except ValueError:
        yield str(target)

async def resolve_host(host):
    try:
        name,_,ips = socket.gethostbyaddr(host)
        return name, ips[0]
    except Exception:
        return '', ''

async def on_request(request):
    pass
    #logging.info(f"on_request() called: url: {request.url}")

async def on_response(response):
    pass
    #logging.info(f"on_response() called, url: {response.url}")

async def on_requestfinished(request):
    pass
    #logging.info(f"on_requestfinished() called, url: {request.url}")

async def screenshot(url, page):
    #async with sem:
    #logging.info(f"Taking screenshot of {url}")
    parsed_url = urlparse(url)

    hostname, ip = await resolve_host(parsed_url.hostname)
    screenshot_path = f'./{report_folder}/{parsed_url.scheme}_{parsed_url.hostname}_{parsed_url.port}.png'

    """
        The page.goto() options might need to be tweaked depending on testing in real environments.

        https://github.com/GoogleChrome/puppeteer/blob/master/docs/api.md#pagewaitfornavigationoptions

        load - consider navigation to be finished when the load event is fired.
        domcontentloaded - consider navigation to be finished when the DOMContentLoaded event is fired.
        networkidle0 - consider navigation to be finished when there are no more than 0 network connections for at least 500 ms.
        networkidle2 - consider navigation to be finished when there are no more than 2 network connections for at least 500 ms.
    """

    response = await page.goto(
        url,
        options={
            "waitUntil": "networkidle0"
        }
    )

    await page.screenshot(
        {
            'path': screenshot_path,
            'fullPage': True
        }
    )

    result_dict = {
        "url": url,
        "screenshot_path": screenshot_path,
        "ip": ip,
        "hostname": hostname,
        "port": parsed_url.port,
        "svc_name": parsed_url.scheme,
        "title": await page.title(), # await page.evaluate('document.title')
        "headers": response.headers
    }

    logging.info(result_dict)
    return result_dict

def task_watch(queue):
    while True:
        sleep(1)
        #total_tasks = queue.qsize()
        logging.info(f"total: {stats.inputs}, done: {stats.execs}, pending: {stats.inputs - stats.execs}, execs: {stats.execs/stats.inputs}")

async def worker(browser, queue):
    while True:
        url = await queue.get()

        page = await browser.newPage()
        page.setDefaultNavigationTimeout(10000)

        #page.on('request', lambda req: asyncio.create_task(on_request(req)))
        #page.on('requestfinished', lambda req: asyncio.create_task(on_requestfinished(req)))
        #page.on('response', lambda resp: asyncio.create_task(on_response(resp)))

        try:
            r = await asyncio.wait_for(screenshot(url, page), timeout=30)

            async with ScanDatabase(report_folder) as db:
                await db.add_host_and_service(**r)
            logging.info(f"Took screenshot of {url}")
        except asyncio.TimeoutError:
            logging.info(f"Task for url {url} timed out")
        except Exception as e:
            #if not any(err in str(e) for err in ['ERR_ADDRESS_UNREACHABLE', 'ERR_CONNECTION_REFUSED', 'ERR_CONNECTION_TIMED_OUT']):
            logging.error(f"Error taking screenshot: {e}")
        finally:
            stats.execs += 1
            await page.close()
            queue.task_done()

async def producer(queue):
    for url in generate_urls(args.target):
        stats.inputs += 1
        await queue.put(url)

async def start_scan():
    await ScanDatabase.create_db_and_schema(report_folder)
    queue = asyncio.Queue()
    asyncio.create_task(producer(queue))

    t = threading.Thread(target=task_watch, args=(queue,))
    t.setDaemon(True)
    t.start()

    browser = await pyppeteer.launch(headless=True, ignoreHTTPSErrors=True)
    try:
        worker_threads = [asyncio.create_task(worker(browser, queue)) for n in range(args.threads)]
        logging.info(f"Using {len(worker_threads)} worker thread(s)")

        await queue.join()

        for task in worker_threads:
            task.cancel()
        # Wait until all worker tasks are cancelled.
        await asyncio.gather(*worker_threads, return_exceptions=True)

    finally:
        await browser.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("target", nargs='+', type=str, help='The target IP(s), range(s), CIDR(s) or hostname(s)')
    parser.add_argument("-p", "--ports", nargs='+', default=[80, 8080, 443, 8443], help="Ports")
    parser.add_argument('--threads', default=25, type=int, help='Number of concurrent threads')
    args = parser.parse_args()

    patch_pyppeteer() # https://github.com/miyakogi/pyppeteer/issues/62

    time = datetime.now().strftime("%Y_%m_%d_%H%M%S")
    report_folder = f"scan_{time}"
    os.mkdir(report_folder)

    asyncio.run(start_scan())
