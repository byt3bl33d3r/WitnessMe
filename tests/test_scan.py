import pytest
import pathlib
import logging
import os
import shutil
from witnessme.scan import WitnessMeScan
from witnessme.utils import patch_pyppeteer

handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s")
)

log = logging.getLogger("witnessme")
log.setLevel(logging.DEBUG)
log.addHandler(handler)

patch_pyppeteer()

@pytest.mark.asyncio
async def test_scan():
    try:
        scan = WitnessMeScan(target=["https://google.com"])
        await scan.run()
        report_folder_path = pathlib.Path(scan.report_folder)

        assert report_folder_path.exists() == True
        assert "witnessme.db" in os.listdir(report_folder_path.absolute())
        assert any(
            map(
                lambda f: f.endswith(".png"),
                os.listdir(report_folder_path.absolute())
            )
        ) == True

    finally:
        shutil.rmtree(report_folder_path.absolute(), ignore_errors=True)
