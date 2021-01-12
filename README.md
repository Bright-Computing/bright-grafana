# Using Grafana to monitor multiple Bright clusters

## Install

Install Grafana on a dedicated machine (e.g. using install-grafana.sh)
This can be a Bright node or an any other linux machine.

Port 3000 needs to be opened in the firewall for external access to the Grafana website.
For cm-cod-os clusters add `--append-inbound-rule 3000:tcp`.

## Prepare your clusters

Upgrade the cmdaemon (on the head node) to 9.1-2 / 9.0-12 / 8.2-24: build date after 28 November 2020.

## Add clusters to Grafana

Adding new clusters can be done with the provided script, root access to the cluster is required once.

`./bright_grafana.py -u root -p ... -H <ip/hostname> -a`

This script will:
* Add the cluster to the local cache `clusters.json`
* Copy (rsync) the cluster pythoncm version to the local directory
* Create a Grafana profile with the minimal required tokens for running queries
* Create a certificate with the Grafana profile
* Configure a Grafana datasource to the cluster in /etc/grafana/provisioning/datasources
* Copy or update the default dashboards to /var/lib/grafana/dashboards/bright
* Test the configuration by doing a basic query

Note that rsync only needs to be done once per `x.y` version of Bright Cluster Manager.

See `./bright_grafana.py --help` for all options.

## Adding a new custom dashboard

The best way to add a new dashboard is to create it manually in Grafana for one cluster.
Once completed export to JSON and save the result in `/var/lib/grafana/dashboards/bright`
Then run `./bright_grafana.py -b`, to make the dashboard multi-cluster aware.

It is also possible to copy / paste JSON panel snippets directly into existing dashboards.

## Making changed dashboards live

Grafana has a internal loop to watch for changes on disk.
However these these detected changes are not made visible in the web browsers.
Force an update by doing `service grafana-server restart` and a page reload in the browser.

## Entity series supported by cmdaemon

CMDaemon provides these series, which can be used as a selector:
* hostname (all devices)
* node (hostnames for devices of type node)
* category
* wlm
* job_id

To verify the cluster cmdaemon version supports these queries:
```bash
wget --no-check-certificate \
  --certificate=$HOME/.cm/admin.pem \
  --private-key=$HOME/.cm/admin.key \
  "https://master:8081/prometheus/api/v1/series?match[]=hostname" -qO- \
| python -mjson.tool
```

Other series can be added as needed on request.

## Start Grafana

Run `./start.sh` to start Grafana and configure it to be started on the next reboot

## Slurm-state metric

All clusters installed with the version higher than 9.1-2 / 9.0-12 / 8.2-24 will have the slurm-state metric by default.
For upgraded clusters the metrics needs to be configured manually.

For 8.2 the Slurm state metrics are defined for the base partition:
```bash
cat<<EOF | cmsh
monitoring setup
add collection slurm-state
set script /cm/local/apps/cmd/scripts/metrics/slurm_states.py
set consolidator default 
nodeexecutionfilters 
active
exit
executionmultiplexers 
add type Partition
set types Partition 
commit
EOF
```

For 9.0 and up the Slurm state metrics are per defined Slurm WLM cluster
```bash
cat<<EOF | cmsh
monitoring setup
add collection slurm-state
set script /cm/local/apps/cmd/scripts/metrics/slurm_states.py
set consolidator default 
nodeexecutionfilters 
active
exit
executionmultiplexers 
add type SlurmWlmCluster
set types SlurmWlmCluster
commit
EOF
```
