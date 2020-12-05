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
import logging
import asyncio
from .observer import Signal

class BaseServer(object):

    def __init__(self):
        super().__init__()
        self._loop = None
        self._server = None

    def configure(self, loop, port, address = ''):
        self._loop = loop
        coro = asyncio.start_server(self._handle, address, port, loop=loop)
        self._server = loop.run_until_complete(coro)

    def close(self):
        if self._server is not None:
            self._server.close()
            self._loop.run_until_complete(self._server.wait_closed())

    async def _handle(self, reader, writer):
        pass


class BaseConnection(object):
    def __init__(self, reader, writer):
        self._reader = reader
        self._writer = writer
        self._data = b""
        self._closed = False
        self.closedSignal = Signal("closed", self)

    def new_data(self):
        """ Called every time new data is added to self._data
            Overwrite to process arriving data. The function must
            remove from self._data the data already processed
            @return False if there wasn't enough data for a full message; wait for more data
                    True  if a full message was read and it should be called again because
                          there can be another message in the buffer """

        # here just remove the read data
        self._data = b""
        return False

    def close(self):
        """ Called when the socket is closed and the class will be destroyed """
        if not self._closed:
            # do close connection
            self._writer.close()
            self._closed = True
            self.closedSignal.emit()

    async def run(self):
        """ Called whenever there is data to be read in the socket.
            Overwrite only to detect when there are new connections """

        while True:
            try:
                data = await self._reader.read(65536)
            except Exception as e:
                logging.error(f"Read exception {e}")
                self.close()
                break
            if len(data) > 0:
                self._data += data
                while True:
                    if not self.new_data():
                        break
            else:
                # socket closed
                self.close()
                break

