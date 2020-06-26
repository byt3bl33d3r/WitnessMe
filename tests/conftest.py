import logging
import pytest

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s"))
log = logging.getLogger("witnessme")
log.setLevel(logging.DEBUG)
log.addHandler(handler)