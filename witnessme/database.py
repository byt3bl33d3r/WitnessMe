import aiosqlite
import json
import logging

log = logging.getLogger("witnessme.database")


class ScanDatabase:
    def __init__(self, report_folder=None, connection=None):
        self.report_folder = report_folder
        self.connection = connection

    @staticmethod
    async def create_db_and_schema(report_folder):
        async with aiosqlite.connect(f"{report_folder}/witnessme.db") as db:
            await db.execute(
                """CREATE TABLE "hosts" (
                "id" integer PRIMARY KEY,
                "hostname" text,
                "ip" text,
                UNIQUE(hostname, ip)
            )"""
            )

            await db.execute(
                """CREATE TABLE "services" (
                "id" integer PRIMARY KEY,
                "url" text,
                "screenshot" text,
                "port" integer,
                "scheme" text,
                "title" text,
                "server" text,
                "headers" text,
                "host_id" integer,
                "matched_sigs" text,
                "body" text,
                FOREIGN KEY(host_id) REFERENCES hosts(id),
                UNIQUE(port, host_id, scheme)
            )"""
            )

            await db.commit()

    async def add_host(self, ip, hostname):
        return await self.db.execute(
            "INSERT OR IGNORE INTO hosts (ip, hostname) VALUES (?,?)", [ip, hostname]
        )

    async def add_service(
        self, url, screenshot, port, scheme, title, server, headers, body, host_id
    ):
        return await self.db.execute(
            "INSERT OR IGNORE INTO services (url, screenshot, port, scheme, title, server, headers, body, host_id) VALUES (?,?,?,?,?,?,?,?,?)",
            [url, screenshot, port, scheme, title, server, headers, body, host_id],
        )

    async def add_host_and_service(
        self, ip, hostname, url, screenshot, port, scheme, title, server, headers, body
    ):
        cursor = await self.add_host(ip, hostname)
        host_id = cursor.lastrowid
        if host_id == 0:
            async with self.db.execute(
                "SELECT id FROM hosts WHERE ip=(?) AND hostname=(?)", [ip, hostname]
            ) as cursor:
                row = await cursor.fetchone()
                host_id = row[0]

        await self.add_service(
            url,
            screenshot,
            port,
            scheme,
            title,
            server,
            json.dumps(headers),
            body,
            host_id,
        )

    async def add_matched_sigs_to_service(self, service_id, matches):
        if await self.get_service_by_id(service_id):
            await self.db.execute(
                "UPDATE services SET matched_sigs=(?) WHERE id=(?)",
                [matches, service_id],
            )

    async def get_matched_sigs_on_host(self, host_id: int):
        async with self.db.execute(
            "SELECT matched_sigs FROM services WHERE host_id=(?)", [host_id]
        ) as cursor:
            return await cursor.fetchall()

    async def get_service_count(self):
        async with self.db.execute("SELECT count(*) FROM services") as cursor:
            result = await cursor.fetchone()
            return result[0]

    async def get_host_count(self):
        async with self.db.execute("SELECT count(*) FROM hosts") as cursor:
            result = await cursor.fetchone()
            return result[0]

    async def get_service_count_on_host(self, host_id: int):
        async with self.db.execute(
            "SELECT count(*) FROM services WHERE host_id=(?)", [host_id]
        ) as cursor:
            result = await cursor.fetchone()
            return result[0]

    async def get_services_on_host(self, host_id: int):
        async with self.db.execute(
            "SELECT * FROM services WHERE host_id=(?)", [host_id]
        ) as cursor:
            result = await cursor.fetchall()
            return result

    async def get_service_by_id(self, service_id: int):
        async with self.db.execute(
            "SELECT * FROM services WHERE id=(?)", [service_id]
        ) as cursor:
            return await cursor.fetchone()

    async def get_host_by_id(self, host_id: int):
        async with self.db.execute(
            "SELECT * FROM hosts WHERE id=(?)", [host_id]
        ) as cursor:
            return await cursor.fetchone()

    async def get_hosts(self, limit=-1, offset=-1):
        async with self.db.execute(
            "SELECT * FROM hosts LIMIT (?) OFFSET (?)", [limit, offset]
        ) as cursor:
            return await cursor.fetchall()

    async def get_services(self, limit=-1, offset=-1):
        async with self.db.execute(
            "SELECT * FROM services LIMIT (?) OFFSET (?)", [limit, offset]
        ) as cursor:
            return await cursor.fetchall()

    async def get_services_with_host(self, limit=-1, offset=-1):
        services_with_hosts = []

        async with self.db.execute(
            "SELECT * FROM services LIMIT (?) OFFSET (?)", [limit, offset]
        ) as cursor:
            services = await cursor.fetchall()

        for service in services:
            _, hostname, ip = await self.get_host_by_id(service[8])
            services_with_hosts.append(service + (hostname, ip))

        return services_with_hosts

    async def search_hosts(self, search: str):
        async with self.db.execute(
            "SELECT * FROM hosts WHERE ip LIKE (?) OR hostname LIKE (?)",
            [f"%{search}%"] * 2,
        ) as cursor:
            return await cursor.fetchall()

    async def search_services(self, search: str):
        async with self.db.execute(
            "SELECT * FROM services WHERE title LIKE (?) OR server LIKE (?)",
            [f"%{search}%"] * 2,
        ) as cursor:
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
