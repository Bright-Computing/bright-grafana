import os
import json

from cluster_config import ClusterConfig


class ConfigFile:
    def __init__(self, filename):
        self.filename = filename
        self.clusters = []

    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as fd:
                self.clusters = [ClusterConfig.load(it) for it in json.load(fd)]
            return True
        return False

    def save(self):
        with open(self.filename, 'w+') as fd:
            json.dump([it.save() for it in self.clusters], fd, indent=2)

    def find(self, hostname):
        return next((it for it in self.clusters if it.hostname == hostname), None)
