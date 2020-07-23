import pytest
import io
from witnessme.parsers import AutomaticTargetGenerator

"""
TO DO: add tests for parsing .nessus files
"""


def test_ip_network_target_parsing():
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


def test_stdin_parsing(monkeypatch):
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO("192.168.0.1/28\n172.16.0.1-10\nhttp-simple-new://google.com:443/"),
    )

    with AutomaticTargetGenerator(["-"]) as gen:
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


def test_nmap_xml_target_parsing():
    with AutomaticTargetGenerator(["tests/nmap_example.xml"]) as gen:
        urls = list(gen)
        print(urls)

        assert len(urls) == 13
