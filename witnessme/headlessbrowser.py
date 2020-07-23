import logging
import asyncio
import os
import pyppeteer
from typing import List
from witnessme.parsers import AutomaticTargetGenerator
from pyppeteer.errors import PageError

log = logging.getLogger("witnessme.headlessbrowser")


class BrowserStats:
    inputs: int = 0
    execs: int = 0

    @property
    def pending(self) -> int:
        return self.inputs - self.execs


async def navigate_to_page(browser, url, page):
    log.debug(f"Navigating to {url}, replace me with something useful")


async def finished_navigation(browser, results):
    log.debug("Finished navigation, replace me with something useful")


class HeadlessChromium:
    def __init__(
        self, threads: int = 15, timeout: int = 15, on_new_tab=None, on_finished=None
    ) -> None:
        self.threads = threads
        self.timeout = timeout
        self.on_new_tab = on_new_tab or navigate_to_page
        self.on_finished = on_finished or finished_navigation
        self.stats = BrowserStats()

        self._queue = asyncio.Queue()
        self._browser_stop_event = asyncio.Event()

    async def _on_request(self, request):
        pass
        # log.info(f"on_request() called: url: {request.url}")

    async def _on_response(self, response):
        pass
        # log.info(f"on_response() called, url: {response.url}")

    async def _on_requestfinished(self, request):
        pass
        # log.info(f"on_requestfinished() called, url: {request.url}")

    async def task_watch(self):
        while not self._browser_stop_event.is_set():
            try:
                await asyncio.sleep(5)
                log.info(
                    f"total: {self.stats.inputs}, done: {self.stats.execs}, pending: {self.stats.pending}"
                )
            except asyncio.CancelledError:
                break

    async def target_producer(self, targets, ports):
        with AutomaticTargetGenerator(targets, ports) as generated_targets:
            for url in generated_targets:
                self.stats.inputs += 1
                await self._queue.put(url)

    async def open_browser_tab(self, context):
        url = await self._queue.get()

        # page.setDefaultNavigationTimeout() accepts milliseconds
        page = await context.newPage()
        page.setDefaultNavigationTimeout(self.timeout * 1000)

        # page.on('request', lambda req: asyncio.create_task(self._on_request(req)))
        # page.on('requestfinished', lambda req: asyncio.create_task(self._on_requestfinished(req)))
        # page.on('response', lambda resp: asyncio.create_task(self._on_response(resp)))

        try:
            results = await asyncio.wait_for(
                self.on_new_tab(self, url, page), timeout=self.timeout
            )
            await self.on_finished(self, results)
            log.debug(f"Navigated to {url}")
        except asyncio.TimeoutError:
            log.error(f"Navigation to url {url} timed out")
        except Exception as e:
            # if not any(err in str(e) for err in ['ERR_ADDRESS_UNREACHABLE', 'ERR_CONNECTION_REFUSED', 'ERR_CONNECTION_TIMED_OUT']):
            log.error(f"Error navigating to url {url}: {e}")
        finally:
            self.stats.execs += 1
            await page.close()
            self._queue.task_done()

    async def start_browser(self, n_urls: int):
        log.info("Starting headless browser")
        # --no-sandbox is required to make Chrome/Chromium run under root
        browser_args = ["--no-sandbox", "--disable-gpu"]

        proxy = os.environ.get("HTTP_PROXY")
        if proxy:
            browser_args.append(f"--proxy-server={proxy}")
            log.info(f"Proxy set to {proxy}")

        browser = await pyppeteer.launch(
            headless=True,
            ignoreHTTPSErrors=True,
            autoClose=False,
            args=browser_args,
            executablePath=os.environ.get("CHROMIUM_EXECUTABLE_PATH"),
        )

        context = await browser.createIncognitoBrowserContext()

        try:
            worker_threads = [
                asyncio.create_task(self.open_browser_tab(context))
                for _ in range(n_urls)
            ]
            log.info(f"Using {len(worker_threads)} browser tab(s)/thread(s)")
            await asyncio.gather(*worker_threads)
        except asyncio.CancelledError:
            log.info(f"Cancelling tab(s)/thread(s)")
        finally:
            try:
                await context.close()
            except PageError:
                log.error("Page crashed, ignoring...")

            log.info("Killing headless browser")
            await browser.disconnect()
            await browser.close()

    async def run(
        self, targets: List[str], ports: List[int] = [80, 8080, 443, 8443]
    ) -> None:
        asyncio.create_task(self.target_producer(targets, ports))

        log.debug("Waiting for queue to populate...")
        while self._queue.qsize() == 0:
            await asyncio.sleep(0.1)

        task_watcher = asyncio.create_task(self.task_watch())

        try:
            while self._queue.qsize() > 0 and not self._browser_stop_event.is_set():
                await self.start_browser(
                    n_urls=self.threads
                    if self._queue.qsize() > self.threads
                    else self._queue.qsize(),
                )
        finally:
            task_watcher.cancel()

    async def stop(self):
        self._browser_stop_event.set()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._queue.join()
