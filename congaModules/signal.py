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

