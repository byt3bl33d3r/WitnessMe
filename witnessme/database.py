import aiosqlite
import os
import json
from datetime import datetime

class ScanDatabase:
    def __init__(self, report_folder=None, connection=None):
        self.report_folder = report_folder
        self.connection = connection

    @staticmethod
    async def create_db_and_schema(report_folder):
        async with aiosqlite.connect(f"{report_folder}/witnessme.db") as db:
            await db.execute('''CREATE TABLE "hosts" (
                "id" integer PRIMARY KEY,
                "hostname" text,
                "ip" text,
                UNIQUE(hostname, ip)
            )''')

            await db.execute('''CREATE TABLE "services" (
                "id" integer PRIMARY KEY,
                "url" text,
                "screenshot" text,
                "port" integer,
                "scheme" text,
                "title" text,
                "server" text,
                "headers" text,
                "host_id" integer,
                FOREIGN KEY(host_id) REFERENCES hosts(id),
                UNIQUE(port, host_id, scheme)
            )''')

            await db.commit()

    async def add_host(self, ip, hostname):
        return await self.db.execute("INSERT OR IGNORE INTO hosts (ip, hostname) VALUES (?,?)", [ip, hostname])

    async def add_service(self, url, screenshot, port, scheme, title, server, headers, host_id):
        return await self.db.execute(
            "INSERT OR IGNORE INTO services (url, screenshot, port, scheme, title, server, headers, host_id) VALUES (?,?,?,?,?,?,?,?)",
            [url, screenshot, port, scheme, title, server, headers, host_id]
        )

    async def add_host_and_service(self, ip, hostname, url, screenshot, port, scheme, title, server, headers):
        cursor = await self.add_host(ip, hostname)
        host_id = cursor.lastrowid
        if host_id == 0:
            async with self.db.execute("SELECT id FROM hosts WHERE ip=(?) AND hostname=(?)", [ip, hostname]) as cursor:
                row = await cursor.fetchone()
                host_id = row[0]

        await self.add_service(url, screenshot, port, scheme, title, server, json.dumps(headers), host_id)

    async def get_service_count(self):
        async with self.db.execute("SELECT count(*) FROM services") as cursor:
            result = await cursor.fetchone()
            return result[0]

    async def get_host_count(self):
        async with self.db.execute("SELECT count(*) FROM hosts") as cursor:
            result = await cursor.fetchone()
            return result[0]
    
    async def get_services_on_host(self, host_id: int):
        async with self.db.execute("SELECT * FROM services WHERE host_id=(?)", [host_id]) as cursor:
            result = await cursor.fetchall()
            return result

    async def get_service_by_id(self, service_id: int):
        async with self.db.execute("SELECT * FROM services WHERE id=(?)", [service_id]) as cursor:
            return await cursor.fetchone()
    
    async def get_host_by_id(self, host_id: int):
        async with self.db.execute("SELECT * FROM hosts WHERE id=(?)", [host_id]) as cursor:
            return await cursor.fetchone()

    async def get_hosts(self):
        async with self.db.execute("SELECT * FROM hosts") as cursor:
            return await cursor.fetchall()

    async def get_services(self):
        async with self.db.execute("SELECT * FROM services") as cursor:
            return await cursor.fetchall()

    async def search_hosts(self, search: str):
        async with self.db.execute("SELECT * FROM hosts WHERE ip LIKE (?) OR hostname LIKE (?)", [f"%{search}%"] * 2) as cursor:
            return await cursor.fetchall()

    async def search_services(self, search: str):
        async with self.db.execute("SELECT * FROM services WHERE title LIKE (?) OR server LIKE (?)", [f"%{search}%"] * 2) as cursor:
            return await cursor.fetchall()

    async def __aenter__(self):
        if not self.connection:
            self.db = await aiosqlite.connect(f"{self.report_folder}/witnessme.db")
        else:
            self.db = self.connection
        return self

    async def __aexit__(self, exec_type, exc, tb):
        await self.db.commit()
        if not self.connection:
            await self.db.close()
