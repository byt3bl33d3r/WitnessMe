import os
import pkg_resources
import logging
import yaml
import pathlib

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

log = logging.getLogger("witnessme.signatures")


class Signatures:
    def __init__(self, sig_folder=None):
        self.signatures = []
        self.sig_folder = sig_folder
        if not sig_folder:
            self.sig_folder = pathlib.Path(
                pkg_resources.resource_filename(__name__, "signatures")
            )

    def load(self):
        self.signatures = []

        for sig_file in os.listdir(self.sig_folder):
            sig_file_path = self.sig_folder / sig_file
            with open(sig_file_path.absolute()) as sig:
                self.signatures.append(yaml.load(sig, Loader=Loader))

        log.debug(f"Loaded {len(self.signatures)} signature(s)")

    def get_sig(self, name: str):
        return next(filter(lambda s: s["name"] == name, self.signatures), None)

    async def find_match(self, service):
        matches = []
        for sig in self.signatures:
            if all(
                i > 0 for i in map(lambda s: service[-1].find(s), sig["signatures"])
            ):
                log.debug(f"Matched {service[1]} for signature '{sig['name']}'")
                matches.append(sig)
        return matches, service
