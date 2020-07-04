#! /usr/bin/env python3

import asyncio
import argparse
import shlex
import logging
import sys
import pathlib
import aiosqlite
import webbrowser
from imgcat import imgcat
from time import time, gmtime, strftime
from argparse import ArgumentDefaultsHelpFormatter
from terminaltables import AsciiTable
from witnessme.database import ScanDatabase
from witnessme.signatures import Signatures
from witnessme.reporting import generate_html_report, generate_csv_report
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion

# from prompt_toolkit.patch_stdout import patch_stdout
# from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML

# from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.styles import Style

# from prompt_toolkit.document import Document

# logging.Formatter("%(asctime)s [%(levelname)s] - %(filename)s: %(funcName)s - %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(name)s] %(levelname)s - %(message)s"))
log = logging.getLogger("witnessme")
log.setLevel(logging.DEBUG)
log.addHandler(handler)


class WMCompleter(Completer):
    def __init__(self, cli_menu):
        self.cli_menu = cli_menu

    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor()
        try:
            list(map(lambda s: s.lower(), shlex.split(document.current_line)))
        except ValueError:
            pass
        else:
            for cmd in [
                "exit",
                "show",
                "open",
                "hosts",
                "servers",
                "scan",
                "generate_report",
                "open_html_report",
            ]:
                if cmd.startswith(word_before_cursor):
                    yield Completion(
                        cmd,
                        -len(word_before_cursor),
                        display_meta=getattr(self.cli_menu, cmd).__doc__.strip(),
                    )


