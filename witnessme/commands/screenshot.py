import logging
import asyncio
import pathlib
import uuid
import shutil
import os
from enum import Enum
from typing import List
from datetime import datetime
from urllib.parse import urlparse
from witnessme.utils import is_ipaddress, agethostbyaddr
from witnessme.headlessbrowser import HeadlessChromium
from witnessme.database import ScanDatabase

log = logging.getLogger("witnessme.screenshot")


class ScanState(str, Enum):
    STARTED = "started"
    STOPPED = "stopped"
    # CANCELLED = 'cancelled'
    DONE = "done"
    # PAUSED = 'paused'
    CONFIGURED = "configured"


class ScreenShot:
    def __init__(
        self,
        target: List[str],
        ports: List[int] = [80, 8080, 443, 8443],
        threads: int = 25,
        timeout: int = 35,
    ) -> None:
        self.id = uuid.uuid4()
        self.target = target
        self.ports = ports
        self.threads = threads
        self.timeout = timeout
        self.state = ScanState.CONFIGURED

        self._browser = HeadlessChromium(
            threads=self.threads,
            timeout=self.timeout,
            on_new_tab=self.screenshot,
            on_finished=self.add_to_database,
        )
        self.stats = self._browser.stats

        self._scan_task = None
        self._report_folder = None

    @property
    def report_folder(self):
        if self._report_folder:
            return self._report_folder

        time = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        self._report_folder = f"scan_{time}"
        return self._report_folder

    async def screenshot(self, browser, url, page):
        """
            The page.goto() options might need to be tweaked depending on testing in real environments.

            https://github.com/GoogleChrome/puppeteer/blob/master/docs/api.md#pagewaitfornavigationoptions

            load - consider navigation to be finished when the load event is fired.
            domcontentloaded - consider navigation to be finished when the DOMContentLoaded event is fired.
            networkidle0 - consider navigation to be finished when there are no more than 0 network connections for at least 500 ms.
            networkidle2 - consider navigation to be finished when there are no more than 2 network connections for at least 500 ms.
        """

        url = urlparse(url)
        dns_resolution_task = asyncio.create_task(agethostbyaddr(url.hostname))

        response = await page.goto(url.geturl(), options={"waitUntil": "networkidle0"})

        if not url.port:
            url = url._replace(netloc=f"{url.hostname}:{response.remotePort}")

        screenshot = f"{url.scheme}_{url.hostname}_{url.port}.png"
        screenshot_path = str(
            pathlib.Path(f"./{self.report_folder}/{screenshot}").absolute()
        )

        await page.screenshot({"path": screenshot_path, "fullPage": True})

        hostname = await dns_resolution_task
        return {
            "ip": response.remoteIPAddress,
            "hostname": hostname,
            "url": url.geturl(),
            "screenshot": screenshot,
            "port": url.port,
            "scheme": url.scheme,
            "title": await page.title(),  # await page.evaluate('document.title')
            "server": response.headers.get("server"),
            "headers": response.headers,
            "body": await response.text(),
        }

    async def add_to_database(self, browser, results):
        log.info(f"Took screenshot of {results['url']}")
        async with ScanDatabase(self.report_folder) as db:
            await db.add_host_and_service(**results)

    async def setup_and_run(self):
        try:
            os.mkdir(self.report_folder)
        except FileExistsError:
            if self.state == ScanState.STOPPED:
                shutil.rmtree(self.report_folder, ignore_errors=True)
                os.mkdir(self.report_folder)

        await ScanDatabase.create_db_and_schema(self.report_folder)

        await self._browser.run(self.target, self.ports)

    async def start(self):
        self.state = ScanState.STARTED
        log.info(f"Starting scan {self.id}")
        self._scan_task = asyncio.create_task(self.setup_and_run())
        await self._scan_task
        log.info(f"Saved scan to {self.report_folder}/")
        if not self._scan_task.cancelled():
            self.state = ScanState.DONE

    async def stop(self):
        if self._scan_task:
            log.info(f"Stopping scan {self.id}")
            self._scan_task.cancel()
            self.state = ScanState.STOPPED
