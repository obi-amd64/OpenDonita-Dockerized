import datetime
import select
import sys
import traceback
import signal

from congaModules.httpClasses import HTTPServer
from congaModules.robotClasses import RobotServer
from congaModules.signal import Signal

class Multiplexer(object):
    def __init__(self, registered_pages, robot_manager, port_http = 80, port_bona = 20008):
        super().__init__()

        self._socklist = []
        self._http_server = HTTPServer(registered_pages, port_http)
        self._add_socket(self._http_server)
        self._robot_server = RobotServer(self, robot_manager, port_bona)
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
