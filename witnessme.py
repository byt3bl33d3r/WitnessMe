#! /usr/bin/env python3

import threading
import logging
import asyncio
import os
import argparse
import signal
import pyppeteer
import pathlib
import witnessme.stats as stats
from time import sleep
from witnessme.utils import patch_pyppeteer, resolve_host
from witnessme.database import ScanDatabase
from witnessme.parsers import AutomaticTargetGenerator
from datetime import datetime
from argparse import ArgumentDefaultsHelpFormatter
from urllib.parse import urlparse

logging.basicConfig(format="%(asctime)s [%(levelname)s] - %(filename)s: %(funcName)s - %(message)s", level=logging.DEBUG)
logging.getLogger('asyncio').setLevel(logging.ERROR)
logging.getLogger('sqlite3').setLevel(logging.ERROR)
logging.getLogger('aiosqlite').setLevel(logging.ERROR)
logging.getLogger('asyncio.coroutines').setLevel(logging.ERROR)
logging.getLogger('websockets').setLevel(logging.ERROR)
logging.getLogger('websockets.server').setLevel(logging.ERROR)
logging.getLogger('websockets.protocol').setLevel(logging.ERROR)
logging.getLogger('pyppeteer').setLevel(logging.INFO)

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
    #logging.info(f"Taking screenshot of {url}")
    parsed_url = urlparse(url)

    hostname, ip = await resolve_host(parsed_url.hostname)
    screenshot_path = str(
        pathlib.Path(
            f'./{report_folder}/{parsed_url.scheme}_{parsed_url.hostname}_{parsed_url.port}.png'
        ).absolute()
    )

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

    return {
        "ip": ip,
        "hostname": hostname,
        "url": url,
        "screenshot_path": screenshot_path,
        "port": parsed_url.port,
        "scheme": parsed_url.scheme,
        "title": await page.title(), # await page.evaluate('document.title')
        "server": response.headers['server'] if 'server' in response.headers else None,
        "headers": response.headers,
    }

def task_watch(queue):
    while True:
        sleep(5)
        #total_tasks = queue.qsize()
        logging.info(f"total: {stats.inputs}, done: {stats.execs}, pending: {stats.inputs - stats.execs}")

async def worker(browser, queue):
    while True:
        url = await queue.get()

        page = await browser.newPage()
        page.setDefaultNavigationTimeout(args.timeout * 1000) # setDefaultNavigationTimeout() accepts milliseconds

        #page.on('request', lambda req: asyncio.create_task(on_request(req)))
        #page.on('requestfinished', lambda req: asyncio.create_task(on_requestfinished(req)))
        #page.on('response', lambda resp: asyncio.create_task(on_response(resp)))

        try:
            r = await asyncio.wait_for(screenshot(url, page), timeout=args.timeout)
            logging.info(r)
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
    with AutomaticTargetGenerator(args.target) as generated_targets:
        for url in generated_targets: 
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
    parser.add_argument('--timeout', default=35, type=int, help='Timeout for each connection attempt in seconds (Default: 35)')
    args = parser.parse_args()

    patch_pyppeteer() # https://github.com/miyakogi/pyppeteer/issues/62

    time = datetime.now().strftime("%Y_%m_%d_%H%M%S")
    report_folder = f"scan_{time}"
    os.mkdir(report_folder)

    asyncio.run(start_scan())
