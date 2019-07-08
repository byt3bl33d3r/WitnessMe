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
from database import ScanDatabase
from datetime import datetime
from ipaddress import ip_address, ip_network, summarize_address_range
from asyncio import FIRST_COMPLETED
from argparse import ArgumentDefaultsHelpFormatter
from time import sleep
from urllib.parse import urlparse
from pyppeteer import launch

logging.getLogger('pyppeteer').setLevel(logging.ERROR)

logging.basicConfig(format="%(asctime)s [%(levelname)s] - %(filename)s: %(funcName)s - %(message)s", level=logging.INFO)

def generate_urls(targets):
    for target in targets:
        for host in generate_targets(target):
            for port in args.ports:
                for scheme in ["http", "https"]:
                    stats.inputs += 1
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

async def screenshot(url, browser):
    async with sem:
        logging.info(f"Taking screenshot of {url}")
        parsed_url = urlparse(url)

        hostname, ip = await resolve_host(parsed_url.hostname)
        screenshot_path = f'./{report_folder}/{parsed_url.scheme}_{parsed_url.hostname}_{parsed_url.port}.png'

        result_dict = {
            "url": url,
            "screenshot_path": screenshot_path,
            "ip": ip,
            "hostname": hostname,
            "port": parsed_url.port,
            "svc_name": parsed_url.scheme
        }

        page = await browser.newPage()
        #page.on('request', lambda req: asyncio.create_task(on_request(req)))
        #page.on('requestfinished', lambda req: asyncio.create_task(on_requestfinished(req)))
        #page.on('response', lambda resp: asyncio.create_task(on_response(resp)))

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

        #result_dict["title"] = await page.evaluate('document.title')
        result_dict["title"] = await page.title()
        result_dict["headers"] = response.headers

        await page.close()
        return result_dict

def task_watch(tasks):
    while True:
        sleep(1)
        total_tasks = len(tasks)
        done_tasks = len([t for t in tasks if t.done()])
        pending_tasks = len([t for t in tasks if not t.done()])

        logging.info(f"total: {total_tasks}, done: {done_tasks}, pending: {pending_tasks}, execs: {stats.execs}/{stats.inputs}")

async def start_scan():
    await ScanDatabase.create_db_and_schema(report_folder)
    browser = await launch(headless=True, ignoreHTTPSErrors=True)

    try:
        tasks = [ asyncio.create_task(screenshot(url, browser)) for url in generate_urls(args.target) ]
        t = threading.Thread(target=task_watch, args=(tasks,))
        t.setDaemon(True)
        t.start()

        for task in asyncio.as_completed(tasks):
            stats.execs += 1
            try:
                r = await task
                logging.info(f"Took screenshot of {r['url']}: {r}")

                async with ScanDatabase(report_folder) as db:
                    await db.add_host_and_service(**r)
            except Exception as e:
                #if not any(err in str(e) for err in ['ERR_ADDRESS_UNREACHABLE', 'ERR_CONNECTION_REFUSED', 'ERR_CONNECTION_TIMED_OUT']):
                logging.error(f"Error taking screenshot: {e}")
    except Exception:
        logging.info("main() got exception")
    finally:
        await browser.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("target", nargs='+', type=str, help='The target IP(s), range(s), CIDR(s) or hostname(s)')
    parser.add_argument("-p", "--ports", nargs='+', default=[80, 8080, 443, 8443], help="Ports")
    parser.add_argument('--threads', default=25, type=int, help='Number of concurrent threads')
    args = parser.parse_args()

    time = datetime.now().strftime("%Y_%m_%d_%H%M%S")
    report_folder = f"scan_{time}"
    os.mkdir(report_folder)

    loop = asyncio.get_event_loop()
    sem = asyncio.BoundedSemaphore(args.threads, loop=loop)

    loop.run_until_complete(start_scan())
