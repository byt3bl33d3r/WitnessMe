import asyncio
import socket
import pyppeteer.connection
import logging
import string
import random
import zipfile
import os
import json
from ipaddress import ip_address
from pyppeteer.network_manager import NetworkManager, Response

log = logging.getLogger("witnessme.utils")


def beautify_json(obj) -> str:
    return "\n" + json.dumps(obj, sort_keys=True, indent=4, separators=(",", ": "))


async def resolve_host(host):
    try:
        return socket.gethostbyaddr(host)[0]
    except Exception as e:
        log.debug(f"Error resolving IP {host}: {e}")


def is_ipaddress(host):
    try:
        ip_address(host)
        return True
    except ValueError:
        return False


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

        Original function https://github.com/miyakogi/pyppeteer/blob/1aa0221f4fda21d59b18373e0f09071f2cd7402b/pyppeteer/network_manager.py#L255-L268
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
    There's a bug in pyppeteer currently (https://github.com/miyakogi/pyppeteer/issues/62) which closes the websocket connection to Chromium after ~20s.
    This is a hack to fix that. Taken from https://github.com/miyakogi/pyppeteer/pull/160

    Additionally this hooks the _onResponseReceived method with our own above.
    """
    log.debug("Patching pyppeteer...")

    original_method = pyppeteer.connection.websockets.client.connect

    def new_method(*args, **kwargs):
        kwargs["ping_interval"] = None
        kwargs["ping_timeout"] = None
        return original_method(*args, **kwargs)

    pyppeteer.connection.websockets.client.connect = new_method
    # Hook the onResponseReceived event
    pyppeteer.network_manager.NetworkManager._onResponseReceived = (
        _customOnResponseReceived
    )
