import asyncio
import logging
import string
import random
import zipfile
import os
import json
import aiodns
import pyppeteer
import functools
import argparse
from ipaddress import ip_address
from pyppeteer.network_manager import NetworkManager, Response

log = logging.getLogger("witnessme.utils")


class WitnessMeArgFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawTextHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    pass


def beautify_json(obj) -> str:
    return "\n" + json.dumps(obj, sort_keys=True, indent=4, separators=(",", ": "))


def is_ipaddress(host):
    try:
        ip_address(host)
        return True
    except ValueError:
        return False


def start_event_loop(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def gen_random_string(length=6):
    return "".join([random.choice(string.ascii_letters) for n in range(length)])


def zip_scan_folder(scan_folder: str):
    zip_file_path = f"{scan_folder}.zip"

    log.info(f"Compressing scan folder {scan_folder} to {zip_file_path}...")
    with zipfile.ZipFile(
        zip_file_path, "w", compresslevel=9, compression=zipfile.ZIP_DEFLATED
    ) as zf:
        for dirname, _, files in os.walk(scan_folder):
            zf.write(dirname)
            for filename in files:
                zf.write(os.path.join(dirname, filename))

    return zip_file_path


def _customOnResponseReceived(self, event: dict) -> None:
    """
        Pyppeteer doesn't expose the remoteIPAddress and remotePort attributes from the received
        Response object from Chrome. This is a hack that adds those attribute to it manually so that we can
        access them in the screenshot function. This is a much more elegant approach as socket.gethostbyaddr() 
        is a blocking call so it would slow things down somewhat significantly.

        Let the browser handle everything! :)

        https://github.com/pyppeteer/pyppeteer/blob/dev/pyppeteer/network_manager.py#L260-L273
        """

    request = self._requestIdToRequest.get(event["requestId"])
    # FileUpload sends a response without a matching request.
    if not request:
        return
    _resp = event.get("response", {})
    response = Response(
        self._client,
        request,
        _resp.get("status", 0),
        _resp.get("headers", {}),
        _resp.get("fromDiskCache"),
        _resp.get("fromServiceWorker"),
        _resp.get("securityDetails"),
    )

    # Add the remoteIPAddress and remotePort attributes to the Response object
    response.remoteIPAddress = _resp.get("remoteIPAddress")
    response.remotePort = _resp.get("remotePort")

    request._response = response
    self.emit(NetworkManager.Events.Response, response)


def patch_pyppeteer():
    """
    This hooks the _onResponseReceived method with our own above.
    """
    log.debug("Patching pyppeteer...")

    # Hook the onResponseReceived event
    pyppeteer.network_manager.NetworkManager._onResponseReceived = (
        _customOnResponseReceived
    )


class AsyncDNSResolver:
    def __init__(self):
        self._resolver = None

    async def __aenter__(self):
        if not self._resolver:
            self._resolver = aiodns.DNSResolver(loop=asyncio.get_running_loop())
        return self._resolver

    async def __aexit__(self, exc_type, exc_value, traceback):
        return


async def agethostbyaddr(addr):
    hostname = ""
    if not is_ipaddress(addr):
        return addr

    async with AsyncDNSResolver() as resolver:
        try:
            record = await asyncio.wait_for(resolver.gethostbyaddr(addr), timeout=3)
            hostname = record.name
            log.debug(f"Resolved {addr} to {hostname}")
        except (asyncio.TimeoutError, aiodns.error.DNSError) as e:
            log.debug(f"Unable to resolve {addr} to domain/host name: {e}")

    return hostname
