import sys
import getpass

from argparse import ArgumentParser


class Options:
    def __init__(self, argv=None):
        parser = ArgumentParser()
        parser.add_argument('-f',
                            '--configfile',
                            dest='config_file',
                            type=str,
                            action='store',
                            default='clusters.json',
                            help='The configuration file containg existing clusters')
        parser.add_argument('-H',
                            '--host',
                            dest='hostname',
                            type=str,
                            action='store',
                            default=None,
                            help='The shared hostname/IP between both HA head nodes or the hostname/IP of the active head node')
        parser.add_argument('--port',
                            dest='port',
                            type=int,
                            action='store',
                            default=8081,
                            help='The HTTPs port of the cmdaemon')
        parser.add_argument('-u',
                            '--username',
                            dest='username',
                            type=str,
                            action='store',
                            default=getpass.getuser(),
                            help='Username to use to connect with using ssh and pythoncm')
        parser.add_argument('-p',
                            '--password',
                            dest='passwd',
                            type=str,
                            action='store',
                            default=None,
                            help='Password to use to connect with using ssh and pythoncm, "-" for stdin, skip this option for password less ssh')
        parser.add_argument('--rsync',
                            dest='rsync',
                            action='store_true',
                            default=False,
                            help='Rsync pythoncm to the local directory')
        parser.add_argument('-d',
                            '--datasource',
                            dest='datasource',
                            action='store_true',
                            default=False,
                            help='Update datasource YAML')
        parser.add_argument('-b',
                            '--dashboard',
                            dest='dashboard',
                            action='store_true',
                            default=False,
                            help='Update dashboard JSON with all datasources')
        parser.add_argument('--provisioning-path',
                            dest='provisioning_path',
                            action='store',
                            default='/etc/grafana/provisioning',
                            help='Path of the datasource and dashboards YAML files')
        parser.add_argument('--dashboard-path',
                            dest='dashboard_path',
                            action='store',
                            default='/var/lib/grafana/dashboards/bright',
                            help='Path of the dashboard JSON files')
        parser.add_argument('-t',
                            '--test',
                            dest='test',
                            action='store_true',
                            default=False,
                            help='Test a grafana plot')
        parser.add_argument('-a',
                            '--all',
                            dest='all',
                            action='store_true',
                            default=False,
                            help='Do all for a new cluster: --rsync --datasource --dashboard --test')

        options = parser.parse_args(argv if argv is not None else sys.argv[1:])
        for arg in vars(options):
            setattr(self, arg, getattr(options, arg))

    @property
    def password(self):
        if self.passwd == '-':
            self.passwd = getpass.getpass(f'cluster password for {self.username}: ')
        return self.passwd
