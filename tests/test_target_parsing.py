import pytest
from witnessme.parsers import AutomaticTargetGenerator


def test_target_parser():
    # TO DO: add tests for parsing .nessus files
    with AutomaticTargetGenerator(
        ["192.168.0.1/28", "172.16.0.1-10", "http-simple-new://google.com:443/"]
    ) as gen:
        urls = list(gen)
        print(urls)
        assert len(urls) == 209
        assert (
            all(
                map(lambda u: u.startswith("http://") or u.startswith("https://"), urls)
            )
            == True
        )
        assert "http://google.com:443/" in urls

    with AutomaticTargetGenerator(["tests/nmap_example.xml"]) as gen:
        urls = list(gen)
        print(urls)
        assert len(urls) == 13
