#!/bin/sh

mkdir -p /opt/congaserver
cp -a congaserver.py /opt/congaserver/
cp -a configconga.py /opt/congaserver/
cp -a html /opt/congaserver/
cp -a congaserver.service /etc/systemd/system/congaserver.service
systemctl enable congaserver.service
