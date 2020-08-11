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

class Signal(object):
    def __init__(self, name, owner):
        self._owner = owner
        self._name = name
        self._cb = []

    def connect(self, function):
        if function not in self._cb:
            self._cb.append(function)

    def disconnect(self, function):
        if function in self._cb:
            self._cb.remove(function)

    def emit(self, *args):
        for fn in self._cb:
            fn(self._name, self._owner, *args)

