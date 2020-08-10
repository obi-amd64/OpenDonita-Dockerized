import configparser
import json
import os

class RobotManager(object):
    def __init__(self, config_path):
        super().__init__()
        self._robots = {} # contains Robot objects, one per physical robot, identified by the DeviceId
        self._config_path = config_path

    def get_robot(self, deviceId):
        if deviceId not in self._robots:
            self._robots[deviceId] = Robot(deviceId, self._config_path)
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
