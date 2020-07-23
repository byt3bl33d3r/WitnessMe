import asyncio
import logging
import uuid
import functools
from witnessme.commands.screenshot import ScreenShot, ScanState
from witnessme.api.models import Scan, ScanConfig
from witnessme.utils import patch_pyppeteer, zip_scan_folder
from fastapi import APIRouter, Request, Response, status, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse

log = logging.getLogger("witnessme.api")
patch_pyppeteer()

router = APIRouter()


@router.post("/")
async def create_scan(scan_config: ScanConfig, request: Request):
    conf = scan_config.dict()
    scan = ScreenShot(**conf)
    request.app.state.SCANS.add(scan)
    return Scan.from_orm(scan)


@router.get("/")
async def get_scans(request: Request):
    return {scan.id: Scan.from_orm(scan) for scan in request.app.state.SCANS.scans}


@router.get("/{scan_id}")
async def get_scan_by_id(scan_id: uuid.UUID, request: Request):
    scan = request.app.state.SCANS.get(scan_id)
    return Scan.from_orm(scan)


@router.get("/{scan_id}/start")
async def start_scan(scan_id: uuid.UUID, request: Request):
    scan = request.app.state.SCANS.get(scan_id)
    if scan.state in [ScanState.CONFIGURED, ScanState.STOPPED]:
        asyncio.create_task(scan.start())
        return Response(status_code=status.HTTP_200_OK)

    return JSONResponse(
        {"error": "finished scans cannot be started"},
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@router.get("/{scan_id}/stop")
async def stop_scan(scan_id: uuid.UUID, request: Request):
    scan = request.app.state.SCANS.get(scan_id)
    await scan.stop()
    return Response(status_code=status.HTTP_200_OK)


@router.get("/{scan_id}/result")
async def get_scan_result(scan_id: uuid.UUID, request: Request):
    scan = request.app.state.SCANS.get(scan_id)
    if not scan.stats.done:
        return JSONResponse(
            {"error": "scan has not finished"}, status_code=status.HTTP_400_BAD_REQUEST
        )

    loop = asyncio.get_running_loop()
    zip_file = await loop.run_in_executor(
        None, functools.partial(zip_scan_folder, scan.report_folder)
    )

    return FileResponse(zip_file, media_type="application/zip")


@router.post("/{scan_id}/upload/{file_id}")
async def upload_scan_target_file(
    scan_id: uuid.UUID, file_id: str, request: Request, file: UploadFile = File(...)
):
    scan = request.app.state.SCANS.get(scan_id)

    for i, t in enumerate(scan.target):
        if t.startswith("file:"):
            _, f_name, f_id = t.split(":")
            if f_id == file_id:
                scan.target[i] = file.path
                return Response(status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)
