import logging
import uvicorn
import argparse
from witnessme.api.routers import scan
from argparse import ArgumentDefaultsHelpFormatter
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ScanNotFoundError(Exception):
    pass


class ActiveScans:
    def __init__(self):
        self.scans = []

    def add(self, scan):
        self.scans.append(scan)

    def get(self, scan_id):
        try:
            return list(filter(lambda s: s.id == scan_id, self.scans))[0]
        except IndexError:
            raise ScanNotFoundError


app = FastAPI(title="WitnessMe API")
app.state.SCANS = ActiveScans()
app.include_router(scan.router, prefix="/screenshot", tags=["scan"])


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


@app.exception_handler(ScanNotFoundError)
async def scan_not_found_exception_handler(request: Request, exc: ScanNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "specified scan id does not exist"},
    )


def run():
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(filename)s: %(funcName)s - %(message)s"
        )
    )

    log = logging.getLogger("witnessme")
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)

    parser = argparse.ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "host", type=str, nargs="?", help="IP to bind to", default="127.0.0.1"
    )
    parser.add_argument(
        "port", type=int, nargs="?", help="port to bind to", default=8000
    )
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    run()
