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
import tkinter as tk
import urllib.parse

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        global root
        root.title("Robot WiFi Pairing")
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.ssid_text = tk.Label(self, text = "WiFi SSID:")
        self.ssid_text.pack(side = "top")
        self.ssid = tk.Entry(self)
        self.ssid.pack(side = "top")

        self.password_text = tk.Label(self, text = "WiFi Password:")
        self.password_text.pack(side = "top")
        self.password = tk.Entry(self)
        self.password.pack(side = "top")

        self.dirip_text = tk.Label(self, text = "OpenDoñita Server IP:")
        self.dirip_text.pack(side = "top")
        self.dirip = tk.Entry(self)
        self.dirip.pack(side = "top")

        self.pair = tk.Button(self)
        self.pair["text"] = "Pair Robot"
        self.pair["command"] = self.pair_conga
        self.pair.pack(side="top")

    def pair_conga(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_address = ('192.168.4.1', 80)
        sock.connect(server_address)
        ssid = urllib.parse.quote(self.ssid.get())
        password = urllib.parse.quote(self.password.get())
        ipdata = self.dirip.get()
        if (ipdata == ''):
            ip1 = 'bl-app-eu.robotbona.com'
            ip2 = 'bl-im-eu.robotbona.com'
        else:
            ip1 = urllib.parse.quote(ipdata)
            ip2 = urllib.parse.quote(ipdata)

        message = f'GET /robot/getRobotInfo.do?ssid={ssid}&pwd={password}&jDomain={ip1}&jPort=8082&sDomain={ip2}&sPort=20008&cleanSTime=5 HTTP/1.1\r\nUser-Agent: blapp\r\nAccept: application/json\r\nHost: 192.168.4.1\r\nConnection: Keep-Alive\r\nAccept-Encoding: gzip\r\n\r\n'

        sock.sendall(message.encode('utf8'))

        received = ""
        while True:
            d = sock.recv(1)
            if len(d) == 0:
                break
            received += d.decode('utf8')
        self.ssid.forget()
        self.password.forget()
        self.password_text.forget()
        self.pair.forget()
        self.dirip.forget()
        self.dirip_text.forget()
        if (received.find("200")):
            self.ssid_text["text"] = "Pairing OK"
        else:
            self.ssid_text["text"] = "Pairing failed"

root = tk.Tk()
app = Application(master=root)
app.mainloop()
