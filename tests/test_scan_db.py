import pytest
import shutil
import os
from witnessme.database import ScanDatabase

report_folder = "./scan_db_test_folder"


@pytest.mark.asyncio
async def test_scan_db_creation():
    os.mkdir(report_folder)
    try:
        await ScanDatabase.create_db_and_schema(report_folder)
    finally:
        shutil.rmtree(report_folder, ignore_errors=True)


@pytest.mark.asyncio
async def test_scan_db():
    # TO DO: Add tests for all ScanDatabase methods
    os.mkdir(report_folder)
    try:
        await ScanDatabase.create_db_and_schema(report_folder)
        async with ScanDatabase(report_folder=report_folder) as db:
            fake_data = {
                "ip": "127.0.0.1",
                "hostname": "test",
                "url": "https://127.0.0.1:443/",
                "screenshot": f"{report_folder}/test.png",
                "port": 443,
                "scheme": "https",
                "title": "Test page",
                "server": "Test server",
                "headers": {"Wat": "Test"},
                "body": "<html><body> Test </body></html>",
            }
            await db.add_host_and_service(**fake_data)

            assert await db.get_host_count() == 1
            assert await db.get_service_count() == 1
            assert len(await db.get_hosts()) == 1
            assert len(await db.get_services()) == 1

    finally:
        shutil.rmtree(report_folder, ignore_errors=True)
