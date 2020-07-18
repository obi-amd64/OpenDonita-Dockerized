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
import select
import sys
import datetime
from urllib.parse import parse_qs
import json
import struct
import random
import traceback
import signal
import os
import configparser

configPath = os.path.join(os.getenv("HOME"), ".config", "congaserver")
try:
    os.makedirs(configPath)
except:
    pass

robot_data = {}
html_path = "html"

# Errors:
#
# 0: No error
# 1: Missing robot ID
# 2: Invalid robot ID
# 3: Robot is not connected to the server
# 4: Robot still not identified in server
# 5: Unknown command
# 6: Missing parameter
# 7: Invalid value (out of range, or similar)
# 8: Key doesn't exist in persistent data

def robot_clear_time(server_object):
    server_object.convert_data()
    send_robot_header(server_object)
    server_object.send_chunked('{"msg":"ok","result":"0","version":"1.0.0"}')
    server_object.close()


def robot_get_token(server_object):
    server_object.convert_data()

    data = server_object.get_data()
    robot_data['appKey'] = data['appKey']
    robot_data['deviceId'] = data['deviceId']
    robot_data['deviceType'] = data['deviceType']
    robot_data['authCode'] = data['authCode']
    robot_data['funDefine'] = data['funDefine']
    robot_data['nonce'] = data['nonce_str']

    send_robot_header(server_object)
    token = ''
    for a in range(32):
        v = random.randint(0,9)
        token += chr(48 + v)
    data = '{"msg":"ok","result":"0","data":{"appKey":"'+robot_data['appKey']+'","deviceNo":"'+robot_data['deviceId']+'","token":"'
    data += token
    data += '"},"version":"1.0.0"}'
    server_object.send_chunked(data)
    server_object.close()


def robot_global(server_object):
    server_object.send_chunked('{"msg":"ok","result":"0","version":"1.0.0"}')
    server_object.close()


def send_robot_header(server_object):
    server_object.protocol = 'HTTP/1.1'
    server_object.add_header('Content-Type', 'application/json;charset=UTF-8')
    server_object.add_header('Transfer-Encoding', 'chunked')
    server_object.add_header('Connection', 'close')
    server_object.add_header('Set-Cookie', 'SERVERID=2423aa26fbdf3112bc4aa0453e825ac8|1592686775|1592686775;Path=/')


def robot_action(server_object):
    robots = robotManager.get_robot_list()
    uri = server_object.get_path()
    error = None
    if uri.startswith('/robot/'):
        action = uri[7:]
        pos = action.find('/')
        if pos == -1:
            server_object.add_header("Content-Type", "application/json")
            server_object.send_answer('{"error":1, "value":"Missing robot ID"}', 400, "MISSING_ROBOT_ID")
            server_object.close()
            return
        robotId = action[:pos]
        action = action[pos+1:]
        if robotId == "all":
            for robot_id in robots:
                robot = robotManager.get_robot(robot_id)
                error, answer = robot.send_command(action, server_object.get_params())
        else:
            if robotId in robots:
                robot = robotManager.get_robot(robotId)
                error, answer = robot.send_command(action, server_object.get_params())
            else:
                server_object.add_header("Content-Type", "application/json")
                server_object.send_answer('{"error":2, "value":"Invalid robot ID"}', 400, "INVALID_ROBOT_ID")
                server_object.close()
                return
    if (error is None) or (answer is None):
        answer = '{}'
        error = 0
    server_object.add_header("Content-Type", "application/json")
    server_object.send_answer('{"error":' + str(error) + ', "value":'+answer+'}', 200, "")
    server_object.close()


def robot_list(server_object):
    robots = robotManager.get_robot_list()
    data = []
    for robot_id in robots:
        data.append(robot_id)
    server_object.send_answer_json_close(data)


def html_server(server_object):
    global html_path

    path = server_object.get_path()
    while (path != '') and ((path[0] == '/') or (path[0] == '.')):
        path = path[1:]
    if path == "":
        path = "index.html"
    path = os.path.join(html_path, path)
    print(f"Reading file {path}")
    if os.path.exists(path):
        try:
            with open(path, "r") as page:
                data = page.read()
            if path.endswith(".js"):
                mimetype = "application/javascript"
            elif path.endswith(".html"):
                mimetype = "text/html"
            elif path.endswith(".svg"):
                mimetype = "image/svg+xml"
            elif path.endswith(".css"):
                mimetype = "text/css"
            else:
                mimetype = None
            if mimetype is not None:
                server_object.add_header("Content-Type", mimetype)
            server_object.send_answer(data, 200, "OK")
        except:
            print("Error 401")
            server_object.send_answer('<html><head></head><body><h1>401 Error while reading the file</h1><p>There was an erro while trying to read that file</p></body></html>', 401, "Error reading file")
    else:
        print("Error 404")
        server_object.send_answer('<html><head></head><body><h1>404 File not found</h1></body></html>', 404, "File not found")
    server_object.close()

