import sys
import xmltodict
import pathlib
import logging
from collections import OrderedDict
from ipaddress import ip_address, ip_network, summarize_address_range
from contextlib import ContextDecorator

log = logging.getLogger("witnessme.parsers")


class TargetGenerator(ContextDecorator):
    def __init__(self, target, ports=[80, 8080, 443, 8443]):
        self.target = target
        self.ports = ports

    def expand_ip_cidr_or_range(self, target):
        try:
            if "-" in target:
                start_ip, end_ip = target.split("-")
                try:
                    end_ip = ip_address(end_ip)
                except ValueError:
                    first_three_octets = start_ip.split(".")[:-1]
                    first_three_octets.append(end_ip)
                    end_ip = ip_address(".".join(first_three_octets))

                for ip_range in summarize_address_range(ip_address(start_ip), end_ip):
                    for ip in ip_range:
                        yield str(ip)
            else:
                for ip in ip_network(target, strict=False):
                    yield str(ip)
        except ValueError:
            yield str(target)

    def __enter__(self):
        if self.target.startswith("http://") or self.target.startswith("https://"):
            yield self.target
        elif self.target.startswith("http-simple-new://"):
            yield self.target.replace("http-simple-new://", "http://")
        elif self.target.startswith("https-simple-new://"):
            yield self.target.replace("https-simple-new://", "https://")
        else:
            for host in self.expand_ip_cidr_or_range(self.target):
                for port in self.ports:
                    for scheme in ["http", "https"]:
                        yield f"{scheme}://{host}:{port}"

    def __exit__(self, *exc):
        pass


class GenericFileParser(ContextDecorator):
    def __init__(self, file_path, ports=[80, 8080, 443, 8443]):
        self.file_path = file_path
        self.ports = ports

    def __enter__(self):
        with open(self.file_path) as target_file:
            for target in target_file:
                with TargetGenerator(
                    target.strip(), ports=self.ports
                ) as target_generator:
                    for url in target_generator:
                        yield url

    def __exit__(self, *exc):
        pass


class XmlParser(ContextDecorator):
    def __init__(self, file_path):
        self.xml_file_path = file_path
        self.item_depth = 4
        self.https_ports = [443, 8443]
        self.http_ports = [80, 8080]
        self.urls = set()

    def parser_callback(self, path, item):
        return True

    def __enter__(self):
        with open(self.xml_file_path, "rb") as xml_file_path:
            xmltodict.parse(
                xml_file_path,
                item_depth=self.item_depth,
                item_callback=self.parser_callback,
                process_namespaces=True,
            )

            for url in self.urls:
                yield url

    def __exit__(self, *exc):
        self.urls = set()


class NmapParser(XmlParser):
    def __init__(self, file_path):
        super().__init__(file_path)
        self.item_depth = 2

    def parser_callback(self, path, item):
        if isinstance(item, OrderedDict):
            if "address" in item.keys() and "ports" in item.keys():
                address = item["address"]["@addr"]
                ports = item["ports"]["port"]

                # If there's only a single port discovered, ports will be an OrderedDict
                if isinstance(ports, OrderedDict):
                    ports = [ports]

                for port in ports:
                    if port["@protocol"] == "tcp" and port["state"]["@state"] == "open":
                        service = port["service"].get("@name")
                        port_number = port["@portid"]
                        if "ssl" in service or service == "https":
                            self.urls.add(f"https://{address}:{port_number}")
                        elif service == "http-alt" or service == "http":
                            self.urls.add(f"http://{address}:{port_number}")
        return True


class NessusParser(XmlParser):
    def parser_callback(self, path, item):
        """
        Apperently, Nessus's plugins are far from being consistent when trying to detect http/https pages
        https://github.com/FortyNorthSecurity/EyeWitness/blob/master/modules/helpers.py#L100-L106
        https://github.com/FortyNorthSecurity/EyeWitness/blob/master/modules/helpers.py#L225-L230
        """
        entry = dict(path)
        if entry.get("ReportItem"):
            report_item = entry["ReportItem"]

            if (
                report_item.get("port")
                and report_item.get("svc_name")
                and report_item.get("pluginName")
            ):

                if (
                    report_item["svc_name"] == "https?"
                    or int(report_item["port"]) in self.https_ports
                ):
                    self.urls.add(
                        f"https://{entry['ReportHost']['name']}:{report_item['port']}"
                    )

                elif (
                    report_item["pluginID"] == "22964"
                    and report_item["svc_name"] == "www"
                ):
                    plugin_output = item.get("plugin_output")
                    if plugin_output.lower() in [
                        "a web server is running on this port.",
                        "a web server is running on the remote host.",
                    ]:
                        self.urls.add(
                            f"http://{entry['ReportHost']['name']}:{report_item['port']}"
                        )
                    elif plugin_output.lower().startswith(
                        "a web server is running on this port through"
                    ):
                        self.urls.add(
                            f"https://{entry['ReportHost']['name']}:{report_item['port']}"
                        )

                elif report_item["svc_name"] in ["www", "http?"]:
                    self.urls.add(
                        f"http://{entry['ReportHost']['name']}:{report_item['port']}"
                    )
        return True


class AutomaticTargetGenerator(ContextDecorator):
    def __init__(self, targets: list, ports=[80, 8080, 443, 8443]):
        self.targets = targets
        self.ports = ports

    def generate(self, targets):
        for target in targets:
            target = target.strip()

            if pathlib.Path(target).exists():
                target = str(pathlib.Path(target).expanduser())
                if target.lower().endswith(".nessus"):
                    log.debug("Detected .nessus file as a target")
                    file_parser = NessusParser(target)
                elif target.lower().endswith(".xml"):
                    log.debug("Detected NMap XML file as a target")
                    file_parser = NmapParser(target)
                else:
                    log.debug("Detected file as a target")
                    file_parser = GenericFileParser(target, ports=self.ports)

                with file_parser as generated_urls:
                    for url in generated_urls:
                        yield url
            else:
                log.debug("Detected IP Address/Range/CIDR, hostname or URL as a target")
                with TargetGenerator(target, ports=self.ports) as generated_urls:
                    for url in generated_urls:
                        yield url

    def __enter__(self):
        if "-" in self.targets:
            log.debug("Reading targets from stdin")
            return self.generate(sys.stdin)

        return self.generate(self.targets)

    def __exit__(self, *exc):
        pass
