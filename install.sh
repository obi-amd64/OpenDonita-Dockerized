#!/bin/bash

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

apt install python3-pip
python3 -m pip install iot-upnp
mkdir -p /opt/congaserver
cp -a congaserver.py /opt/congaserver/
cp -a configconga.py /opt/congaserver/
cp -a congaModules /opt/congaserver/
cp -a html /opt/congaserver/
cp -a congaserver.service /etc/systemd/system/congaserver.service
systemctl enable congaserver.service
systemctl restart congaserver.service
