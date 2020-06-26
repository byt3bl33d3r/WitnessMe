import os
import logging
import yaml
import pathlib

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

log = logging.getLogger("witnessme.signatures")


class Signatures:
    def __init__(self, sig_folder="./witnessme/signatures"):
        self.sig_folder = pathlib.Path(sig_folder)
        self.signatures = []

    def load(self):
        self.signatures = []
        for sig_file in os.listdir(self.sig_folder):
            with open(self.sig_folder.joinpath(sig_file).absolute()) as sig:
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
