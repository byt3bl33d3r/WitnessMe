import aiosqlite
import os
import json
from datetime import datetime

class ScanDatabase:
    def __init__(self, report_folder):
        self.report_folder = report_folder

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
                "screenshot_path" text,
                "port" integer,
                "name" text,
                "headers" text,
                "title" text,
                "host_id" integer,
                FOREIGN KEY(host_id) REFERENCES hosts(id),
                UNIQUE(port, host_id, name)
            )''')

            await db.commit()

    async def add_host(self, ip, hostname):
        return await self.db.execute("INSERT OR IGNORE INTO hosts (ip, hostname) VALUES (?,?)", [ip, hostname])

    async def add_service(self, url, screenshot_path, port, name, headers, title, host_id):
        return await self.db.execute(
            "INSERT OR IGNORE INTO services (url, screenshot_path, port, name, headers, title, host_id) VALUES (?,?,?,?,?,?,?)",
            [url, screenshot_path, port, name, headers, title, host_id]
        )

    async def add_host_and_service(self, url, screenshot_path, ip, hostname, port, svc_name, headers, title):
        cursor = await self.add_host(ip, hostname)
        host_id = cursor.lastrowid
        if host_id == 0:
            async with self.db.execute("SELECT id FROM hosts WHERE ip=(?) AND hostname=(?)", [ip, hostname]) as cursor:
                row = await cursor.fetchone()
                host_id = row[0]

        await self.add_service(url, screenshot_path, port, svc_name, json.dumps(headers), title, host_id)
    
    async def get_service_count(self):
        async with self.db.execute("SELECT count(*) FROM services") as cursor:
            result = await cursor.fetchone()
            return result[0]

    async def get_host_count(self):
        async with self.db.execute("SELECT count(*) FROM hosts") as cursor:
            result = await cursor.fetchone()
            return result[0]

    async def __aenter__(self):
        self.db = await aiosqlite.connect(f"{self.report_folder}/witnessme.db")
        return self

    async def __aexit__(self, exec_type, exc, tb):
        await self.db.commit()
        await self.db.close()
