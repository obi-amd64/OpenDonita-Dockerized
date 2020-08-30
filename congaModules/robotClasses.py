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

import logging
import datetime
import json
import struct
import asyncio
import types
import traceback
import time

from .robotManager import robot_manager
from .baseServer import BaseServer, BaseConnection
from .observer import Signal

class RobotServer(BaseServer):

    async def _handle(self, reader, writer):
        connection = RobotConnection(self._loop, reader, writer)
        await connection.run()

class RobotConnection(BaseConnection):
    def __init__(self, loop, reader, writer):
        super().__init__(reader, writer)
        logging.info("Connected a new robot")
        self._loop = loop
        self._identified = False
        self._packet_queue = asyncio.Queue()
        self._wait_for_ack = asyncio.Event()
        self._wait_for_status = asyncio.Event()
        self._packet_id = 1
        self._token = None
        self._deviceId = None
        self._appKey = None
        self._authCode = None
        self._deviceIP = None
        self._devicePort = None
        self._end_tasks = False
        self._waiting_for_command = None
        self.statusUpdate = Signal("status", self)
        self._state = 0
        self._loop.create_task(self.execute_commands())
        self._loop.create_task(self.manual_loop())
        self._current_direction = 0
        self._desired_direction = 0
        self._manual_time = time.time()
        self._manual_event = asyncio.Event()


    async def manual_loop(self):
        """ Manages the manual control of the robot """

        params = types.SimpleNamespace()
        params.command = "108"
        params.suffix_commands = None
        params.wait_for_ack = True

        while not self._end_tasks:
            try:
                self._manual_event.clear()
                if self._current_direction == 0:
                    await self._manual_event.wait()
                else:
                    try:
                        await asyncio.wait_for(self._manual_event.wait(), 2.2)
                    except asyncio.TimeoutError:
                        # after 2.2 seconds without receiving calls, stop the robot
                        if self._current_direction != 0:
                            params.prefix_commands = f'"direction":"5","tag":"{self._current_direction}"'
                            self._current_direction = 0
                            self._desired_direction = 0
                            await self._send_packet(params)
                        continue
                if self._end_tasks:
                    break
                if (self._current_direction != 0) and (self._desired_direction != self._current_direction):
                    # changing direction, so first stop the robot
                    params.prefix_commands = f'"direction":"5","tag":"{self._current_direction}"'
                    self._current_direction = 0
                    await self._send_packet(params)
                self._current_direction = self._desired_direction
                if self._current_direction != 0:
                    params.prefix_commands = f'"direction":"{self._current_direction}"'
                    await self._send_packet(params)
            except:
                traceback.print_exc()


    async def execute_commands(self):
        while not self._end_tasks:
            parameters = await self._packet_queue.get()
            if parameters is None:
                self._packet_queue.task_done()
                break

            if parameters.command == 'waitState':
                while (parameters.state != self._state) and ((parameters.state != 'home') or ((self._state != '5') and (self._state != '6'))):
                    print(f"Waiting for state {parameters.state}")
                    self._wait_for_status.clear()
                    await self._wait_for_status.wait()

            elif parameters.command == 'wait':
                print(f"Waiting {parameters.seconds} seconds")
                await asyncio.sleep(parameters.seconds)

            elif parameters.command == 'manual':
                self._desired_direction = parameters.direction
                self._manual_event.set()

            else: # rest of commands
                await self._send_packet(parameters)

            self._packet_queue.task_done()


    async def _send_packet(self, parameters):
        while self._wait_for_ack.is_set():
            await self._wait_for_ack.wait()
        if self._end_tasks:
            return
        self._packet_id += 1
        data = '{"cmd":0,"control":{"authCode":"'
        data += self._authCode
        data += '","deviceIp":"'
        data += self._deviceIP
        data += '","devicePort":"'
        data += self._devicePort
        data += '","targetId":"1","targetType":"3"},"seq":0,"value":{'
        if parameters.prefix_commands is not None:
            data += parameters.prefix_commands+','
        data += '"transitCmd":"'
        data += parameters.command
        data += '"'
        if parameters.suffix_commands is not None:
            data += ','+parameters.suffix_commands
        data += '}}\n'
        print(f"Sending command {data}")
        self._send_binary_packet(0x00c800fa, 0x01090000, self._packet_id, 0x00, data)
        if parameters.wait_for_ack:
            self._waiting_for_command = self._packet_id
            await self._wait_for_ack.wait()
            self._wait_for_ack.clear()


    def send_command(self, command, params):
        if not self._identified:
            logging.error("Sent a command before the robot has identified itself")
            return 4, "Not identified"

        parameters = types.SimpleNamespace()
        parameters.command = None
        parameters.wait_for_ack = True
        parameters.prefix_commands = None
        parameters.suffix_commands = None

        if command == 'wait':
            if 'seconds' not in params:
                return 6, "Missing parameter (seconds)"
            try:
                parameters.seconds = float(params['seconds'])
            except:
                return 7, "Invalid value for seconds"
            parameters.command = 'wait'
        elif command == 'waitState':
            if 'state' not in params:
                return 6, "Missing parameter (state)"
            if params['state'] == 'cleaning':
                parameters.state = '1'
            elif params['state'] == 'stopped':
                parameters.state = '2'
            elif params['state'] == 'returning':
                parameters.state = '4'
            elif params['state'] == 'charging':
                parameters.state = '5'
            elif params['state'] == 'charged':
                parameters.state = '6'
            elif params['state'] == 'home':
                parameters.state = 'home'
            else:
                return 7, "Invalid value (valid values are 'cleaning', 'stopped', 'returning', 'charging', 'charged' and 'home'"
            parameters.command = 'waitState'
        elif command == 'clean':
            logging.info("Starting to clean")
            parameters.command = '100'
        elif command == 'stop':
            logging.info("Stopping cleaning")
            parameters.command = '102'
        elif command == 'return':
            logging.info("Returning to base")
            parameters.command = '104'
        elif command == 'updateMap':
            logging.info("Asking map")
            parameters.command = '131'
        elif command == 'sound':
            if "status" not in params:
                return 6, "Missing parameter (status)"
            if params['status'] == '0':
                logging.info("Disabling sound")
                parameters.command = '125'
            elif params['status'] == '1':
                logging.info("Enabling sound")
                parameters.command = '123'
            else:
                return 7, "Invalid value (valid values are 0 and 1)"
        elif command == 'fan':
            parameters.command = '110'
            if 'speed' not in params:
                return 6, "Missing parameter (speed)"
            if params['speed'] == '0':
                parameters.prefix_commands = '"fan":"1"' # OFF
            elif params['speed'] == '1':
                parameters.prefix_commands = '"fan":"4"' # ECO
            elif params['speed'] == '2':
                parameters.prefix_commands = '"fan":"2"' # NORMAL
            elif params['speed'] == '3':
                parameters.prefix_commands = '"fan":"3"' # TURBO
            else:
                return 7, "Invalid value (valid values are 0, 1, 2 and 3)"
            logging.info(f"Setting fan to {params['speed']}")
        elif command == 'watertank':
            parameters.command = '145'
            if 'speed' not in params:
                return 6, "Missing parameter (speed)"
            if params['speed'] == '0':
                parameters.suffix_commands = '"waterTank":"255"' # OFF
            elif params['speed'] == '1':
                parameters.suffix_commands = '"waterTank":"60"' # SMALL
            elif params['speed'] == '2':
                parameters.suffix_commands = '"waterTank":"40"' # NORMAL
            elif params['speed'] == '3':
                parameters.suffix_commands = '"waterTank":"20"' # FAST
            else:
                return 7, "Invalid value (valid values are 0, 1, 2 and 3)"
            logging.info(f"Setting water to {params['speed']}")
        elif command == 'mode':
            parameters.command = '106'
            if 'type' not in params:
                return 6, "Missing parameter (type)"
            if params['type'] == 'auto':
                parameters.prefix_commands = '"mode":"11"'
            elif params['type'] == 'gyro':
                parameters.prefix_commands = '"mode":"1"'
            elif params['type'] == 'random':
                parameters.prefix_commands = '"mode":"3"'
            elif params['type'] == 'borders':
                parameters.prefix_commands = '"mode":"4"'
            elif params['type'] == 'area':
                parameters.prefix_commands = '"mode":"6"'
            elif params['type'] == 'x2':
                parameters.prefix_commands = '"mode":"8"'
            elif params['type'] == 'scrub':
                parameters.prefix_commands = '"mode":"10"'
            else:
                return 7, "Invalid value (valid values are 'auto','giro','random','borders','area','x2','scrub')"
            logging.info(f"Setting mode to {params['type']}")
        elif command == 'notifyConnection': # seems to be sent whenever the tablet connects to the server
            parameters.command = '400'
            parameters.wait_for_ack = False
            logging.info("Web client opened")
        elif command == 'askStatus': # seems to ask the robot to send a Status packet
            parameters.command = '98'
            parameters.wait_for_ack = False
            logging.info("Asking status")
        elif command == 'goForward':
            parameters.command = 'manual'
            parameters.direction = 1
        elif command == 'goBackwards':
            parameters.command = 'manual'
            parameters.direction = 2
        elif command == 'turnLeft':
            parameters.command = 'manual'
            parameters.direction = 3
        elif command == 'turnRight':
            parameters.command = 'manual'
            parameters.direction = 4
        elif command == 'stayStill':
            parameters.command = 'manual'
            parameters.direction = 0
        else:
            logging.error(f"Unknown command {command}")
            return 5, "Unknown command"

        self._packet_queue.put_nowait(parameters)
        return 0, "{}"

    def close(self):
        print("Robot disconnected")
        self._identified = False
        self._end_tasks = True
        self._wait_for_ack.set()
        self._wait_for_status.set()
        self._manual_event.set()
        self._packet_queue.put_nowait(None)
        super().close()

    def new_data(self):
        if len(self._data) < 20:
            return False
        data_header = self._data[0:20]
        header = struct.unpack("<LLLLL", self._data[0:20])
        if len(self._data) < header[0]:
            return False
        payload = self._data[20:header[0]]
        self._data = self._data[header[0]:]
        try:
            header_str = ""
            c = 0
            for n in data_header:
                d = hex(n)[2:]
                if n < 16:
                    d = "0"+d
                header_str += d + " "
                c += 1
                if (c%4 == 0) and (c < 20):
                    header_str += "| "
            logging.info(f"Received packet with values {header_str}")
        except:
            traceback.print_exc()

        # process the packet
        # PING
        if self._check_header(header, 0x14, 0x00c80100, 0x01,0x03e7):
            print("Pong")
            self._send_binary_packet(0x00c80111, 0x01080001, header[3], 0x03e7)
            return True
        # Identification
        if self._check_header(header, None, 0x0010, 0x0001, 0x00):
            self._send_payload(payload)
            self._log_payload(payload, "connection")
            payload = json.loads(payload)
            self._token = payload['value']['token']
            self._deviceId = payload['value']['deviceId']
            self._appKey = payload['value']['appKey']
            self._authCode = payload['value']['authCode']
            self._deviceIP = payload['value']['deviceIp']
            self._devicePort = payload['value']['devicePort']
            robot_manager.get_robot(self._deviceId).connected(self)
            self._identified = True
            now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            self._send_binary_packet(0x00c80011, 0x01, header[3], 0x00, '{"msg":"login succeed","result":0,"version":"1.0","time":"'+now+'"}')
            logging.info(f"Robot identified as {self._deviceId} at IP {self._deviceIP}")
            return True
        # Status
        if self._check_header(header, None, 0x0018, 0x0001, 0x00):
            print("Status")
            self._send_binary_packet(0x00c80019, 0x01, header[3], 0x01, '{"msg":"OK","result":0,"version":"1.0"}\n')
            self._send_payload(payload)
            self._log_payload(payload, "status")
            self._wait_for_status.set()
            return True
        # ACK
        if self._check_header(header, None, 0x000000fa, 0x0001, 0x00):
            if self._waiting_for_command is not None:
                if header[3] == self._waiting_for_command:
                    self._send_payload(payload)
                    self._waiting_for_command = None
                    self._wait_for_ack.set()
                    print("ACK fine")
                else:
                    print("ACK error")
            return True
        # Map
        if self._check_header(header, None, 0x0014, 0x0001, 0x00):
            print("Map")
            self._send_payload(payload)
            self._log_payload(payload, "map")
            return True
        # Error
        if self._check_header(header, None, 0x0016, 0x0001, 0x00):
            print("Error")
            self._log_payload(payload, "error")
            self._send_binary_packet(0x00c80019, 0x01, header[3], 0x01, '{"msg":"OK","result":0,"version":"1.0"}\n')
            return True
        print("Unknown packet")
        print(header)
        print(payload)
        logging.info(f"Unknown packet {header} {payload}")
        return True

    def _log_payload(self, payload, type):
        try:
            jsonPayload = json.loads(payload)
        except:
            print(f'Payload is not a JSON file: "{payload}"')
            logging.error(f'Payload is not a JSON file: "{payload}"')
            return
        logging.info(f"New {type}: {json.dumps(jsonPayload, sort_keys=True, indent=4)}\n\n")

    def _send_payload(self, payload):
        if len(payload) == 0:
            return
        try:
            jsonPayload = json.loads(payload)
        except:
            print(f'Payload is not a JSON file: "{payload}"')
            return

        if ('value' in jsonPayload) and ('workState' in jsonPayload['value']):
            self._state = jsonPayload['value']['workState']

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

    def _send_binary_packet(self, value1, value2, packet_id, value3, data = b""):
        logging.info(f"Sending packet with id {hex(packet_id)}")
        if isinstance(data, str):
            data = data.encode('utf8')
        header = bytearray(struct.pack("<LLLLL", 20 + len(data), value1, value2, packet_id, value3))
        self._writer.write(header + data)
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

robot_server = RobotServer()
