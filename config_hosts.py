#!/usr/bin/env python3

import netifaces
import os

def configure_server(use_internal):
    hosts = []
    with open('/etc/hosts', 'r') as hostfile:
        for line in hostfile.readlines():
            line = line.strip()
            if line.find("robotbona.com") == -1:
                hosts.append(line)
    with open('/etc/hosts', 'w') as hostfile:
        for line in hosts:
            hostfile.write(line + '\n')
        if use_internal:
            ip = None
            try:
                ip = netifaces.ifaddresses('wlan0')[netifaces.AF_INET][0]['addr']
            except:
                pass
            if ip is None:
                try:
                    ip = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
                except:
                    pass
            if ip is not None:
                hostfile.write(f'{ip} bl-app-eu.robotbona.com\n')
                hostfile.write(f'{ip} bl-im-eu.robotbona.com\n')
    os.system("systemctl restart dnsmasq.service")

configure_server(True)
