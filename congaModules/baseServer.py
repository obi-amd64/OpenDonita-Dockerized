import socket
from congaModules.observer import Signal

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

