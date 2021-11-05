#!/bin/bash

if [[ "$1" =~ ^[0-9]+\.[0-9]+ ]]; then
  version=$1
  echo "Selected version: $version"
  shift
else
  version=$(wget -qO- 'https://github.com/grafana/grafana/releases' | grep -v alpha | grep -v beta | grep '/grafana/grafana/releases/tag/' -m 1  | sed -e 's/^.*v\(.*\)">.*/\1/')
  if [ -z "$version" ]; then
    echo "Unable to determine latest grafana version, specify as first command line argument"
    exit 1
  fi
  echo "Latest version: $version"
fi

source /etc/os-release
if [ "${ID}" = "centos" ]; then
  wget https://dl.grafana.com/oss/release/grafana-${version}-1.x86_64.rpm
  sudo yum -y install grafana-${version}-1.x86_64.rpm 
elif [ "${ID}" = "sles" ]; then
  wget https://dl.grafana.com/oss/release/grafana-${version}-1.x86_64.rpm
  sudo rpm -i --nodeps grafana-${version}-1.x86_64.rpm
elif [ "${ID}" = "ubuntu" ]; then
  sudo apt-get install -y adduser libfontconfig1
  wget https://dl.grafana.com/oss/release/grafana_${version}_amd64.deb
  sudo dpkg -i grafana_${version}_amd64.deb
else
  echo "Unknown distribution"
  exit 1
fi

if [ "$1" = "-d" ]; then
  # enable debug by default
  perl -pi -e s'#;level = info#level = debug#g' /etc/grafana/grafana.ini 
fi

disable_ssl_auth_client=0
if [ -e "/etc/cm-release" ]; then
  # As of Bright Computing version 9.x, firewall can be controlled by cmdaemon
  versioninfo=$(cat "/etc/cm-release")
  if [[ "$versioninfo" =~ v([0-9]+)\.([0-9]+) ]]; then
    major=${BASH_REMATCH[1]}
    minor=${BASH_REMATCH[2]}
    if [ "$major" = "9" ]; then
      disable_ssl_auth_client=1
      if [ "$major" = "0" ]; then
        role="login"
      else
        role="firewall"
      fi
    fi
  elif [[ "$versioninfo" =~ 'vmaster' || "$versioninfo" =~ 'vtrunk' || "$versioninfo" =~ 'v1trunk' ]]; then
    disable_ssl_auth_client=1
    role="firewall"
  fi
fi

port=3000
if [ ! -z "$role" ]; then
  cat<<EOF | cmsh
device foreach -t headnode ( \
roles; \
use firewall; \
openports; \
add ACCEPT net 3000 tcp; \
set description grafana; \
commit)
EOF
else
  echo "Make sure to open the local firewall to port $port"
fi

if [ $disable_ssl_auth_client -gt 0 ]; then
  echo "Disable SSL client CA in the cmdaemon HTTP server"
  base_dir=$(dirname "$0")
  $base_dir/cm-manipulate-advanced-config.py -q "AddSSLClientCA=0"
  if [ $? -gt 0 ]; then
    service cmd restart
  fi
fi