registered_pages = {
    '/baole-web/common/sumbitClearTime.do': robot_clear_time,
    '/baole-web/common/getToken.do': robot_get_token,
    '/baole-web/common/*': robot_global,
    '/robot/list': robot_list,
    '/robot/*': robot_action,
    '/*': html_server
}


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


class RobotManager(object):
    def __init__(self):
        self._robots = {} # contains Robot objects, one per physical robot, identified by the DeviceId

    def get_robot(self, deviceId):
        if deviceId not in self._robots:
            self._robots[deviceId] = Robot(deviceId)
        return self._robots[deviceId]

    def get_robot_list(self):
        l = []
        for a in self._robots:
            l.append(a)
        return l

robotManager = RobotManager()

class BaseServer(object):
    def __init__(self, sock = None):
        if sock is None:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self._sock = sock
        print(f"Socket: {self.fileno()}")
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self._data = b""
        self._closed = False
        self.closedSignal = Signal("closed", self)

    def fileno(self):
        return self._sock.fileno()

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
            print(f"Closing socket {self.fileno()}")
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self._sock.close()
            except:
                pass
            self._closed = True
            self.closedSignal.emit()

    def data_available(self):
        """ Called whenever there is data to be read in the socket.
            Overwrite only to detect when there are new connections """
        try:
            data = self._sock.recv(65536)
        except Error as e:
            self.close()
            print(f"Connection lost {self.fileno()}")
            print(e)
            return
        if len(data) > 0:
            self._data += data
            while True:
                if not self.new_data():
                    break
        else:
            # socket closed
            self.close()


class HTTPConnection(BaseServer):
    """ Manages an specific connection to the HTTP server """

    def __init__(self, sock, address):
        super().__init__(sock)
        print("New http connection")
        self._address = address
        self.headers = None
        self.protocol = 'HTTP/1.0'
        self._headers_answer = b""
        self._return_error = 200
        self._return_error_text = ""
        self._answer_sent = False

    def new_data(self):
        if self.headers is None:
            pos = self._data.find(b"\r\n\r\n")
            if pos == -1:
                return False
            header = self._data[:pos].split(b"\r\n")
            self._data = self._data[pos+4:]
            self.headers = {}
            http_line = header[0].decode('utf8').split(" ")
            self._command = http_line[0]
            self._URI = http_line[1]
            if (len(self._URI) == 0) or (self._URI[0] != '/'):
                self._URI = '/' + self._URI
            self._protocol = http_line[2]
            for entry in header[1:]:
                pos = entry.find(b":")
                if pos != -1:
                    self.headers[entry[:pos].decode('utf8').strip()] = entry[pos+1:].decode('utf8').strip()
        if 'Content-Length' in self.headers:
            if len(self._data) < int(self.headers['Content-Length']):
                return False
        self._process_data()
        return False

    def _process_data(self):
        global registered_pages

        length = 0
        jump = None
        path = self.get_path()
        for page in registered_pages:
            if page[-1] == '*':
                if path.startswith(page[:-1]):
                    if length < len(page):
                        jump = page
                        length = len(page)
                continue
            if path == page:
                print(f'{self._URI}')
                print(f'{self._data}')
                registered_pages[page](self)
                return
        if jump is not None:
            print(f'{self._URI}')
            print(f'{self._data}')
            registered_pages[jump](self)
            return
        self.send_answer("", 404, "NOT FOUND")
        self.close()

    def add_header(self, name, value):
        self._headers_answer += (f'{name}: {value}\r\n').encode('utf8')

    def send_answer_json_close(self, data):
        result = '{"error":0, "value": '+json.dumps(data)+'}'
        server_object.add_header("Content-Type", "application/json")
        self.send_answer(result.encode('utf8'), 200, 'OK')
        self.close()

    def send_answer(self, data, error = 200, text = ''):
        if isinstance(data, str):
            data = data.encode('utf8')
        if not self._answer_sent:
            cmd = (f'{self.protocol} {error} {text}\r\n').encode('utf8')
            cmd += self._headers_answer
            cmd += b'\r\n'
            cmd += data
        else:
            cmd = data
        self._answer_sent = True
        self._sock.send(cmd)

    def get_data(self):
        return self._data

    def get_uri(self):
        return self._URI

    def get_path(self):
        pos = self._URI.find("?")
        if pos == -1:
            return self._URI
        else:
            return self._URI[:pos]

    def get_params(self):
        pos = self._URI.find("?")
        if pos == -1:
            return {}
        else:
            tmpdata = parse_qs(self._URI[pos+1:])
            data = {}
            for element in tmpdata:
                data[element] = tmpdata[element][0]
            return data

    def convert_data(self):
        if ('Content-Type' in self.headers):
            if self.headers['Content-Type'] == 'application/x-www-form-urlencoded':
                tmpdata = parse_qs(self._data.decode('utf8'))
                data = {}
                for element in tmpdata:
                    data[element] = tmpdata[element][0]
                self._data = data
            elif self.headers['Content-Type'].startswith('application/json'):
                self._data = json.loads(self._data)

    def send_chunked(self, text):
        chunk = f'{hex(len(text))[2:]}\r\n{text}\r\n'
        self.send_answer(chunk)
        self.send_answer('0\r\n\r\n')


