import asyncio
import socket

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


async def resolve_host(host):
    try:
        name,_,ips = socket.gethostbyaddr(host)
        return name, ips[0]
    except Exception:
        return '', ''
