import logging
import pytest
from witnessme.utils import patch_pyppeteer

patch_pyppeteer()

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(name)s] %(levelname)s - %(message)s"))
log = logging.getLogger("witnessme")
log.setLevel(logging.DEBUG)
log.addHandler(handler)


@pytest.fixture(scope="session", autouse=True)
def fake_target_file(tmp_path_factory):
    targets = ["192.168.1.0/24", "10.0.0.1-20", "http://google.com"]
    target_file = tmp_path_factory.mktemp("witnessme") / "targets.txt"
    with target_file.open("w") as tmp_email_file:
        for target in targets:
            tmp_email_file.write(target + "\n")
    return tmp_email_file
