import pytest
import logging
from witnessme.parsers import AutomaticTargetGenerator

handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s")
)

log = logging.getLogger("witnessme")
log.setLevel(logging.DEBUG)
log.addHandler(handler)

def test_target_parser():
    # TO DO: add tests for parsing .nessus and nmap xml files
    with AutomaticTargetGenerator(["192.168.0.1/28", "172.16.0.1-10", "http-simple-new://google.com:443/"]) as gen:
        urls = list(gen)
        print(urls)
        assert len(urls) == 209
        assert all(map(lambda u: u.startswith("http://") or u.startswith("https://"), urls)) == True
        assert "http://google.com:443/" in urls
