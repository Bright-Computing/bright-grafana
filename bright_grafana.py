#!/usr/bin/env python3

import os
import sys
import json
import time
import subprocess

from config_file import ConfigFile
from cluster_config import ClusterConfig
from dashboard import Dashboard
from options import Options
from rsync import RSync


def main():
    base = os.path.dirname(os.path.realpath(__file__))

    options = Options()
    config_file = ConfigFile(options.config_file)
    if not config_file.load() and options.hostname is None:
        print(f'Config file {options.config_file} not found and no new cluster hostname/IP provided')
        return 1
    elif options.hostname is not None:
        cluster_config = config_file.find(options.hostname)
        if cluster_config is None:
            cluster_config = ClusterConfig(options.hostname, options.port)
            if not cluster_config.get_version():
                print('Failed to determine cluster_config version')
                return 1
            cluster_config.get_build_index()
            print(f'Cluster at {cluster_config.hostname}:{cluster_config.port} is running: {cluster_config.version}, build: {cluster_config.build_index}')
            config_file.clusters.append(cluster_config)
            config_file.save()
    else:
        cluster_config = None

    if options.rsync or options.all:
        if cluster_config is None:
            print('A cluster_config must be provided in order to run rsync')
            return 2
        else:
            if not RSync.run(cluster_config.hostname,
                             options.username,
                             options.password,
                             cluster_config.cluster_pythoncm_directory,
                             cluster_config.pythoncm_directory):
                print('*** Failed to rsync ***')
                return 2
            elif cluster_config.python_version == 2:
                if subprocess.call(['/usr/bin/patch',
                                    '-d',
                                    cluster_config.pythoncm_directory,
                                    '-p9',
                                    '-i',
                                    f'{os.path.dirname(os.path.abspath(__file__))}/py2-to-py3.patch']):
                    print(f'*** Failed to convert {cluster_config.pythoncm_directory} to python3 ***')
                    return 2

    if cluster_config is not None and cluster_config.certificate is None:
        if cluster_config.create_certificate(options.username, options.password):
            config_file.save()
        else:
            return 3

    if cluster_config is None:
        all_cluster_config = config_file.clusters
    else:
        all_cluster_config = [cluster_config]

    if options.datasource or options.all:
        for it in all_cluster_config:
            it.update_datasource(f'{options.provisioning_path}/datasources')

    if options.dashboard or options.all:
        if not os.path.exists(options.dashboard_path):
            os.makedirs(options.dashboard_path)
            write_dashboard_yaml(f'{options.provisioning_path}/dashboards/bright.yaml', options.dashboard_path)
        datasources = [it.name for it in config_file.clusters]
        for dirpath, dirnames, filenames in os.walk(options.dashboard_path):
            for filename in [it for it in filenames if it.endswith('.json')]:
                dashboard = Dashboard(f'{dirpath}/{filename}')
                version = dashboard.update_datasources(datasources)
                if version is not None:
                    dashboard.save()
                    print(f'*** Updated dashboard {dirpath}/{filename} with {len(datasources)} datasources, version {version} ***')
        for dirpath, dirnames, filenames in os.walk(f'{base}/dashboards'):
            for filename in [it for it in filenames if it.endswith('.json')]:
                target = f'{options.dashboard_path}/{filename}'
                if not os.path.exists(target):
                    dashboard = Dashboard(f'{dirpath}/{filename}')
                    if dashboard.update_datasources(datasources):
                        dashboard.save(target)
                        print(f'*** Added dashboard {target} with {len(datasources)} datasources ***')

    if options.test or options.all:
        query = f'api/v1/query?query=forks&time={int(time.time())}'
        for it in all_cluster_config:
            print(f'*** {it.name} ***')
            cluster = it.get_cluster()
            data = json.loads(cluster.monitoring.prometheus.raw_query(query))
            print(json.dumps(data, indent=2))
            cluster.disconnect()
            cluster

    return 0


def write_dashboard_yaml(filename, dashboard_path):
    with open(filename, 'w') as fd:
        fd.write(f'''
apiVersion: 1

providers:
  - name: 'Bright'
    folder: ''
    type: file
    disableDeletion: false
    editable: false
    updateIntervalSeconds: 60
    options:
      path: {dashboard_path}
''')


if __name__ == '__main__':
    if (sys.version_info.major, sys.version_info.minor) >= (3, 7):
        try:
            sys.exit(main())
        except Exception as e:
            print(f'*** Error: {e}, is the cluster reachable and running a version from after 20 November 2020? ***')
            sys.exit(9)
    else:
        print('Python 3.7 or higher is required')
        sys.exit(37)
