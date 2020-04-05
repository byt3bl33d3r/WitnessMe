import logging
import asyncio
import os
import argparse
import signal
import pyppeteer
import pathlib
import contextvars
import uuid
from dataclasses import dataclass
from typing import List
from datetime import datetime
from urllib.parse import urlparse
from witnessme.utils import resolve_host, is_ipaddress
from witnessme.database import ScanDatabase
from witnessme.parsers import AutomaticTargetGenerator

log = logging.getLogger("witnessme")

@dataclass
class ScanStats:
    inputs: int = 0
    execs: int = 0
    done: bool = False

    @property
    def pending(self):
        return self.inputs - self.execs

class WitnessMeScan:
    def __init__(self, target: List[str], ports: List[int] = [80, 8080, 443, 8443], threads: int = 25, timeout: int = 35) -> None:
        self.id = uuid.uuid4()
        self.target = target
        self.ports = ports
        self.threads = threads
        self.timeout = timeout
        self.stats = ScanStats()

        time = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        self.report_folder = f"scan_{time}"

        self._queue = asyncio.Queue()
        self._task_watch_event = asyncio.Event()

    async def _on_request(self, request):
        pass
        #log.info(f"on_request() called: url: {request.url}")

    async def _on_response(self, response):
        pass
        #log.info(f"on_response() called, url: {response.url}")

    async def _on_requestfinished(self, request):
        pass
        #log.info(f"on_requestfinished() called, url: {request.url}")

    async def _task_watch(self):
        while not self._task_watch_event.is_set():
            await asyncio.sleep(5)
            log.info(f"total: {self.stats.inputs}, done: {self.stats.execs}, pending: {self.stats.pending}")

    async def screenshot(self, url, page):
        """
            The page.goto() options might need to be tweaked depending on testing in real environments.

            https://github.com/GoogleChrome/puppeteer/blob/master/docs/api.md#pagewaitfornavigationoptions

            load - consider navigation to be finished when the load event is fired.
            domcontentloaded - consider navigation to be finished when the DOMContentLoaded event is fired.
            networkidle0 - consider navigation to be finished when there are no more than 0 network connections for at least 500 ms.
            networkidle2 - consider navigation to be finished when there are no more than 2 network connections for at least 500 ms.
        """

        url = urlparse(url)
        response = await page.goto(
            url.geturl(),
            options={
                "waitUntil": "networkidle0"
            }
        )

        hostname = None
        if is_ipaddress(url.hostname):
            hostname = await asyncio.wait_for(resolve_host(url.hostname), timeout=3)
        else:
            hostname = url.hostname

        if not url.port:
            url = url._replace(netloc=f"{url.hostname}:{response.remotePort}")

        screenshot = f'{url.scheme}_{url.hostname}_{url.port}.png'
        screenshot_path = str(pathlib.Path(f'./{self.report_folder}/{screenshot}').absolute())
        await page.screenshot(
            {
                'path': screenshot_path,
                'fullPage': True
            }
        )

        return {
            "ip": response.remoteIPAddress,
            "hostname": hostname,
            "url": url.geturl(),
            "screenshot": screenshot,
            "port": url.port,
            "scheme": url.scheme,
            "title": await page.title(), # await page.evaluate('document.title')
            "server": response.headers.get('server'),
            "headers": response.headers,
            "body": await response.text()
        }

    async def worker(self, context):
        #while True:
        url = await self._queue.get()

        page = await context.newPage()
        page.setDefaultNavigationTimeout(self.timeout * 1000) # setDefaultNavigationTimeout() accepts milliseconds

        #page.on('request', lambda req: asyncio.create_task(self._on_request(req)))
        #page.on('requestfinished', lambda req: asyncio.create_task(self._on_requestfinished(req)))
        #page.on('response', lambda resp: asyncio.create_task(self._on_response(resp)))

        try:
            r = await asyncio.wait_for(self.screenshot(url, page), timeout=self.timeout)
            log.debug(r)
            async with ScanDatabase(self.report_folder) as db:
                await db.add_host_and_service(**r)
            log.info(f"Took screenshot of {url}")
        except asyncio.TimeoutError:
            log.info(f"Task for url {url} timed out")
        except Exception as e:
            #if not any(err in str(e) for err in ['ERR_ADDRESS_UNREACHABLE', 'ERR_CONNECTION_REFUSED', 'ERR_CONNECTION_TIMED_OUT']):
            log.error(f"Error taking screenshot: {e}")
        finally:
            self.stats.execs += 1
            await page.close()
            self._queue.task_done()

    async def producer(self):
        with AutomaticTargetGenerator(self.target) as generated_targets:
            for url in generated_targets: 
                self.stats.inputs += 1
                await self._queue.put(url)

    async def scan(self, n_urls: int):
        log.info("Starting headless browser")
        browser = await pyppeteer.launch(headless=True, ignoreHTTPSErrors=True, autoClose=False, args=['--no-sandbox']) # --no-sandbox is required to make Chrome/Chromium run under root.
        context = await browser.createIncognitoBrowserContext()

        try:
            worker_threads = [asyncio.create_task(self.worker(context)) for _ in range(n_urls)]
            log.info(f"Using {len(worker_threads)} worker thread(s)")
            await asyncio.gather(*worker_threads)
        finally:
            await context.close()
            log.info("Killing headless browser")
            await browser.disconnect()
            await browser.close()

    async def run(self):
        os.mkdir(self.report_folder)
        await ScanDatabase.create_db_and_schema(self.report_folder)

        asyncio.create_task(self.producer())

        log.debug("Waiting for queue to populate...")
        while self._queue.qsize() == 0:
            await asyncio.sleep(0.1)

        asyncio.create_task(self._task_watch())

        while self._queue.qsize() > 0:
            await self.scan(
                    n_urls=self.threads if self._queue.qsize() > self.threads else self._queue.qsize(),
                )

        self._task_watch_event.set()
        self.stats.done = True