class HTTPServer(BaseServer):
    def __init__(self, port = 80):
        super().__init__()
        self._sock.bind(('', port))
        self._sock.listen(10)

    def data_available(self):
        # there is a new connection
        newsock, address = self._sock.accept()
        return HTTPConnection(newsock, address)


class RobotServer(BaseServer):
    def __init__(self, port = 20008):
        super().__init__()
        self._sock.bind(('', port))
        self._sock.listen(10)

    def data_available(self):
        # there is a new connection
        print("Robot connected")
        newsock, address = self._sock.accept()
        return RobotConnection(newsock, address)


class RobotConnection(BaseServer):
    def __init__(self, sock, address):
        global multiplexer

        super().__init__(sock)
        print("New robot connection")
        self._address = address
        self._identified = False
        self._packet_queue = []
        self._packet_id = 1
        self._token = None
        self._deviceId = None
        self._appKey = None
        self._authCode = None
        self._deviceIP = None
        self._devicePort = None
        self._waiting_for_command = None
        multiplexer.timer.connect(self.timeout)
        self.statusUpdate = Signal("status", self)

    def timeout(self, signame, caller, now):
        self._next_command()

    def _next_command(self):
        if self._waiting_for_command is not None:
            return
        if len(self._packet_queue) == 0:
            return
        command, params = self._packet_queue.pop(0)
        self.send_command(command, params)


    def send_command(self, command, params):
        if not self._identified:
            return 4, "Not identified"

        wait_for_ack = True
        extraCommand = None
        extraCommand2 = None

        if command == 'clean':
            ncommand = '100'
        elif command == 'stop':
            ncommand = '102'
        elif command == 'return':
            ncommand = '104'
        elif command == 'updateMap':
            ncommand = '131'
        elif command == 'sound':
            if "status" not in params:
                return 6, "Missing parameter (status)"
            if params['status'] == '0':
                ncommand = '125'
            elif params['status'] == '1':
                ncommand = '123'
            else:
                return 7, "Invalid value (valid values are 0 and 1)"
        elif command == 'fan':
            ncommand = '110'
            if 'speed' not in params:
                return 6, "Missing parameter (speed)"
            if params['speed'] == '0':
                extraCommand = '"fan":"1"' # OFF
            elif params['speed'] == '1':
                extraCommand = '"fan":"4"' # ECO
            elif params['speed'] == '2':
                extraCommand = '"fan":"2"' # NORMAL
            elif params['speed'] == '3':
                extraCommand = '"fan":"3"' # TURBO
            else:
                return 7, "Invalid value (valid values are 0, 1, 2 and 3)"
        elif command == 'watertank':
            ncommand = '145'
            if 'speed' not in params:
                return 6, "Missing parameter (speed)"
            if params['speed'] == '0':
                extraCommand2 = '"waterTank":"255"' # OFF
            elif params['speed'] == '1':
                extraCommand2 = '"waterTank":"60"' # SMALL
            elif params['speed'] == '2':
                extraCommand2 = '"waterTank":"40"' # NORMAL
            elif params['speed'] == '3':
                extraCommand2 = '"waterTank":"20"' # FAST
            else:
                return 7, "Invalid value (valid values are 0, 1, 2 and 3)"
        elif command == 'mode':
            ncommand = '106'
            if 'type' not in params:
                return 6, "Missing parameter (type)"
            if params['type'] == 'auto':
                extraCommand = '"mode":"11"'
            elif params['type'] == 'gyro':
                extraCommand = '"mode":"1"'
            elif params['type'] == 'random':
                extraCommand = '"mode":"3"'
            elif params['type'] == 'borders':
                extraCommand = '"mode":"4"'
            elif params['type'] == 'area':
                extraCommand = '"mode":"6"'
            elif params['type'] == 'x2':
                extraCommand = '"mode":"8"'
            elif params['type'] == 'scrub':
                extraCommand = '"mode":"10"'
            else:
                return 7, "Invalid value (valid values are 'auto','giro','random','borders','area','x2','scrub')"
        elif command == 'notifyConnection': # seems to be sent whenever the tablet connects to the server
            ncommand = '400'
            wait_for_ack = False
        elif command == 'askStatus': # seems to ask the robot to send a Status packet
            ncommand = '98'
            wait_for_ack = False
        else:
            return 5, "Unknown command"

        if self._waiting_for_command is not None:
            print("waiting for command")
            self._packet_queue.append((command, params))
            return 0, "{}"

        self._packet_id += 1
        if wait_for_ack:
            self._waiting_for_command = self._packet_id
        data = '{"cmd":0,"control":{"authCode":"'
        data += self._authCode
        data += '","deviceIp":"'
        data += self._deviceIP
        data += '","devicePort":"'
        data += self._devicePort
        data += '","targetId":"1","targetType":"3"},"seq":0,"value":{'
        if extraCommand is not None:
            data += extraCommand+','
        data += '"transitCmd":"'
        data += ncommand
        data += '"'
        if extraCommand2 is not None:
            data += ','+extraCommand2
        data += '}}\n'
        print(f"Sending command {data}")
        self._send_packet(0x00c800fa, 0x01090000, self._packet_id, 0x00, data)
        if not wait_for_ack:
            self._next_command()
        return 0, "{}"


    def close(self):
        print("Robot disconnected")
        multiplexer.timer.disconnect(self.timeout)
        super().close()
        self._identified = False


    def new_data(self):
        global robotManager

        if len(self._data) < 20:
            return False
        header = struct.unpack("<LLLLL", self._data[0:20])
        if len(self._data) < header[0]:
            return False
        payload = self._data[20:header[0]]
        self._data = self._data[header[0]:]

        # process the packet
        # PING
        if self._check_header(header, 0x14, 0x00c80100, 0x01,0x03e7):
            print("Pong")
            self._send_packet(0x00c80111, 0x01080001, header[3], 0x03e7)
            return True
        # Identification
        if self._check_header(header, None, 0x0010, 0x0001, 0x00):
            print("Identification")
            payload = json.loads(payload)
            self._token = payload['value']['token']
            self._deviceId = payload['value']['deviceId']
            self._appKey = payload['value']['appKey']
            self._authCode = payload['value']['authCode']
            self._deviceIP = payload['value']['deviceIp']
            self._devicePort = payload['value']['devicePort']
            robotManager.get_robot(self._deviceId).connected(self)
            self._identified = True
            now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            self._send_packet(0x00c80011, 0x01, header[3], 0x00, '{"msg":"login succeed","result":0,"version":"1.0","time":"'+now+'"}')
            return True
        # Status
        if self._check_header(header, None, 0x0018, 0x0001, 0x00):
            print("Status")
            self._send_packet(0x00c80019, 0x01, header[3], 0x01, '{"msg":"OK","result":0,"version":"1.0"}\n')
            self._send_payload(payload)
            return True
        # ACK
        if self._check_header(header, None, 0x000000fa, 0x0001, 0x00):
            if self._waiting_for_command is not None:
                if header[3] == self._waiting_for_command:
                    self._send_payload(payload)
                    self._waiting_for_command = None
                    print("ACK fine")
                    self._next_command()
                else:
                    print("ACK error")
            return True
        # Map
        if self._check_header(header, None, 0x0014, 0x0001, 0x00):
            print("Map")
            self._send_payload(payload)
            return True
        # Error
        if self._check_header(header, None, 0x0016, 0x0001, 0x00):
            print("Error")
            self._send_packet(0x00c80019, 0x01, header[3], 0x01, '{"msg":"OK","result":0,"version":"1.0"}\n')
            return True
        print("Unknown packet")
        print(header)
        print(payload)
        return True


    def _send_payload(self, payload):
        if len(payload) == 0:
            return
        try:
            jsonPayload = json.loads(payload)
        except:
            print(f'Payload is not a JSON file: "{payload}"')
            return
        self.statusUpdate.emit(jsonPayload)

    def _check_header(self, header, value0, value1, value2, value4):
        if (value0 is not None) and (value0 != header[0]):
            return False
        if (value1 is not None) and (value1 != header[1]):
            return False
        if (value2 is not None) and (value2 != header[2]):
            return False
        if (value4 is not None) and (value4 != header[4]):
            return False
        return True

    def _send_packet(self, value1, value2, packet_id, value3, data = b""):
        if isinstance(data, str):
            data = data.encode('utf8')
        header = bytearray(struct.pack("<LLLLL", 20 + len(data), value1, value2, packet_id, value3))
        self._sock.send(header + data)
        # data2 = struct.unpack("BBBBBBBBBBBBBBBBBBBB", header)
        # c = 0
        # for n in data2:
        #     d = hex(n)[2:]
        #     if n < 16:
        #         d = "0"+d
        #     print(d + " ", end="")
        #     c += 1
        #     if (c%4 == 0) and (c < 20):
        #         print("| ", end="")
        # print()
        # if len(data) > 0:
        #     print("    '"+ data.decode('utf8').replace('\n','\\n\n    ').replace('\r','\\r') + "'")
        # print()



