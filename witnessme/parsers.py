import xmltodict
import pathlib
import logging
from ipaddress import ip_address, ip_network, summarize_address_range
from contextlib import ContextDecorator

class IPTargetGenerator(ContextDecorator):
    def __init__(self, ip_cidr_or_range, ports = [80, 8080, 443, 8443]):
        self.ip_cidr_or_range = ip_cidr_or_range
        self.ports = ports

    def expand_ip_cidr_or_range(self, target):
        try:
            if '-' in target:
                start_ip, end_ip = target.split('-')
                try:
                    end_ip = ip_address(end_ip)
                except ValueError:
                    first_three_octets = start_ip.split(".")[:-1]
                    first_three_octets.append(end_ip)
                    end_ip = ip_address(
                                ".".join(first_three_octets)
                            )

                for ip_range in summarize_address_range(ip_address(start_ip), end_ip):
                    for ip in ip_range:
                        yield str(ip)
            else:
                for ip in ip_network(target, strict=False): yield str(ip)
        except ValueError:
            yield str(target)

    def __enter__(self):
        for host in self.expand_ip_cidr_or_range(self.ip_cidr_or_range):
            for port in self.ports:
                for scheme in ["http", "https"]:
                    yield f"{scheme}://{host}:{port}"
    
    def __exit__(self, *exc):
        pass

class UrlFileParser(ContextDecorator):
    def __init__(self, file_path):
        self.file_path = file_path

    def __enter__(self):
        with open(self.file_path) as url_file:
            for url in url_file:
                yield url.strip()
    
    def __exit__(self, *exc):
        pass

class XmlParser(ContextDecorator):
    def __init__(self, file_path):
        self.xml_file_path = file_path
        self.item_depth = 4
        self.urls = set()

    def parser_callback(self, path, item):
        return True

    def __enter__(self):
        with open(self.xml_file_path, 'rb') as xml_file_path:
            xmltodict.parse(
                xml_file_path,
                item_depth=self.item_depth,
                item_callback=self.parser_callback,
                process_namespaces=True
            )

            for url in self.urls:
                yield url

    def __exit__(self, *exc):
        self.urls = set()

class NmapParser(XmlParser):
    def parser_callback(self, path, item):
        return True

class NessusParser(XmlParser):
    def parser_callback(self, path, item):
        """
        Apperently, Nessus's plugins are far from being consistent when trying to detect http/https pages
        https://github.com/FortyNorthSecurity/EyeWitness/blob/master/modules/helpers.py#L100-L106
        https://github.com/FortyNorthSecurity/EyeWitness/blob/master/modules/helpers.py#L225-L230
        """

        try:
            entry = dict(path)
            if entry['ReportItem']['svc_name'] == 'https?':
                self.urls.add(f"https://{entry['ReportHost']['name']}:{entry['ReportItem']['port']}")

            elif entry['ReportItem']['pluginID'] == "22964" and entry['ReportItem']['svc_name'] == 'www':
                if "A web server is running on this port through" in dict(item)['plugin_output']:
                    self.urls.add(f"https://{entry['ReportHost']['name']}:{entry['ReportItem']['port']}")
                else:
                    self.urls.add(f"http://{entry['ReportHost']['name']}:{entry['ReportItem']['port']}")

            elif entry['ReportItem']['svc_name'] in ['http?', 'www']:
                self.urls.add(f"http://{entry['ReportHost']['name']}:{entry['ReportItem']['port']}")
        except KeyError:
            pass

        return True

class AutomaticTargetGenerator(ContextDecorator):
    def __init__(self, targets: list):
        self.targets = targets

    def __enter__(self):
        for target in self.targets:
            if pathlib.Path(target).exists():
                target = str(pathlib.Path(target).expanduser())
                if target.lower().endswith(".nessus"):
                    logging.debug("Detected .nessus file as a target")
                    file_parser = NessusParser(target)
                elif target.lower().endswith(".xml"):
                    logging.debug("Detected NMap XML file as a target")
                    file_parser = NmapParser(target)
                else:
                    logging.debug("Detected URL file as a target")
                    file_parser = UrlFileParser(target)

                with file_parser as generated_urls:
                    for url in generated_urls:
                        yield url
                
            else:
                logging.debug("Detected IP Range or CIDR as a target")
                with IPTargetGenerator(target) as generated_urls:
                    for url in generated_urls:
                        yield url

    def __exit__(self, *exc):
        pass
