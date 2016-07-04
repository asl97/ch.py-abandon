################################################################
# Title: Chatango Library
# Original Author: Lumirayz/Lumz <lumirayz@gmail.com>
# Version: 1.4.0
################################################################

################################################################
# License
################################################################
# Copyright 2011 Lumirayz
# Copyright 2015 asl97 & aqua101
# This program is distributed under the terms of the GNU AGPL 3

################################################################
# Imports
################################################################
import re
import socket
import time
import urllib.parse
import urllib.request

import ch


################################################################
# ANON PM class
################################################################
# noinspection PyProtectedMember,PyUnusedLocal,PyPep8Naming
class _ANON_PM_OBJECT:
    """Manages connection with Chatango anon PM."""

    def __init__(self, mgr, name):
        self._connected = False
        self._mgr = mgr
        self._wlock = False
        self._firstCommand = True
        self._wbuf = b""
        self._wlockbuf = b""
        self._rbuf = b""
        self._pingTask = None
        self._name = name

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
        *foods, self._rbuf = (self._rbuf + data).split(b"\x00")
        for food in foods:
            food = food.decode(errors="replace").rstrip("\r\n")
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
        self._persons[name] = _ANON_PM_OBJECT(self._mgr, name)
        sock = socket.socket()
        sock.connect((self._mgr._anonPMHost, self._mgr._PMPort))
        sock.setblocking(False)
        self._persons[name]._sock = sock
        if not self._persons[name]._auth():
            return
        self._persons[name]._pingTask = self._mgr.setInterval(self._mgr._pingDelay, self._persons[name].ping)
        self._persons[name]._connected = True

    def message(self, user, msg):
        """send a pm to a user"""
        if user.name not in self._persons:
            self._connect(user.name)
        self._persons[user.name].message(user, msg)

    def getConnections(self):
        return list(self._persons.values())


