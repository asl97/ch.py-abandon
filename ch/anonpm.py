import socket

import ch


# noinspection PyProtectedMember,PyPep8Naming,PyUnusedLocal
class _ANON_PM_OBJECT:
    """Manages connection with Chatango anon PM."""

    def __init__(self, mgr, name, sock):
        self._connected = False
        self._mgr = mgr
        self._sock = sock
        self._name = name
        self._wlock = False
        self._firstCommand = True
        self._wbuf = b""
        self._wlockbuf = b""
        self._rbuf = b""
        self._pingTask = None

        if self._auth():
            self._pingTask = self._mgr.setInterval(self._mgr._pingDelay, self.ping)
            self._connected = True

    def _auth(self):
        self._sendCommand("mhs", "mini", "unknown", "%s" % self._name)
        self._setWriteLock(True)
        return True

    def disconnect(self):
        """Disconnect the bot from PM"""
        self._disconnect()
        self._callEvent("onAnonPMDisconnect", ch.User(self._name))

    def _disconnect(self):
        self._connected = False
        self._pingTask.cancel()
        self._sock.close()
        self._sock = None

    def ping(self):
        """send a ping"""
        self._sendCommand("")
        self._callEvent("onPMPing")

    def message(self, user, msg):
        """send a pm to a user"""
        if msg is not None:
            self._sendCommand("msg", user.name, msg)

    ####
    # Feed
    ####
    def _feed(self, data):
        """
        Feed data to the connection.

        @type data: bytes
        @param data: data to be fed
        """
        *foods, self._rbuf = (self._rbuf + data.decode('utf-8', errors="replace")).split("\x00")
        for food in foods:
            food = food.rstrip("\r\n")
            if food:
                self._process(food)

    def _process(self, data):
        """
        Process a command string.

        @type data: str
        @param data: the command string
        """
        self._callEvent("onRaw", data)
        data = data.split(":")
        cmd, args = data[0], data[1:]
        func = "_rcmd_" + cmd
        if hasattr(self, func):
            getattr(self, func)(args)
        else:
            if ch.debug:
                print("[unknown] data: " + str(data))

    @property
    def mgr(self):
        return self._mgr

    ####
    # Received Commands
    ####

    def _rcmd_mhs(self, args):
        """
        note to future maintainers

        args[1] is ether "online" or "offline"
        """
        self._connected = True
        self._setWriteLock(False)

    def _rcmd_msg(self, args):
        user = ch.User(args[0])
        body = ch._strip_html(":".join(args[5:]))
        self._callEvent("onPMMessage", user, body)

    ####
    # Util
    ####
    def _callEvent(self, evt, *args, **kw):
        getattr(self.mgr, evt)(self, *args, **kw)
        self.mgr.onEventCalled(self, evt, *args, **kw)

    def _write(self, data):
        if self._wlock:
            self._wlockbuf += data
        else:
            self.mgr._write(self, data)

    def _setWriteLock(self, lock):
        self._wlock = lock
        if self._wlock is False:
            self._write(self._wlockbuf)
            self._wlockbuf = b""

    def _sendCommand(self, *args):
        """
        Send a command.

        @type args: [str, str, ...]
        @param args: command and list of arguments
        """
        if self._firstCommand:
            terminator = b"\x00"
            self._firstCommand = False
        else:
            terminator = b"\r\n\x00"
        self._write(":".join(args).encode() + terminator)


################################################################
# ANON PM class
################################################################
# noinspection PyProtectedMember,PyUnusedLocal,PyPep8Naming
# noinspection PyProtectedMember,PyPep8Naming
class ANON_PM:
    """Comparable wrapper for anon Chatango PM"""

    ####
    # Init
    ####
    def __init__(self, mgr):
        self._mgr = mgr
        self._wlock = False
        self._firstCommand = True
        self._persons = dict()
        self._wlockbuf = b""
        self._pingTask = None

    ####
    # Connections
    ####
    def _connect(self, name):
        sock = socket.socket()
        sock.connect((self._mgr._anonPMHost, self._mgr._PMPort))
        self._persons[name] = _ANON_PM_OBJECT(self._mgr, name, sock)

    def message(self, user, msg):
        """send a pm to a user"""
        if user.name not in self._persons:
            self._connect(user.name)
        self._persons[user.name].message(user, msg)

    def getConnections(self):
        return list(self._persons.values())
