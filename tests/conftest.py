import logging
import pytest


def pytest_runtest_setup(item):
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s"))

    log = logging.getLogger("witnessme")
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)
