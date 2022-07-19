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

import configparser
import json
import os
import traceback

from PIL import Image, ImageDraw
import io
import base64

from .observer import Signal

class RobotManager(object):
    def __init__(self, config_path):
        super().__init__()
        self._robots = {} # contains Robot objects, one per physical robot, identified by the DeviceId
        self._config_path = config_path
        self.new_robot = Signal('new', self)

    def get_robot(self, deviceId):
        if deviceId not in self._robots:
            self._robots[deviceId] = Robot(deviceId, self._config_path)
            self.new_robot.emit(deviceId)
        return self._robots[deviceId]

    def get_robot_list(self):
        l = []
        for a in self._robots:
            l.append(a)
        return l


class Robot(object):
    """ Manages each physical robot """
    def __init__(self, identifier, config_path):

        super().__init__()

        self._persistentData = configparser.ConfigParser()
        self._configFile = os.path.join(config_path, f"data_{identifier}.ini")
        if os.path.exists(self._configFile):
            self._persistentData.read(self._configFile)
        if identifier not in self._persistentData:
            self._persistentData[identifier] = {}

        self._identifier = identifier
        self._connection = None
        self._notecmdValues = {}
        self._notecmdKeys = ['workState','workMode','fan','direction','brush','battery','voice','error','standbyMode',
                             'waterTank','clearComponent','waterMark','version','attract','deviceIp','devicePort',
                             'cleanGoon', 'clearArea','clearTime','clearSign','clearModule','isFinish','chargerPos',
                             'map','track','errorCode','doTime',
                             'appKey','deviceType','authCode','funDefine','nonce_str','version','sign']
        self._modes = ["auto", "gyro", "random", "borders", "area", "x2", "scrub"]
        self._defPersistent('water', '0')
        self._defPersistent('fan', '2')
        self._defPersistent('mode', '0')
        self._defPersistent('battery_guard_enabled', '1')
        self._defPersistent('battery_guard_level', '80')
        self._defPersistent('battery_guard_times', '3')
        self._resetStatus()

    def _defPersistent(self, key, value):
        if key not in self._persistentData[self._identifier]:
            self._persistentData[self._identifier][key] = value

    def connected(self, connection):
        if self._connection is not None:
            print("Closing old robot connection and opening a new one")
            self._connection.closedSignal.disconnect(self.disconnected)
            self._connection.close()
        self._connection = connection
        connection.closedSignal.connect(self.disconnected)
        connection.statusUpdate.connect(self.statusUpdate)

    def _resetStatus(self):
        for key in self._notecmdKeys:
            self._notecmdValues[key] = ''
        self._current_workState = -1
        self._battery_changes_counter = 0

    def disconnected(self, name, connection):
        self._connection = None
        self._resetStatus()

    def get_status(self):
        return json.dumps(self._notecmdValues)

    def _paint_map(self, width, height):
        data = Image.new('RGB', (width, height))
        if ('map' in self._notecmdValues) and (len(self._notecmdValues['map']) != 0):
            mapa = base64.b64decode(self._notecmdValues['map'])
            track = base64.b64decode(self._notecmdValues['track']) [4:]
            charger = self._notecmdValues['chargerPos'].split(',')
            chargerX = int(charger[0])
            chargerY = int(charger[1])

            mapw = mapa[5] * 256 + mapa[6];
            maph = mapa[7] * 256 + mapa[8];
            pixels = []
            pos = 9
            repetitions = 0

            minx = chargerX
            maxx = chargerX
            miny = chargerY
            maxy = chargerY
            index = 0
            errorCharger = False
            if ((chargerX == -1) or (chargerY == -1)):
                errorCharger = True

            while pos < len(mapa):
                if ((mapa[pos] & 0xc0) == 0xc0):
                    repetitions *= 64
                    repetitions += mapa[pos] & 0x3F
                    pos += 1
                    continue
                if (repetitions == 0):
                    repetitions = 1
                value = mapa[pos]
                pos += 1
                for a in range(repetitions):
                    mul = 64
                    for b in range(4):
                        v = (int(value/mul)) & 0x03
                        pixels.append(v)
                        mul /= 4
                        if (v == 0):
                            index += 1
                            continue
                        x = index % mapw
                        y = int(index / mapw)
                        index += 1
                        if (errorCharger):
                            minx = x
                            miny = y
                            maxx = x
                            maxy = y
                            errorCharger = False
                        else:
                            if (x < minx):
                                minx = x
                            if (y < miny):
                                miny = y
                            if (x > maxx):
                                maxx = x
                            if (y > maxy):
                                maxy = y
                repetitions = 0

            ctx = ImageDraw.Draw(data)
            pos = minx + miny * mapw
            ctx.rectangle([(0, 0), (width, height)], fill='#ffffff')
            if (minx <= maxx):
                radius1 = width / (maxx - minx + 1)
                radius2 = height / (maxy - miny + 1)

                if (radius2 < radius1):
                    radius1 = radius2
                radius2 = radius1 / 2
                radius3 = int(radius1 * 0.8); # each point is 20cm wide, and the robot is 32cm wide

                for y in range(miny, maxy+1):
                    for x in range(minx, maxx+1):
                        pos = x + mapw * y
                        if (pixels[pos] == 0):
                            pos += 1
                            continue
                        if pixels[pos] == 1:
                            # Wall
                            fillStyle = '#000000'
                        elif pixels[pos] == 2:
                            # Floor
                            fillStyle = '#ffff00'

                        nx = (x - minx) * radius1
                        ny = (y - miny) * radius1
                        fr1 = nx + radius1
                        fr2 = ny + radius1
                        ctx.rectangle([(nx, ny), (fr1, fr2)], fill=fillStyle)
                        pos += 1
                strokeStyle = '#00ffff';
                # Clean zones
                points = []
                isx = True
                for a in track:
                    if isx:
                        x = int((a - minx) * radius1 + radius2)
                        points.append(x)
                        isx = False
                    else:
                        y = int((a - miny) * radius1 + radius2)
                        points.append(y)
                        isx = True
                        ctx.ellipse([x - radius3, y - radius3, x + radius3, y + radius3], fill=strokeStyle)
                ctx.line(points, fill=strokeStyle, width=radius3*2)

                # robot position
                fillStyle = '#ff00ff'
                strokeStyle = '#000000'
                self._paint_circle(ctx, x, y, radius2, strokeStyle, fillStyle)

                # charger
                if ((chargerX != -1) and (chargerY != -1)):
                    fillStyle = '#00ff00'
                    strokeStyle = '#000000'
                    x = (chargerX - minx) * radius1 + radius2
                    y = (chargerY - miny) * radius1 + radius2
                    self._paint_circle(ctx, x, y, radius2, strokeStyle, fillStyle)

        f = io.BytesIO()
        data.save(f, "PNG")
        return f.getvalue()

    def _paint_circle(self, ctx, x, y, radius, strokeStyle, fillStyle):
        ctx.ellipse([x - radius, y - radius, x + radius, y + radius], fill = strokeStyle)
        radius = int(radius/2)
        ctx.ellipse([x - radius, y - radius, x + radius, y + radius], fill = fillStyle)

    def send_command(self, command, params):
        if self._connection is None:
            return "application/json", 3, '"Not connected"'

        if command == 'setStatus':
            for key in params:
                if key not in self._notecmdKeys:
                    continue
                self._notecmdValues[key] = params[key]
            return "application/json", 0, self.get_status()

        if command == 'getMap':
            try:
                w = int(params['width'])
            except:
                w = 640
            try:
                h = int(params['height'])
            except:
                h = 640
            return "image/png", 0, self._paint_map(w,h)

        if command == 'getStatus':
            return "application/json", 0, self.get_status()

        if command == 'getProperty':
            if 'key' not in params:
                data = {}
                for key in self._persistentData[self._identifier]:
                    data[key] = self._persistentData[self._identifier][key]
                return "application/json", 0, json.dumps(data)
            if params['key'] not in self._persistentData[self._identifier]:
                return "application/json", 8, f'"Key {params["key"]} does not exist in persistent data"'
            return "application/json", 0, json.dumps({params["key"]: self._persistentData[self._identifier][params["key"]]})

        if command == 'setProperty':
            if 'key' not in params:
                return "application/json", 6, '"Missing parameter (key)"'
            if 'value' not in params:
                return "application/json", 6, '"Missing parameter (value)"'
            self._persistentData[self._identifier][params['key']] = str(params['value'])
            with open(self._configFile, 'w') as configfile:
                self._persistentData.write(configfile)
            return "application/json", 0, '"OK"'

        if command == 'setDefaults':
            self._setDefaults()
            return "application/json", 0, '"OK"'

        if command == 'resetBattery':
            self._resetBattery()
            return "application/json", 0, '"OK"'

        return self._connection.send_command(command, params)


    def _setDefaults(self):
        self._connection.send_command('fan', {'speed': self._getPersistentString('fan', 2)})
        self._connection.send_command('watertank', {'speed': self._getPersistentString('water', 0)})
        try:
            fmode = self._modes[self._getPersistentInteger('mode', 0)]
        except:
            fmode = 'auto'
        self._connection.send_command('mode', {'type': fmode})


    def statusUpdate(self, signame, sender, status):
        """ Called whenever the status changes """
        if 'value' not in status:
            return
        value = status['value']

        if ('noteCmd' in value) or ('transitCmd' in value):
            for key in value:
                if key not in self._notecmdKeys:
                    continue
                self._notecmdValues[key] = value[key]

        if ('workState' in value) and ('battery' in value):
            state = value['workState']
            if (state != "5") and (state != "6") and (state != "10"):
                self._battery_changes_counter = 0
            else:
                if (self._current_workState == "6") and ((state == "5") or (state == "10")):
                    # changed from "charged" to "charging"
                    try:
                        if int(value['battery']) <= self._getPersistentInteger('battery_guard_level', 80):
                            self._battery_changes_counter += 1
                            if self._battery_changes_counter >= self._getPersistentInteger('battery_guard_times', 3):
                                if self._getPersistentBoolean('battery_guard_enabled', True):
                                    self._resetBattery()
                    except:
                        pass
            self._current_workState = state

    def _getPersistentString(self, key, default = None):
        if key not in self._persistentData[self._identifier]:
            return default
        else:
            return self._persistentData[self._identifier][key]

    def _getPersistentBoolean(self, key, default_value):
        try:
            return self._persistentData[self._identifier].getboolean(key, default_value)
        except:
            return default_value

    def _getPersistentInteger(self, key, default_value):
        try:
            return self._persistentData[self._identifier].getint(key, default_value)
        except:
            return default_value


    def _resetBattery(self):
        self._battery_changes_counter = 0
        self._connection.send_command('radar', {})
        self._connection.send_command('wait', {'seconds': '1'})
        self._connection.send_command('radar', {})
        self._connection.send_command('wait', {'seconds': '1'})
        self._connection.send_command('fan', {'speed': '0'})
        self._connection.send_command('watertank', {'speed': '0'})
        self._connection.send_command('clean', {})
        self._connection.send_command('waitState', {'state': 'cleaning'})
        self._connection.send_command('wait', {'seconds': '4'})
        self._connection.send_command('stop', {})
        self._connection.send_command('wait', {'seconds': '1'})
        self._connection.send_command('fan', {'speed': self._persistentData[self._identifier]['fan']})
        self._connection.send_command('watertank', {'speed': self._persistentData[self._identifier]['water']})
        self._connection.send_command('waitState', {'state': 'stopped'})
        self._connection.send_command('return', {})
        self._connection.send_command('waitState', {'state': 'home'})
        #self._connection.send_command('closeConnection', {})

    def httpDataUpdate(self, data):
        for key in data:
            if key not in self._notecmdKeys:
                continue
            self._notecmdValues[key] = data[key]


# TODO: add docker support for this (i.e.: write into a volume)
configPath = "/config/congaserver" # os.path.join(os.getenv("HOME"), ".config", "congaserver")
try:
    os.makedirs(configPath)
except:
    pass
robot_manager = RobotManager(configPath)
