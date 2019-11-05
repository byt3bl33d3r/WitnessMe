#! /usr/bin/env python3

import asyncio
import argparse
import shlex
import sys
import pathlib
import logging
#import json
#import functools
import aiosqlite
import webbrowser
from imgcat import imgcat
from terminaltables import AsciiTable
from witnessme.database import ScanDatabase
from argparse import ArgumentDefaultsHelpFormatter
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.eventloop import use_asyncio_event_loop
from prompt_toolkit.patch_stdout import patch_stdout
#from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
#from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.styles import Style

#from prompt_toolkit.document import Document

class WMCompleter(Completer):
    def __init__(self, cli_menu):
        self.cli_menu = cli_menu

    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor()
        try:
            cmd_line = list(map(lambda s: s.lower(), shlex.split(document.current_line)))
        except ValueError:
            pass
        else:
            for cmd in ["exit", "show", "open", "hosts", "servers"]:
                if cmd.startswith(word_before_cursor):
                    yield Completion(cmd, -len(word_before_cursor), display_meta=getattr(self.cli_menu, cmd).__doc__.strip())

class WMDBShell:
    def __init__(self, db_path):
        self.db_path = db_path
        
        self.completer = WMCompleter(self)
        self.prompt_session = PromptSession(
            HTML("WMDB ≫ "),
            #bottom_toolbar=functools.partial(bottom_toolbar, ts=self.teamservers),
            completer=self.completer,
            complete_in_thread=True,
            complete_while_typing=True,
            auto_suggest=AutoSuggestFromHistory(),
            #rprompt=get_rprompt(False),
            #style=example_style,
            search_ignore_case=True
        )

    async def exit(self, *args, **kwargs):
        """
        Guess what this does
        """

        print("Ciao!")

    async def show(self, *args, **kwargs):
        """
        Preview screenshot in Terminal
        """
        async with ScanDatabase(connection=self.db) as db:
            entry = await db.get_service_by_id(int(*args[0]))
            _,_,screenshot_path,_,_,_,_,_,_ = entry
            imgcat(open(screenshot_path))

    async def open(self, *args, **kwargs):
        """
        Open screenshot in browser/previewer
        """
        async with ScanDatabase(connection=self.db) as db:
            entry = await db.get_service_by_id(int(*args[0]))
            _,_,screenshot_path,_,_,_,_,_,_ = entry
            screenshot_path = str(pathlib.Path(screenshot_path).absolute())
            webbrowser.open(screenshot_path.replace("/", "file:////", 1))

    async def hosts(self, *args, **kwargs):
        """
        Show hosts
        """
        async with ScanDatabase(connection=self.db) as db:
            table_data = [["Id", "IP", "Hostname"]]
            for entry in await db.get_hosts():
                host_id, hostname, ip = entry
                table_data.append([host_id, ip, hostname])

            table = AsciiTable(table_data)
            table.inner_row_border = True
            print(table.table)

    async def servers(self, *args, **kwargs):
        """
        Show discovered servers
        """
        async with ScanDatabase(connection=self.db) as db:
            table_data = [["Id", "URL", "Title", "Server"]]
            for entry in await db.get_services():
                service_id, url,_,_,_,title,server,_,_ = entry
                table_data.append([
                    service_id,
                    url,
                    title,
                    server
                ])

            table = AsciiTable(table_data)
            table.inner_row_border = True
            print(table.table)

    async def cmdloop(self):
        use_asyncio_event_loop()
        self.db = await aiosqlite.connect(self.db_path)

        try:
            while True:
                #with patch_stdout():
                text = await self.prompt_session.prompt(async_=True)
                command = shlex.split(text)
                if len(command):
                    # Apperently you can't call await on a method retrieved via getattr() ??
                    # So this sucks now but thankfully we don't have a lot of commands
                    try:
                        if command[0] == 'exit':
                            await self.exit(command[1:])
                            break
                        elif command[0] == 'show':
                            await self.show(command[1:])
                        elif command[0] == 'open':
                            await self.open(command[1:])
                        elif command[0] == 'hosts':
                            await self.hosts(command[1:])
                        elif command[0] == 'servers':
                            await self.servers(command[1:])
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        print(f"Error calling command '{command[0]}': {e}")
        finally:
            await self.db.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("db_path", type=str, help='WitnessMe database path to open')
    args = parser.parse_args()

    db_path = pathlib.Path(args.db_path)
    if not db_path.exists():
        print("Path to db doesn't appear to be valid")
        sys.exit(1)

    dbcli = WMDBShell(str(db_path.expanduser()))
    print("[!] Press tab for autocompletion and available commands")
    asyncio.run(dbcli.cmdloop())