class WMDBShell:
    def __init__(self, scan_folder_path):
        self.scan_folder_path = scan_folder_path
        self.db_path = scan_folder_path / "witnessme.db"

        self.completer = WMCompleter(self)
        self.signatures = Signatures()
        self.prompt_session = PromptSession(
            HTML("WMDB ≫ "),
            # bottom_toolbar=functools.partial(bottom_toolbar, ts=self.teamservers),
            completer=self.completer,
            complete_in_thread=True,
            complete_while_typing=True,
            auto_suggest=AutoSuggestFromHistory(),
            # rprompt=get_rprompt(False),
            # style=example_style,
            search_ignore_case=True,
        )

    async def _print_services(self, services, table_title=None):
        table_data = [["Id", "URL", "Title", "Server", "Matched Signature(s)"]]
        for entry in services:
            service_id, url, _, _, _, title, server, _, _, matched_sigs, _ = entry
            table_data.append([service_id, url, title, server, matched_sigs])

        table = AsciiTable(table_data)
        table.inner_row_border = True
        table.title = table_title
        print(table.table)

    async def _print_hosts(self, hosts, table_title=None):
        table_data = []

        async with ScanDatabase(connection=self.db) as db:
            for entry in hosts:
                host_id, hostname, ip = entry
                service_count = await db.get_service_count_on_host(host_id)
                matched_sigs = map(
                    lambda x: x[0].split(","),
                    filter(
                        lambda x: x[0] is not None,
                        await db.get_matched_sigs_on_host(host_id),
                    ),
                )

                table_data.append(
                    [
                        host_id,
                        ip,
                        hostname,
                        service_count,
                        ",".join(
                            set(
                                sig_name
                                for result in matched_sigs
                                for sig_name in result
                            )
                        ),
                    ]
                )

        table_data = list(sorted(table_data, key=lambda i: (i[3], i[4]), reverse=True))
        table_data.insert(
            0, ["Id", "IP", "Hostname", "Discovered Services", "Matched Signature(s)"]
        )

        table = AsciiTable(table_data)
        table.inner_row_border = True
        table.title = table_title
        print(table.table)

    async def exit(self):
        """
        Guess what this does
        """

        print("Ciao!")

    async def show(self, args):
        """
        Preview a screenshot in the terminal
        """

        try:
            server_id = int(args[0])
        except IndexError:
            print("No server id given")
        except ValueError:
            print("Invalid server id")
        else:
            async with ScanDatabase(connection=self.db) as db:
                entry = await db.get_service_by_id(server_id)
                with open((self.scan_folder_path / entry[2]).absolute(), "rb") as image:
                    imgcat(image)

    async def open(self, args):
        """
        Open a screenshot in your default browser/previewer
        """

        try:
            server_id = int(args[0])
        except IndexError:
            print("No server id given")
        except ValueError:
            print("Invalid server id")
        else:
            async with ScanDatabase(connection=self.db) as db:
                entry = await db.get_service_by_id(server_id)
                screenshot_path = self.scan_folder_path / entry[2]
                webbrowser.open(screenshot_path.absolute().as_uri())

    async def hosts(self, args):
        """
        Show hosts
        """

        async with ScanDatabase(connection=self.db) as db:
            try:
                filter_term = args[0]
            except IndexError:
                hosts = await db.get_hosts()
                await self._print_hosts(hosts)
            else:
                try:
                    host = await db.get_host_by_id(int(filter_term))
                    if not host:
                        raise ValueError(f"No host found with id: {filter_term}")
                except ValueError:
                    query_results = await db.search_hosts(filter_term)
                    await self._print_hosts(query_results)
                else:
                    await self._print_hosts([host])
                    services = await db.get_services_on_host(host[0])
                    await self._print_services(services)

    async def servers(self, args):
        """
        Show discovered servers
        """

        async with ScanDatabase(connection=self.db) as db:
            if len(args):
                query_results = await db.search_services(args[0])
            else:
                query_results = await db.get_services()

            await self._print_services(query_results)

    async def generate_report(self, args):
        """
        Generate a report
        """

        await self.scan()

        if not args or args[0] == "html":
            await generate_html_report(self.scan_folder_path, self.db)
        elif args[0] == "csv":
            await generate_csv_report(self.scan_folder_path, self.db)
        elif args[0] == "json":
            raise NotImplementedError
        else:
            print("Valid report formats are: csv,html,json")

    async def open_html_report(self):
        """
        Open a generated HTML report in the default browser
        """

        report_path = self.scan_folder_path / "witnessme_report.html"
        if not report_path.exists():
            await self.generate_report(["html"])

        webbrowser.open(report_path.absolute().as_uri())

    async def scan(self):
        """
        Peform a signature scan on all discovered servers
        """

        self.signatures.load()

        log.debug("Starting signature scan...")
        start_time = time()
        async with ScanDatabase(connection=self.db) as db:
            tasks = [
                self.signatures.find_match(service)
                for service in await db.get_services()
            ]

            matches = list(
                filter(lambda x: len(x[0]) > 0, await asyncio.gather(*tasks))
            )

            for match in matches:
                await db.add_matched_sigs_to_service(
                    match[1][0], ",".join([sig["name"] for sig in match[0]])
                )

            completed_time = strftime("%Mm%Ss", gmtime(time() - start_time))
            log.debug(
                f"Signature scan completed, identified {len(matches)} service(s) in {completed_time}"
            )

    async def cmdloop(self):
        self.db = await aiosqlite.connect(self.db_path)

        try:
            while True:
                # with patch_stdout():
                text = await self.prompt_session.prompt_async()
                command = shlex.split(text)
                if len(command):
                    # Apperently you can't call await on a coroutine retrieved via getattr() ??
                    # So this sucks now but thankfully we don't have a lot of commands
                    try:
                        if command[0] == "exit":
                            await self.exit()
                            break
                        elif command[0] == "show":
                            await self.show(command[1:])
                        elif command[0] == "generate_report":
                            await self.generate_report(command[1:])
                        elif command[0] == "open_html_report":
                            await self.open_html_report()
                        elif command[0] == "open":
                            await self.open(command[1:])
                        elif command[0] == "hosts":
                            await self.hosts(command[1:])
                        elif command[0] == "servers":
                            await self.servers(command[1:])
                        elif command[0] == "scan":
                            await self.scan()
                        else:
                            print("Command does not exist")
                    except Exception as e:
                        import traceback

                        traceback.print_exc()
                        print(f"Error calling command '{command[0]}': {e}")
        finally:
            await self.db.close()


def run():
    parser = argparse.ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("scan_folder", type=str, help="WitnessMe scan folder")
    args = parser.parse_args()

    scan_folder = pathlib.Path(args.scan_folder)
    # For backwards compatibility, handle pointing directly to the database
    if scan_folder.name == "witnessme.db":
        scan_folder = scan_folder.parent

    db_path = scan_folder / "witnessme.db"
    if not db_path.exists():
        print("Unable to find db, not a WitnessMe scan folder or invalid path?")
        sys.exit(1)

    print("[!] Press tab for autocompletion and available commands")
    dbcli = WMDBShell(scan_folder.expanduser())
    asyncio.run(dbcli.cmdloop())


if __name__ == "__main__":
    run()
