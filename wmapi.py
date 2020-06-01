import logging
import uvicorn
from witnessme.api.routers import scan
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(filename)s: %(funcName)s - %(message)s"
    )
)

log = logging.getLogger("witnessme")
log.setLevel(logging.DEBUG)
log.addHandler(handler)


class ActiveScans:
    def __init__(self):
        self.scans = []

    def add(self, scan):
        self.scans.append(scan)

    def get(self, scan_id):
        return next(filter(lambda s: s.id == scan_id, self.scans), None)


app = FastAPI(debug=True, title=__name__)
app.state.SCANS = ActiveScans()
app.include_router(scan.router, prefix="/scan", tags=["scan"])


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
