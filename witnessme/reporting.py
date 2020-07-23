import csv
import logging
import pkg_resources
from jinja2 import Template
from witnessme.database import ScanDatabase

log = logging.getLogger("witnessme.reporting")


async def generate_html_report(scan_folder, db):
    results_per_page = 100
    template_path = pkg_resources.resource_filename(__name__, "templates/template.html")

    log.info("Generating HTML report, please wait...")
    async with ScanDatabase(connection=db) as db:
        service_count = await db.get_service_count()
        total_pages = (
            service_count // results_per_page
            if service_count % results_per_page == 0
            else (service_count // results_per_page) + 1
        )

        current_page = 1
        offset = 0
        while True:
            services = await db.get_services_with_host(
                limit=results_per_page, offset=offset
            )
            if not services:
                break

            report_file = scan_folder / f"report_page_{current_page}.html"
            if current_page == 1:
                report_file = scan_folder / "witnessme_report.html"

            with open(report_file, "w") as report:
                with open(template_path) as file_:
                    template = Template(file_.read())
                    report.write(
                        template.render(
                            name="WitnessMe Report",
                            current_page=current_page,
                            total_pages=total_pages,
                            services=services,
                        )
                    )

            current_page += 1
            offset += results_per_page
        log.info("Done")


async def generate_csv_report(scan_folder, db):
    result_limit = 100
    csv_path = scan_folder / "witnessme_report.csv"

    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "url",
                "ip",
                "hostname",
                "port",
                "scheme",
                "title",
                "server",
                "screenshot",
                "matched_sigs",
            ]
        )

        log.info("Generating CSV report, please wait...")
        async with ScanDatabase(connection=db) as db:
            offset = 0
            while True:
                services = await db.get_services_with_host(
                    limit=result_limit, offset=offset
                )
                if not services:
                    break

                for service in services:
                    writer.writerow(
                        [
                            service[1],
                            service[12],
                            service[11],
                            service[3],
                            service[4],
                            service[5],
                            service[6],
                            service[2],
                            service[9],
                        ]
                    )

                offset += result_limit
            log.info("Done")
