import pytest
import pathlib
import os
import shutil
from witnessme.commands import ScreenShot


@pytest.mark.asyncio
async def test_scan():
    try:
        scan = ScreenShot(target=["https://google.com"])
        await scan.start()
        report_folder_path = pathlib.Path(scan.report_folder)

        assert report_folder_path.exists() == True
        assert "witnessme.db" in os.listdir(report_folder_path.absolute())
        assert (
            any(
                map(
                    lambda f: f.endswith(".png"),
                    os.listdir(report_folder_path.absolute()),
                )
            )
            == True
        )

    finally:
        shutil.rmtree(report_folder_path.absolute(), ignore_errors=True)
