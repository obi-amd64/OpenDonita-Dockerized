#!/usr/bin/env python3

import socket
import sys

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('192.168.4.1', 80)
sock.connect(server_address)

message = b'GET /robot/getRobotInfo.do?ssid=congawifi&pwd=congapass&jDomain=bl-app-eu.robotbona.com&jPort=8082&sDomain=bl-im-eu.robotbona.com&sPort=20008&cleanSTime=5 HTTP/1.1\r\nUser-Agent: blapp\r\nAccept: application/json\r\nHost: 192.168.4.1\r\nConnection: Keep-Alive\r\nAccept-Encoding: gzip\r\n\r\n'

sock.sendall(message)

while True:
    d = sock.recv(1)
    if len(d) == 0:
        break
    print(d.decode('latin1'), end="")


# GET /robot/getRobotInfo.do?ssid=XXXXXXXX&pwd=YYYYYYYY&jDomain=bl-app-eu.robotbona.com&jPort=8082&sDomain=bl-im-eu.robotbona.com&sPort=20008&cleanSTime=5 HTTP/1.1
# User-Agent: blapp
# Accept: application/json
# Host: 192.168.4.1
# Connection: Keep-Alive
# Accept-Encoding: gzip
