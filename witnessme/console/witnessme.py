#! /usr/bin/env python3

import argparse
import logging
import asyncio
from argparse import ArgumentDefaultsHelpFormatter
from witnessme.utils import patch_pyppeteer
from witnessme.scan import WitnessMe


def run():
    # logging.Formatter("%(asctime)s [%(levelname)s] - %(filename)s: %(funcName)s - %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(name)s] %(levelname)s - %(message)s"))

    log = logging.getLogger("witnessme")
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)

    parser = argparse.ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "target",
        nargs="+",
        type=str,
        help="The target IP(s), range(s), CIDR(s) or hostname(s)",
    )
    parser.add_argument(
        "-p",
        "--ports",
        nargs="+",
        default=[80, 8080, 443, 8443],
        help="Ports to scan if IP Range/CIDR is provided",
    )
    parser.add_argument(
        "--threads", default=25, type=int, help="Number of concurrent threads"
    )
    parser.add_argument(
        "--timeout",
        default=15,
        type=int,
        help="Timeout for each connection attempt in seconds",
    )
    args = parser.parse_args()

    patch_pyppeteer()

    scan = WitnessMe(**vars(args))
    asyncio.run(scan.run())


if __name__ == "__main__":
    run()
