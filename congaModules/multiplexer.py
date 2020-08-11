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

import datetime
import select
import sys
import traceback
import signal

from congaModules.observer import Signal

class Multiplexer(object):
    def __init__(self):
        super().__init__()

        self._socklist = []
        signal.signal(signal.SIGINT, self._close_and_exit)
        self.timer = Signal("timer", self)
        self._before = datetime.datetime.now().timestamp()
        self._interval = 0.5

    def add_socket(self, socket_class):
        if socket_class not in self._socklist:
            socket_class.added()
            self._socklist.append(socket_class)
            socket_class.closedSignal.connect(self._remove_socket)

    def _remove_socket(self, name, socket_class):
        if socket_class in self._socklist:
            print("Removing")
            self._socklist.remove(socket_class)
            socket_class.closedSignal.disconnect(self._remove_socket)

    def run(self):
        self._second = datetime.datetime.now().time().second
        while True:
            readable, writable, exceptions = select.select(self._socklist[:], [], [], self._interval)
            for has_data in readable:
                try:
                    retval = has_data.data_available()
                except:
                    traceback.print_exc()
                    has_data.close()
                if retval is not None:
                    self.add_socket(retval)
            now = datetime.datetime.now().timestamp()
            if now >= (self._before + self._interval):
                self._before = now
                self.timer.emit(now)

    def _close_and_exit(self, sig, frame):
        print("Exiting gracefully")
        for s in self._socklist[:]:
            s.close()
        sys.exit(0)

multiplexer = Multiplexer()
