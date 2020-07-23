#! /usr/bin/env python3

import argparse
import logging
from witnessme import __version__, __codename__
from witnessme.utils import patch_pyppeteer, start_event_loop, WitnessMeArgFormatter
from witnessme.commands import ScreenShot, Grab


@start_event_loop
async def screenshot(args):
    cmd = ScreenShot(
        target=args.target,
        ports=args.ports,
        timeout=args.timeout,
        threads=args.threads,
    )

    await cmd.start()


@start_event_loop
async def grab(args):
    cmd = Grab(
        target=args.target,
        timeout=args.timeout,
        threads=args.threads,
        xpath=args.xpath,
        links=args.links,
    )

    await cmd.start()


def run():
    # logging.Formatter("%(asctime)s [%(levelname)s] - %(filename)s: %(funcName)s - %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(name)s] %(levelname)s - %(message)s"))

    log = logging.getLogger("witnessme")
    log.setLevel(logging.INFO)
    log.addHandler(handler)

    parser = argparse.ArgumentParser(
        description="WitnessMe!", formatter_class=WitnessMeArgFormatter
    )

    parser.add_argument(
        "--threads",
        default=15,
        type=int,
        help="Number of concurrent browser tab(s) to open\n[WARNING: This can cause huge RAM consumption if set to high values]",
    )

    parser.add_argument(
        "--timeout",
        default=15,
        type=int,
        help="Timeout for each connection attempt in seconds",
    )

    parser.add_argument(
        "-d", "--debug", default=False, action="store_true", help="Enable debug output"
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"{__version__} - '{__codename__}'"
    )

    subparsers = parser.add_subparsers(dest="command")
    screenshot_parser = subparsers.add_parser("screenshot")
    screenshot_parser.add_argument(
        "target",
        nargs="+",
        type=str,
        help="The target IP(s), range(s), CIDR(s) or hostname(s), NMap XML file(s), .Nessus file(s)",
    )

    screenshot_parser.add_argument(
        "-p",
        "--ports",
        nargs="+",
        default=[80, 8080, 443, 8443],
        help="Ports to scan if IP Range/CIDR is provided",
    )
    screenshot_parser.set_defaults(func=screenshot)

    grab_parser = subparsers.add_parser("grab")
    grab_parser.add_argument(
        "target",
        nargs="+",
        type=str,
        help="The target IP(s), range(s), CIDR(s) or hostname(s), NMap XML file(s), .Nessus file(s)",
    )

    exclusive_group = grab_parser.add_mutually_exclusive_group()
    exclusive_group.add_argument("-x", "--xpath", type=str, help="XPath to use")
    exclusive_group.add_argument(
        "-l", "--links", action="store_true", help="Get all links"
    )
    grab_parser.set_defaults(func=grab)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        parser.exit(1)

    if args.debug:
        log.setLevel(logging.DEBUG)

    patch_pyppeteer()
    log.debug(vars(args))
    args.func(args)


if __name__ == "__main__":
    run()
