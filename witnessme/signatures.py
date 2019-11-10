import os
import logging
import yaml
import pathlib

class Signatures:
    def __init__(self, sig_folder='./witnessme/signatures'):
        self.sig_folder = pathlib.Path(sig_folder)
        self.signatures = []

    def load(self):
        self.signatures = []
        for sig_file in os.listdir(self.sig_folder):
            with open(self.sig_folder.joinpath(sig_file).absolute()) as sig:
                self.signatures.append(yaml.load(sig, Loader=yaml.CLoader))

        logging.debug(f"Loaded {len(self.signatures)} signature(s)")

    def get_sig(self, name: str):
        return list(filter(lambda sig: sig['name'] == name, self.signatures))[0]

    async def find_match(self, service):
        matches = []
        for sig in self.signatures:
            if len(list(filter(lambda x: x > 0, map(lambda s: service[-1].find(s), sig['signatures'])))):
                logging.debug(f"Matched {service[1]} for signature \'{sig['name']}\'")
                matches.append(sig)
        return matches, service
