import os
import sys

import urllib.request

from https_client_auth_handler import HTTPSClientAuthHandler


class ClusterConfig:
    def __init__(self, hostname=None, port=8081):
        self.hostname = hostname
        self.port = port
        self.name = None
        self.version = None
        self.build_index = None
        self.certificate = None
        self.private_key = None
        self.ca_file = 'pythoncm/etc/cacert.pem'

    def get_cluster(self, auto_connect=False, redirect=False):
        self.create_symlink()

        from pythoncm.cluster import Cluster
        from pythoncm.settings import Settings

        settings = Settings(host=self.hostname,
                            port=self.port,
                            cert_file=self.certificate,
                            key_file=self.private_key,
                            ca_file=self.ca_file)
        return Cluster(settings,
                       auto_connect=auto_connect,
                       follow_redirect=Cluster.REDIRECT_ACTIVE if redirect else Cluster.REDIRECT_NONE)

    def get_version(self):
        url = f'https://{self.hostname}:{self.port}/info/version'
        opener = urllib.request.build_opener(HTTPSClientAuthHandler(),
                                             urllib.request.ProxyHandler({}))
        request = urllib.request.Request(url)
        response = opener.open(request)
        self.version = response.read().decode('utf-8')
        return len(self.version) > 0

    def get_build_index(self):
        url = f'https://{self.hostname}:{self.port}/info/build_index'
        opener = urllib.request.build_opener(HTTPSClientAuthHandler(),
                                             urllib.request.ProxyHandler({}))
        request = urllib.request.Request(url)
        response = opener.open(request)
        try:
            self.build_index = int(response.read().decode('utf-8'))
            return True
        except ValueError:
            return False

    def save(self):
        return {'hostname': self.hostname,
                'port': self.port,
                'name': self.name,
                'version': self.version,
                'certificate': self.certificate,
                'private_key': self.private_key}

    @property
    def python_version(self):
        if self.version == '8.2':
            return 2
        return 3

    @property
    def cluster_pythoncm_directory(self):
        if self.version == '8.2':
            return '/cm/local/apps/python2/lib/python2.7/site-packages/pythoncm'
        if self.version in ['9.0', '9.1']:
            return '/cm/local/apps/python37/lib/python3.7/site-packages/pythoncm'
        if bool(self.build_index) and self.build_index > 148338:
            return '/cm/local/apps/cmd/pythoncm/lib/python3.9/site-packages/pythoncm'
        return '/cm/local/apps/python39/lib/python3.9/site-packages/pythoncm'

    @property
    def pythoncm_directory(self):
        return f'pythoncm_{self.version.replace(".","")}'

    @classmethod
    def load(cls, data):
        cluster = ClusterConfig()
        for key, value in data.items():
            setattr(cluster, key, value)
        return cluster

    def create_symlink(self, target='pythoncm'):
        if os.path.exists(target):
            if os.path.islink(target):
                if os.readlink(target) == self.pythoncm_directory:
                    return False
                os.remove(target)
            else:
                raise FileExistsError
        print(f'*** Switch to {self.pythoncm_directory} ***')
        # unload all old pythoncm modules, to make sure we load the new ones after this
        for name in list(sys.modules.keys()):
            if name.startswith('pythoncm.'):
                del sys.modules[name]
        os.symlink(self.pythoncm_directory, target)
        return True

    def create_certificate(self, username, password, name='grafana', profile_name='grafana'):
        self.create_symlink()

        from pythoncm.cluster import Cluster
        from pythoncm.settings import Settings
        from pythoncm.entity import Certificate, Profile

        settings = Settings(host=self.hostname,
                            port=self.port,
                            ca_file=self.ca_file)
        if settings.get_cookie(username, password):
            cluster = Cluster(settings, follow_redirect=Cluster.REDIRECT_NONE)
            profile = cluster.get_by_name(profile_name, 'Profile')
            result = True
            if profile is None:
                profile = Profile(cluster)
                profile.name = profile_name
                profile.nonuser = True
                profile.accessServices = ['CMMon']
                profile.tokens = ['PLOT_TOKEN',
                                  'PRIVATE_MONITORING_TOKEN',
                                  'GET_LABELED_ENTITY_TOKEN']
                commit_result = profile.commit()
                if not commit_result.good:
                    print(f'*** Failed to create {profile_name} profile ***')
                    print(commit_result)
                    result = False
            if result:
                certificate = Certificate(cluster)
                if certificate.create(name, profile=profile_name):
                    self.name = cluster.name
                    self.certificate = f'{self.name}.pem'
                    self.private_key = f'{self.name}.key'
                    certificate.save(filename=self.certificate, private_key_file=self.private_key)
                    print(f'*** Saved {name} certificate for cluster {self.name} with profile {profile_name} ***')
                else:
                    result = False
            cluster.disconnect()
            return result
        else:
            raise IOError(settings.cookie)

    def update_datasource(self, path):
        filename = f'{path}/{self.name}.yaml'
        with open(filename, 'w') as fd:
            fd.write(self._datasource)
        print(f'*** Saved {filename} ***')

    def _read_file(self, filename, indent=0):
        with open(filename, 'r') as fd:
            lines = [' ' * indent + it for it in fd.readlines()]
        return ''.join(lines)

    @property
    def _datasource(self):
        return f'''# created by bright-grafana
apiVersion: 1

datasources:
- name: {self.name}
  type: prometheus
  access: proxy
  url: https://{self.hostname}:{self.port}/prometheus

  version: 1
  editable: true

  basicAuth: false
  withCredentials: true

  jsonData:
     httpMethod: GET
     tlsAuth: true
     tlsSkipVerify: false
     serverName: master.cm.cluster
     tlsAuthWithCACert: true
  secureJsonData:
    tlsCACert: |
{self._read_file(self.ca_file, indent=6)}
    tlsClientCert: |
{self._read_file(self.certificate, indent=6)}
    tlsClientKey: |
{self._read_file(self.private_key, indent=6)}
'''
