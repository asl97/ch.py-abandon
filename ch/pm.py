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
# PM class
################################################################
class PM:
    """Manages a connection with Chatango PM."""

    ####
    # Init
    ####
    def __init__(self, mgr):
        self._auth_re = re.compile(r"auth\.chatango\.com ?= ?([^;]*)", re.IGNORECASE)
        self.connected = False
        self.mgr = mgr
        self._auid = None
        self._blocklist = set()
        self._contacts = set()
        self._status = dict()
        self._wlock = False
        self._firstCommand = True
        self._wbuf = b""
        self._wlockbuf = b""
        self._rbuf = ""
        self.sock = None
        self.pingTask = None
        self._write = self._writeUnlocked
        self.sendCommand = self._firstSendCommand
        self._connect()

    ####
    # Connections
    ####
    def _connect(self):
        self._wbuf = b""
        self.sock = socket.socket()
        self.sock.connect((self.mgr.PMHost, self.mgr.PMPort))
        self.sendCommand = self._firstSendCommand
        if self.auth():
            self.pingTask = self.mgr.setInterval(self.mgr.pingDelay, self.ping)
            self.connected = True

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

    def auth(self):
        self._auid = self._getAuth(self.mgr.name, self.mgr.password)
        if self._auid is None:
            self.sock.close()
            self._callEvent("onLoginFail")
            self.sock = None
            return False
        self.sendCommand("tlogin", self._auid, "2")
        self._setWriteLock(True)
        return True

    def disconnect(self):
        """Disconnect the bot from PM"""
        self._disconnect()
        self._callEvent("onPMDisconnect")

    def _disconnect(self):
        self.connected = False
        self.pingTask.cancel()
        self.sock.close()
        self.sock = None

    ####
    # Feed
    ####
    def feed(self, data):
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

    ####
    # Properties
    ####
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
        self.sendCommand("wl")
        self.sendCommand("getblock")
        self._callEvent("onPMConnect")

    def _rcmd_wl(self, args):
        self._contacts = set()
        for i in range(0, len(args), 4):
            name, last_on, is_on, idle = args[i: i + 4]
            user = ch.User(name)
            if last_on == "None":
                pass  # in case chatango gives a "None" as data argument
            elif not is_on == "on":
                self._status[user] = [int(last_on), False, 0]
            elif idle == '0':
                self._status[user] = [int(last_on), True, 0]
            else:
                self._status[user] = [int(last_on), True, time.time() - (int(idle) * 60)]
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
        if args[2] == "online":
            if args[1] == '0':
                idle = 0
            else:
                idle = time.time() - int(args[1]) * 60
            is_on = True
        else:
            last_on = args[1]
            idle = 0
            is_on = False
        self._status[user] = [last_on, is_on, idle]

    def _rcmd_DENIED(self, args):
        self._disconnect()
        self._callEvent("onLoginFail")

    def _rcmd_msg(self, args):
        user = ch.User(args[0])
        body = ch.strip_html(":".join(args[5:]))
        self._callEvent("onPMMessage", user, body)

    def _rcmd_msgoff(self, args):
        user = ch.User(args[0])
        body = ch.strip_html(":".join(args[5:]))
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
        self.sendCommand("")
        self._callEvent("onPMPing")

    def message(self, user, msg):
        """send a pm to a user"""
        if msg is not None:
            self.sendCommand("msg", user.name, msg)

    def addContact(self, user):
        """add contact"""
        if user not in self._contacts:
            self.sendCommand("wladd", user.name)
            self._contacts.add(user)
            self._callEvent("onPMContactAdd", user)

    def removeContact(self, user):
        """remove contact"""
        if user in self._contacts:
            self.sendCommand("wldelete", user.name)
            self._contacts.remove(user)
            self._callEvent("onPMContactRemove", user)

    def block(self, user):
        """block a person"""
        if user not in self._blocklist:
            self.sendCommand("block", user.name, user.name, "S")
            self._blocklist.add(user)
            self._callEvent("onPMBlock", user)

    def unblock(self, user):
        """unblock a person"""
        if user in self._blocklist:
            self.sendCommand("unblock", user.name)

    def track(self, user):
        """get and store status of person for future use"""
        self.sendCommand("track", user.name)

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

    def _writeLocked(self, data):
        self._wlockbuf += data

    def _writeUnlocked(self, data):
        self.mgr.write(self, data)

    def _setWriteLock(self, lock):
        self._wlock = lock
        if self._wlock is False:
            self._write = self._writeUnlocked
            self._write(self._wlockbuf)
            self._wlockbuf = b""
        else:
            self._write = self._writeLocked

    def _firstSendCommand(self, *args):
        self._write(":".join(args).encode() + b"\x00")
        self.sendCommand = self._otherSendCommand

    def _otherSendCommand(self, *args):
        self._write(":".join(args).encode() + b"\r\n\x00")

    def getConnections(self):
        return [self]
