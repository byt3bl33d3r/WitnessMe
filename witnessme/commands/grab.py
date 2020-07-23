import logging
import asyncio
import lxml.html
from urllib.parse import urlparse
from typing import List
from witnessme.utils import beautify_json
from witnessme.headlessbrowser import HeadlessChromium

log = logging.getLogger("witnessme.grab")


class Grab:
    def __init__(
        self,
        target: List[str],
        threads: int = 25,
        timeout: int = 35,
        xpath=None,
        links=False,
    ) -> None:
        self.target = target
        self.threads = threads
        self.timeout = timeout
        self.xpath = xpath
        self.links = links

    async def grab_page(self, browser, url, page):
        url = urlparse(url)

        """
        await page.goto(url.geturl())
        response = await page.waitForNavigation(
            options={"waitUntil": "domcontentloaded"}
        )
        """

        _, response = await asyncio.gather(
            *[
                page.goto(url.geturl()),
                page.waitForNavigation(options={"waitUntil": "networkidle0"}),
            ]
        )

        if not url.port:
            url = url._replace(netloc=f"{url.hostname}:{response.remotePort}")

        return {
            "url": url.geturl(),
            "ip": response.remoteIPAddress,
            "port": url.port,
            "scheme": url.scheme,
            "title": await page.title(),  # await page.evaluate('document.title')
            "server": response.headers.get("server"),
            "headers": response.headers,
            "body": await response.text(),
        }

    async def parse_html(self, browser, results):
        html = lxml.html.fromstring(results["body"])
        results["body"] = f"{len(results['body'])} bytes"

        log.info(f"Grabbed page:" + beautify_json(results))

        if self.xpath:
            for match in html.xpath(self.xpath):
                if isinstance(match, str):
                    print(match.strip(" ").strip())
                else:
                    print(match)

        elif self.links:
            for match in html.xpath("//@href"):
                if len(match) > 0 and match != "#":
                    print(match.strip(" ").strip())

    async def start(self):
        if self.xpath:
            try:
                lxml.etree.XPath(self.xpath)
            except lxml.etree.XPathSyntaxError:
                log.error("Bad xpath! Exiting...")
                return

        async with HeadlessChromium(
            threads=self.threads,
            timeout=self.timeout,
            on_new_tab=self.grab_page,
            on_finished=self.parse_html,
        ) as browser:
            await browser.run(self.target)
