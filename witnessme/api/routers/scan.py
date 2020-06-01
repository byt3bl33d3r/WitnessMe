import asyncio
import logging
import uuid
import functools
from witnessme.scan import WitnessMe, ScanStats
from witnessme.api.models import *
from witnessme.utils import patch_pyppeteer, gen_random_string, zip_scan_folder
from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse, FileResponse

log = logging.getLogger("witnessme.api")
patch_pyppeteer()

router = APIRouter(default_response_class=JSONResponse)


@router.post("/")
async def create_scan(scan_config: ScanConfig, request: Request):
    conf = scan_config.dict()
    scan = WitnessMe(**conf)
    request.app.state.SCANS.add(scan)
    return Scan.from_orm(scan)


@router.get("/")
async def get_scans(request: Request):
    return {scan.id: Scan.from_orm(scan) for scan in request.app.state.SCANS.scans}


@router.get("/{scan_id}")
async def get_scan_by_id(scan_id: uuid.UUID, request: Request):
    scan = request.app.state.SCANS.get(scan_id)
    if not scan:
        return JSONResponse(
            {"error": "specified scan id does not exist"},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return Scan.from_orm(scan)


@router.get("/{scan_id}/start")
async def start_scan(scan_id: uuid.UUID, request: Request):
    scan = request.app.state.SCANS.get(scan_id)
    if not scan:
        return JSONResponse(
            {"error": "specified scan id does not exist"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    asyncio.create_task(scan.start())
    return Response(status_code=status.HTTP_200_OK)


@router.get("/{scan_id}/stop")
async def stop_scan(scan_id: uuid.UUID, request: Request):
    scan = request.app.state.SCANS.get(scan_id)
    if not scan:
        return JSONResponse(
            {"error": "specified scan id does not exist"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    asyncio.create_task(scan.stop())
    return Response(status_code=status.HTTP_200_OK)


@router.get("/{scan_id}/result")
async def get_scan_result(scan_id: uuid.UUID, request: Request):
    scan = request.app.state.SCANS.get(scan_id)
    if not scan:
        return JSONResponse(
            {"error": "specified scan id does not exist"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
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
async def upload_scan_target_file(scan_id: uuid.UUID, file_id: str, request: Request):
    scan = request.app.state.SCANS.get(scan_id)
    if not scan:
        return JSONResponse(
            {"error": "specified scan id does not exist"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    for i, t in enumerate(scan.target):
        if t.startswith("file:"):
            _, f_name, f_id = t.split(":")
            if f_id == file_id:
                with open(f_name, "wb") as uploaded_scan_file:
                    async for data in request.body:
                        uploaded_scan_file.write(data)
                    scan.target.append(upload_scan_target_file.path)
                scan.target[i] = f_name
                return Response(status_code=status.HTTP_200_OK)
