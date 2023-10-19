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

import random
import os
import logging
import asyncio
import traceback

from init import port_bona, port_http, running_in_docker, html_path

from congaModules.robotManager import robot_manager
from congaModules.httpClasses import http_server
from congaModules.robotClasses import robot_server

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
    data = server_object.get_data()
    robot = robot_manager.get_robot(data['deviceId'])
    robot.httpDataUpdate(data)
    send_robot_header(server_object)
    server_object.send_chunked('{"msg":"ok","result":"0","version":"1.0.0"}')
    server_object.close()


def robot_get_token(server_object):
    server_object.convert_data()

    data = server_object.get_data()
    robot = robot_manager.get_robot(data['deviceId'])
    robot.httpDataUpdate(data)
    robot_data = {}
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
    robots = robot_manager.get_robot_list()
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
                robot = robot_manager.get_robot(robot_id)
                print(f"Pido {action}")
                try:
                    dtype, error, answer = robot.send_command(action, server_object.get_params())
                except:
                    traceback.print_exc()
        else:
            if robotId in robots:
                robot = robot_manager.get_robot(robotId)
                dtype, error, answer = robot.send_command(action, server_object.get_params())
            else:
                server_object.add_header("Content-Type", "application/json")
                server_object.send_answer('{"error":2, "value":"Invalid robot ID"}', 400, "INVALID_ROBOT_ID")
                server_object.close()
                return
    if (error is None) or (answer is None):
        answer = '{}'
        error = 0
        dtype = "Content-Type", "application/json"
    server_object.add_header("Content-Type", dtype)
    if (dtype == "application/json"):
        server_object.send_answer('{"error":' + str(error) + ', "value":'+answer+'}', 200, "")
    else:
        server_object.send_answer(answer, 200, "")
    server_object.close()


def robot_list(server_object):
    robots = robot_manager.get_robot_list()
    data = []
    for robot_id in robots:
        data.append(robot_id)
    server_object.send_answer_json_close(data)


def html_server(server_object):

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
            server_object.send_answer('<html><head></head><body><h1>401 Error while reading the file</h1><p>There was an error while trying to read that file</p></body></html>', 401, "Error reading file")
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

loop = asyncio.new_event_loop()  # asyncio.get_event_loop()

http_server.configure(registered_pages, loop, port_http)
logging.info("HTTP server started on port " + str(port_http))
robot_server.configure(loop, port_bona)
logging.info("Robot server started on port " + str(port_bona))

try:
    loop.run_forever()
except:
    pass

robot_server.close()
http_server.close()
loop.close()
