#!/usr/bin/env python3

# Copyright 2020 (C) Raster Software Vigo (Sergio Costas)
#
# This file is part of OpenDoñita
#
# OpenDoñita is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# OpenDoñita is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import socket
import sys
import urllib.parse

length = len(sys.argv)

if (length != 4):
    print("Usage: configconga.py WIFI_SSID WIFI_PASSWORD OPENDOÑITA_SERVER_IP_ADDRESS")
    sys.exit(1)

ssid = urllib.parse.quote(sys.argv[1])
pwd =  urllib.parse.quote(sys.argv[2])
domain = urllib.parse.quote(sys.argv[3])

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('192.168.4.1', 80)
sock.connect(server_address)

message = f'GET /robot/getRobotInfo.do?ssid={ssid}&pwd={pwd}&jDomain={domain}&jPort=8082&sDomain={domain}&sPort=20008&cleanSTime=5 HTTP/1.1\r\nUser-Agent: blapp\r\nAccept: application/json\r\nHost: 192.168.4.1\r\nConnection: Keep-Alive\r\nAccept-Encoding: gzip\r\n\r\n'

sock.sendall(message.encode('utf8'))

while True:
    d = sock.recv(1)
    if len(d) == 0:
        break
    print(d.decode('utf8'), end="")


# GET /robot/getRobotInfo.do?ssid=XXXXXXXX&pwd=YYYYYYYY&jDomain=bl-app-eu.robotbona.com&jPort=8082&sDomain=bl-im-eu.robotbona.com&sPort=20008&cleanSTime=5 HTTP/1.1
# User-Agent: blapp
# Accept: application/json
# Host: 192.168.4.1
# Connection: Keep-Alive
# Accept-Encoding: gzip