class Robot(object):
    """ Manages each physical robot """
    def __init__(self, identifier):
        global configPath

        super().__init__()

        self._persistentData = configparser.ConfigParser()
        self._configFile = os.path.join(configPath, f"data_{identifier}.ini")
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
                             'map','track','errorCode','doTime']
        self._resetStatus()

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

    def disconnected(self, name, connection):
        self._connection = None
        self._resetStatus()

    def get_status(self):
        return json.dumps(self._notecmdValues)

    def send_command(self, command, params):
        if self._connection is None:
            return 3, '"Not connected"'

        if command == 'setStatus':
            for key in params:
                if key not in self._notecmdKeys:
                    continue
                self._notecmdValues[key] = params[key]
            return 0, self.get_status()

        if command == 'getStatus':
            return 0, self.get_status()

        if command == 'getProperty':
            if 'key' not in params:
                return 6, '"Missing parameter (key)"'
            if params['key'] not in self._persistentData[self._identifier]:
                return 8, f'"Key {params["key"]} does not exist in persistent data"'
            return 0, json.dumps({params["key"]: self._persistentData[self._identifier][params["key"]]})

        if command == 'setProperty':
            if 'key' not in params:
                return 6, '"Missing parameter (key)"'
            if 'value' not in params:
                return 6, '"Missing parameter (value)"'
            self._persistentData[self._identifier][params['key']] = str(params['value'])
            with open(self._configFile, 'w') as configfile:
                self._persistentData.write(configfile)
            return 0, '"OK"'

        return self._connection.send_command(command, params)


    def statusUpdate(self, signame, sender, status):
        if 'value' not in status:
            return
        value = status['value']
        if ('noteCmd' in value) or ('transitCmd' in value):
            for key in value:
                if key not in self._notecmdKeys:
                    continue
                self._notecmdValues[key] = value[key]


class Multiplexer(object):
    def __init__(self, port_http = 80, port_bona = 20008):
        self._socklist = []
        self._http_server = HTTPServer(port_http)
        self._add_socket(self._http_server)
        self._robot_server = RobotServer(port_bona)
        self._add_socket(self._robot_server)
        signal.signal(signal.SIGINT, self._close_and_exit)
        self.timer = Signal("timer", self)
        self._before = datetime.datetime.now().timestamp()
        self._interval = 0.5

    def _add_socket(self, socket_class):
        if socket_class not in self._socklist:
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
                    self._add_socket(retval)
            now = datetime.datetime.now().timestamp()
            if now >= (self._before + self._interval):
                self._before = now
                self.timer.emit(now)

    def _close_and_exit(self, sig, frame):
        print("Exiting gracefully")
        for s in self._socklist[:]:
            s.close()
        sys.exit(0)


if len(sys.argv) > 2:
    port_http = int(sys.argv[1])
    port_bona = int(sys.argv[2])
else:
    port_http = 80
    port_bona = 20008
multiplexer = Multiplexer(port_http, port_bona)
multiplexer.run()
