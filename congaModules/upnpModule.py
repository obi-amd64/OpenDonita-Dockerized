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
import logging

class UPNPAnnouncer(object):
    def __init__(self):
        self._loop = None

        self._device = upnp.Device({
            'deviceType': 'urn:rastersoft-com:device:donita:1',
            'friendlyName': 'OpenDoñita',
            'uuid': 'ca0e5d94-381c-44d4-8a47-8cddbecae0cf',
            'manufacturer': 'Rastersoft',
            'manufacturerURL': 'http://www.rastersoft.com'
        })

        self._service = upnp.Service({
            'serviceType': 'rastersoft-com:service:vacuumcleaner',
            'serviceId': 'rastersoft-com:serviceId:1',
        })
        self._device.addService(self._service)
        logging.info("UPNP Announcer initialized")

    def configure(self, loop):
        self._loop = loop
        self._server = upnp.Annoncer(self._device)
        self._server.initLoop(loop)
        self._server.notify()
        logging.info("UPNP Announcer configured")


upnp_announcer = UPNPAnnouncer()
