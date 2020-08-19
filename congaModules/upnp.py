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

import upnp
import asyncio
from congaModules.robotManager import robot_manager

class UPNPAnnouncer(object):
    def __init__(self):
        self._loop = None
        #robot_manager.new_robot.connect(self._robot_detected)
        self._device = upnp.Device({
            'deviceType': 'urn:sadmin-fr:device:demo:1',
            'friendlyName': 'UPnP Test',
            'uuid': '00a56575-78fa-40fe-b107-8f4b5043a2b0',
            'manufacturer': 'BONNET',
            'manufacturerURL': 'http://sadmin.fr'
        })
        self._service = upnp.Service({
            'serviceType': 'sadmin-fr:service:dummy',
            'serviceId': 'sadmin-fr:serviceId:1',
        })
        self._device.addService(self._service)

    def configure(self, loop):
        self._loop = loop
        self._server = upnp.Annoncer(self._device)
        self._server.initLoop(loop)
        loop.create_task(self._send_announces())


    async def _send_announces(self):
        while True:
            print("Notify upnp")
            self._server.notify()
            await asyncio.sleep(2)


    # def _robot_detected(self, deviceId):
    #     service = upnp.Service({
    #         'serviceType': 'sadmin-fr:service:dummy',
    #         'serviceId': 'sadmin-fr:serviceId:1',
    #     })


upnp_announcer = UPNPAnnouncer()