################################################################
# PM class
################################################################
# noinspection PyProtectedMember,PyUnusedLocal,PyBroadException
class PM:
    """Manages a connection with Chatango PM."""

    ####
    # Init
    ####
    def __init__(self, mgr):
        self._auth_re = re.compile(r"auth\.chatango\.com ?= ?([^;]*)", re.IGNORECASE)
        self._connected = False
        self._mgr = mgr
        self._auid = None
        self._blocklist = set()
        self._contacts = set()
        self._status = dict()
        self._wlock = False
        self._firstCommand = True
        self._wbuf = b""
        self._wlockbuf = b""
        self._rbuf = b""
        self._pingTask = None
        self._connect()

    ####
    # Connections
    ####
    def _connect(self):
        self._wbuf = b""
        self._sock = socket.socket()
        self._sock.connect((self._mgr._PMHost, self._mgr._PMPort))
        self._sock.setblocking(False)
        self._firstCommand = True
        if not self._auth():
            return
        self._pingTask = self.mgr.setInterval(self._mgr._pingDelay, self.ping)
        self._connected = True

    def _getAuth(self, name, password):
        """
        Request an auid using name and password.

        @type name: str
        @param name: name
        @type password: str
        @param password: password

        @rtype: str
        @return: auid
        """
        data = urllib.parse.urlencode({
            "user_id": name,
            "password": password,
            "storecookie": "on",
            "checkerrors": "yes"
        }).encode()
        try:
            resp = urllib.request.urlopen("http://chatango.com/login", data)
            headers = resp.headers
        except:
            return None
        for header, value in headers.items():
            if header.lower() == "set-cookie":
                m = self._auth_re.search(value)
                if m:
                    auth = m.group(1)
                    if auth == "":
                        return None
                    return auth
        return None

    def _auth(self):
        self._auid = self._getAuth(self._mgr.name, self._mgr.password)
        if self._auid is None:
            self._sock.close()
            self._callEvent("onLoginFail")
            self._sock = None
            return False
        self._sendCommand("tlogin", self._auid, "2")
        self._setWriteLock(True)
        return True

    def disconnect(self):
        """Disconnect the bot from PM"""
        self._disconnect()
        self._callEvent("onPMDisconnect")

    def _disconnect(self):
        self._connected = False
        self._sock.close()
        self._sock = None

    ####
    # Feed
    ####
    def _feed(self, data):
        """
        Feed data to the connection.

        @type data: bytes
        @param data: data to be fed
        """
        *foods, self._rbuf = (self._rbuf + data).split(b"\x00")
        for food in foods:
            food = food.decode(errors="replace").rstrip("\r\n")
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

    ####
    # Properties
    ####
    @property
    def mgr(self):
        return self._mgr

    @property
    def contacts(self):
        return self._contacts

    @property
    def blocklist(self):
        return self._blocklist

    ####
    # Received Commands
    ####
    def _rcmd_OK(self, args):
        self._setWriteLock(False)
        self._sendCommand("wl")
        self._sendCommand("getblock")
        self._callEvent("onPMConnect")

    def _rcmd_wl(self, args):
        self._contacts = set()
        for i in range(len(args) // 4):
            name, last_on, is_on, idle = args[i * 4: i * 4 + 4]
            user = ch.User(name)
            if last_on == "None":
                pass  # in case chatango gives a "None" as data argument
            elif not is_on == "on":
                self._status[user] = [int(last_on), False, 0]
            elif idle == '0':
                self._status[user] = [int(last_on), True, 0]
            else:
                self._status[user] = [int(last_on), True, time.time() - int(idle) * 60]
            self._contacts.add(user)
        self._callEvent("onPMContactlistReceive")

    def _rcmd_block_list(self, args):
        self._blocklist = set()
        for name in args:
            if name == "":
                continue
            self._blocklist.add(ch.User(name))

    def _rcmd_idleupdate(self, args):
        user = ch.User(args[0])
        last_on, is_on, idle = self._status[user]
        if args[1] == '1':
            self._status[user] = [last_on, is_on, 0]
        else:
            self._status[user] = [last_on, is_on, time.time()]

    def _rcmd_track(self, args):
        user = ch.User(args[0])
        if user in self._status:
            last_on = self._status[user][0]
        else:
            last_on = 0
        if args[1] == '0':
            idle = 0
        else:
            idle = time.time() - int(args[1]) * 60
        if args[2] == "online":
            is_on = True
        else:
            is_on = False
        self._status[user] = [last_on, is_on, idle]

    def _rcmd_DENIED(self, args):
        self._disconnect()
        self._callEvent("onLoginFail")

    def _rcmd_msg(self, args):
        user = ch.User(args[0])
        body = ch._strip_html(":".join(args[5:]))
        self._callEvent("onPMMessage", user, body)

    def _rcmd_msgoff(self, args):
        user = ch.User(args[0])
        body = ch._strip_html(":".join(args[5:]))
        self._callEvent("onPMOfflineMessage", user, body)

    def _rcmd_wlonline(self, args):
        user = ch.User(args[0])
        last_on = float(args[1])
        self._status[user] = [last_on, True, last_on]
        self._callEvent("onPMContactOnline", user)

    def _rcmd_wloffline(self, args):
        user = ch.User(args[0])
        last_on = float(args[1])
        self._status[user] = [last_on, False, 0]
        self._callEvent("onPMContactOffline", user)

    def _rcmd_kickingoff(self, args):
        self.disconnect()

    def _rcmd_toofast(self, args):
        self.disconnect()

    def _rcmd_unblocked(self, user):
        """call when successfully unblocked"""
        if user in self._blocklist:
            self._blocklist.remove(user)
            self._callEvent("onPMUnblock", user)

    ####
    # Commands
    ####
    def ping(self):
        """send a ping"""
        self._sendCommand("")
        self._callEvent("onPMPing")

    def message(self, user, msg):
        """send a pm to a user"""
        if msg is not None:
            self._sendCommand("msg", user.name, msg)

    def addContact(self, user):
        """add contact"""
        if user not in self._contacts:
            self._sendCommand("wladd", user.name)
            self._contacts.add(user)
            self._callEvent("onPMContactAdd", user)

    def removeContact(self, user):
        """remove contact"""
        if user in self._contacts:
            self._sendCommand("wldelete", user.name)
            self._contacts.remove(user)
            self._callEvent("onPMContactRemove", user)

    def block(self, user):
        """block a person"""
        if user not in self._blocklist:
            self._sendCommand("block", user.name, user.name, "S")
            self._blocklist.add(user)
            self._callEvent("onPMBlock", user)

    def unblock(self, user):
        """unblock a person"""
        if user in self._blocklist:
            self._sendCommand("unblock", user.name)

    def track(self, user):
        """get and store status of person for future use"""
        self._sendCommand("track", user.name)

    def checkOnline(self, user):
        """return True if online, False if offline, None if unknown"""
        if user in self._status:
            return self._status[user][1]
        else:
            return None

    def getIdle(self, user):
        """return last active time, time.time() if isn't idle, 0 if offline, None if unknown"""
        if user not in self._status:
            return None
        if not self._status[user][1]:
            return 0
        if not self._status[user][2]:
            return time.time()
        else:
            return self._status[user][2]

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

    def getConnections(self):
        return [self]
