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
import socket
import time

import ch


################################################################
# Room class
################################################################
# noinspection PyProtectedMember,PyUnusedLocal,PyUnusedLocal,PyPep8Naming
class Room:
    """Manages a connection with a Chatango room."""

    ####
    # Init
    ####
    def __init__(self, room, uid=None, server=None, port=None, mgr=None):
        """init, don't overwrite"""
        # Basic stuff
        self._name = room
        self._server = server or ch.getServer(room)
        self._port = port or 443
        self._mgr = mgr

        # Under the hood
        self._connected = False
        self._reconnecting = False
        self._uid = uid or ch._genUid()
        self._rbuf = ""
        self._wbuf = b""
        self._wlockbuf = b""
        self._owner = None
        self._mods = dict()
        self._mqueue = dict()
        self._history = list()
        self._userlist = list()
        self._firstCommand = True
        self._connectAmmount = 0
        self._premium = False
        self._userCount = 0
        self._pingTask = None
        self._botname = None
        self._currentname = None
        self._users = dict()
        self._msgs = dict()
        self._wlock = False
        self._silent = False
        self._banlist = dict()
        self._unbanlist = dict()

        # Inited vars
        if self._mgr:
            self._connect()

    ####
    # Connect/disconnect
    ####
    def _connect(self):
        """Connect to the server."""
        self._sock = socket.socket()
        self._sock.connect((self._server, self._port))
        self._sock.setblocking(False)
        self._firstCommand = True
        self._wbuf = b""
        self._auth()
        self._pingTask = self.mgr.setInterval(self.mgr._pingDelay, self.ping)
        if not self._reconnecting:
            self.connected = True

    def reconnect(self):
        """Reconnect."""
        self._reconnect()

    def _reconnect(self):
        """Reconnect."""
        self._reconnecting = True
        if self.connected:
            self._disconnect()
        self._uid = ch._genUid()
        self._connect()
        self._reconnecting = False

    def disconnect(self):
        """Disconnect."""
        self._disconnect()
        self._callEvent("onDisconnect")

    def _disconnect(self):
        """Disconnect from the server."""
        if not self._reconnecting:
            self.connected = False
        for user in self._userlist:
            if self in user._sids:
                del user._sids[self]
        self._userlist = list()
        self._pingTask.cancel()
        self._sock.close()
        if not self._reconnecting:
            del self.mgr._rooms[self.name]

    def _auth(self):
        """Authenticate."""
        # login as name with password
        if self.mgr.name and self.mgr.password:
            self._sendCommand("bauth", self.name, self._uid, self.mgr.name, self.mgr.password)
            self._currentname = self.mgr.name
        # login as anon
        else:
            self._sendCommand("bauth", self.name)

        self._setWriteLock(True)

    ####
    # Properties
    ####
    @property
    def name(self):
        return self._name

    @property
    def botName(self):
        if self.mgr.name and self.mgr.password:
            return self.mgr.name
        elif self.mgr.name and self.mgr.password is None:
            return "#" + self.mgr.name
        elif self.mgr.name is None:
            return self._botname

    @property
    def currentName(self):
        return self._currentname

    @property
    def mgr(self):
        return self._mgr

    @property
    def userList(self, mode=None, unique=None, memory=None):
        ul = None

        if mode is None:
            mode = self.mgr._userlistMode
        if unique is None:
            unique = self.mgr._userlistUnique
        if memory is None:
            memory = self.mgr._userlistMemory

        if mode == ch.Userlist.Recent:
            ul = map(lambda x: x.user, self._history[-memory:])
        elif mode == ch.Userlist.All:
            ul = self._userlist

        if unique:
            return list(set(ul))
        else:
            return ul

    @property
    def usernames(self):
        ul = self._userlist
        return list(map(lambda x: x.name, ul))

    @property
    def user(self):
        return self.mgr.user

    @property
    def owner(self):
        return self._owner

    @property
    def ownerName(self):
        return self._owner.name

    @property
    def mods(self):
        return set(self._mods)

    @property
    def modNames(self):
        return [x.name for x in self.mods]

    @property
    def userCount(self):
        return self._userCount

    @property
    def silent(self):
        return self._silent

    @silent.setter
    def silent(self, val):
        self._silent = val

    @property
    def banList(self):
        return list(self._banlist.keys())

    @property
    def unBanList(self):
        return [[record["target"], record["src"]] for record in self._unbanlist.values()]

    ####
    # Feed/process
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

    ####
    # Received Commands
    ####
    def _rcmd_ok(self, args):
        # if no name, join room as anon and no password
        if args[2] == "N" and self.mgr.password is None and self.mgr.name is None:
            n = args[4].rsplit('.', 1)[0]
            n = n[-4:]
            puid = args[1][0:8]
            name = "!anon" + ch._getAnonId(n, puid)
            self._botname = name
            self._currentname = name
            self.user._nameColor = n
        # if got name, join room as name and no password
        elif args[2] == "N" and self.mgr.password is None:
            self._sendCommand("blogin", self.mgr.name)
            self._currentname = self.mgr.name
        # if got password but fail to login
        elif args[2] != "M":  # unsuccesful login
            self._callEvent("onLoginFail")
            self.disconnect()
        self._uid = args[1]
        self._puid = args[1][0:8]
        self._owner = ch.User(
            name=args[0],
            perm=(self.name, 1048575)
        )

        self._mods = dict()
        for x in args[6].split(";"):
            perm = int(x.split(",")[1])
            self._mods[ch.User(name=x.split(",")[0], perm=(self.name, perm))] = perm

        self._i_log = list()

    def _rcmd_denied(self, args):
        self._disconnect()
        self._callEvent("onConnectFail")

    def _rcmd_inited(self, args):
        self._sendCommand("g_participants", "start")
        self._sendCommand("getpremium", "1")
        self.requestBanlist()
        self.requestUnBanlist()
        if self._connectAmmount == 0:
            self._callEvent("onConnect")
            for msg in reversed(self._i_log):
                user = msg.user
                self._callEvent("onHistoryMessage", user, msg)
                self._addHistory(msg)
            del self._i_log
        else:
            self._callEvent("onReconnect")
        self._connectAmmount += 1
        self._setWriteLock(False)

    def _rcmd_premium(self, args):
        if float(args[1]) > time.time():
            self._premium = True
            if self.user._mbg:
                self.setBgMode(1)
            if self.user._mrec:
                self.setRecordingMode(1)
        else:
            self._premium = False

    def _rcmd_mods(self, args):
        modnames = args
        premods = set(self._mods)
        self._mods = dict()
        for x in args[6].split(";"):
            perm = int(x.split(",")[1])
            self._mods[ch.User(name=x.split(",")[0], perm=(self.name, perm))] = perm
        mods = set(self._mods)
        for user in mods - premods:  # modded
            self._callEvent("onModAdd", user)
        for user in premods - mods:  # demodded
            self._callEvent("onModRemove", user)
        self._callEvent("onModChange")

    def _rcmd_b(self, args):
        mtime = float(args[0])
        puid = args[3]
        ip = args[6]
        name = args[1]
        channel = args[7]
        rawmsg = ":".join(args[9:])
        msg, n, f = ch._clean_message(rawmsg)
        if name == "":
            nameColor = None
            name = "#" + (args[2] or "!anon" + ch._getAnonId(n, puid))
        else:
            if n:
                nameColor = ch._parseNameColor(n)
            else:
                nameColor = None
        i = args[5]
        unid = args[4]
        user = ch.User(
            name=name,
            puid=puid,
            ip=ip
        )
        # Create an anonymous message and queue it because msgid is unknown.
        if f:
            fontColor, fontFace, fontSize = ch._parseFont(f)
        else:
            fontColor, fontFace, fontSize = None, None, None
        msg = ch.Message(
            time=mtime,
            user=user,
            body=msg,
            raw=rawmsg,
            ip=ip,
            channel=channel,
            nameColor=nameColor,
            fontColor=fontColor,
            fontFace=fontFace,
            fontSize=fontSize,
            unid=unid,
            puid=puid,
            room=self
        )
        self._mqueue[i] = msg

    def _rcmd_u(self, args):
        if args[0] in self._mqueue:
            msg = self._mqueue[args[0]]
            if msg.user != self.user:
                msg.user._fontColor = msg.fontColor
                msg.user._fontFace = msg.fontFace
                msg.user._fontSize = msg.fontSize
                msg.user._nameColor = msg.nameColor
            del self._mqueue[args[0]]
            msg.attach(self, args[1])
            self._addHistory(msg)
            self._callEvent("onMessage", msg.user, msg)

    def _rcmd_i(self, args):
        mtime = float(args[0])
        puid = args[3]
        ip = args[6]
        name = args[1]
        rawmsg = ":".join(args[9:])
        msg, n, f = ch._clean_message(rawmsg)
        if name == "":
            nameColor = None
            name = "#" + (args[2] or "!anon" + ch._getAnonId(n, puid))
        else:
            if n:
                nameColor = ch._parseNameColor(n)
            else:
                nameColor = None
        i = args[5]
        unid = args[4]
        user = ch.User(
            name=name,
            puid=puid,
            ip=ip
        )
        # Create an anonymous message and queue it because msgid is unknown.
        if f:
            fontColor, fontFace, fontSize = ch._parseFont(f)
        else:
            fontColor, fontFace, fontSize = None, None, None
        msg = ch.Message(
            time=mtime,
            user=user,
            body=msg,
            raw=rawmsg,
            ip=ip,
            nameColor=nameColor,
            fontColor=fontColor,
            fontFace=fontFace,
            fontSize=fontSize,
            unid=unid,
            puid=puid,
            room=self
        )
        self._i_log.append(msg)

    def _rcmd_g_participants(self, args):
        args = ":".join(args).split(";")
        for data in args:
            data = data.split(":")
            puid = data[2]
            name = data[3].lower()
            if name == "none":
                continue
            user = ch.User(
                name=name,
                room=self,
                puid=puid,
                participant=('1', self, data[0])
            )
            self._userlist.append(user)

    def _rcmd_participant(self, args):
        puid = args[2]
        name = args[3].lower()
        if name == "none":
            return
        user = ch.User(
            name=name,
            puid=puid,
            participant=(args[0], self, args[1])
        )

        if args[0] == "0":  # leave
            self._userlist.remove(user)
            if user not in self._userlist or not self.mgr._userlistEventUnique:
                self._callEvent("onLeave", user, puid)
        else:  # join
            self._userlist.append(user)
            if user not in self._userlist or not self.mgr._userlistEventUnique:
                self._callEvent("onJoin", user, puid)

    def _rcmd_show_fw(self, args):
        self._callEvent("onFloodWarning")

    def _rcmd_show_tb(self, args):
        self._callEvent("onFloodBan")

    def _rcmd_tb(self, args):
        self._callEvent("onFloodBanRepeat")

    def _rcmd_delete(self, args):
        msg = self._msgs.get(args[0])
        if msg:
            if msg in self._history:
                self._history.remove(msg)
                self._callEvent("onMessageDelete", msg.user, msg)
                msg.detach()

    def _rcmd_deleteall(self, args):
        for msgid in args:
            self._rcmd_delete([msgid])

    def _rcmd_n(self, args):
        self._userCount = int(args[0], 16)
        self._callEvent("onUserCountChange")

    def _rcmd_blocklist(self, args):
        self._banlist = dict()
        sections = ":".join(args).split(";")
        for section in sections:
            params = section.split(":")
            if len(params) != 5:
                continue
            if params[2] == "":
                continue
            user = ch.User(params[2])
            self._banlist[user] = {
                "unid": params[0],
                "ip": params[1],
                "target": user,
                "time": float(params[3]),
                "src": ch.User(params[4])
            }
        self._callEvent("onBanlistUpdate")

    def _rcmd_unblocklist(self, args):
        self._unbanlist = dict()
        sections = ":".join(args).split(";")
        for section in sections:
            params = section.split(":")
            if len(params) != 5:
                continue
            if params[2] == "":
                continue
            user = ch.User(params[2])
            self._unbanlist[user] = {
                "unid": params[0],
                "ip": params[1],
                "target": user,
                "time": float(params[3]),
                "src": ch.User(params[4])
            }
        self._callEvent("onUnBanlistUpdate")

    def _rcmd_blocked(self, args):
        if args[2] == "":
            return
        target = ch.User(args[2])
        user = ch.User(args[3])
        self._banlist[target] = {"unid": args[0], "ip": args[1], "target": target, "time": float(args[4]), "src": user}
        self._callEvent("onBan", user, target)

    def _rcmd_unblocked(self, args):
        if args[2] == "":
            return
        target = ch.User(args[2])
        user = ch.User(args[3])
        del self._banlist[target]
        self._unbanlist[user] = {"unid": args[0], "ip": args[1], "target": target, "time": float(args[4]), "src": user}
        self._callEvent("onUnban", user, target)

    ####
    # Commands
    ####
    def login(self, NAME, PASS=None):
        """login as a user or set a name in room"""
        if PASS:
            self._sendCommand("blogin", NAME, PASS)
        else:
            self._sendCommand("blogin", NAME)
        self._currentname = NAME

    def logout(self):
        """logout of user in a room"""
        self._sendCommand("blogout")
        self._currentname = self._botname

    def ping(self):
        """Send a ping."""
        self._sendCommand("")
        self._callEvent("onPing")

    def rawMessage(self, msg, channel="0"):
        """
        Send a message without n and f tags.

        @type msg: str
        @param msg: message

        @type channel: str
        @param channel: channel mode
        """
        if not self._silent:
            self._sendCommand("bm:tl2r", channel, msg)

    def message(self, msg, html=False, channel="0"):
        """
        Send a message. (Use "\n" for new line)

        @type msg: str
        @param msg: message

        @type html: bool
        @param html: interpret message as html

        @type channel: str
        @param channel: channel mode
        """
        if msg is None:
            return
        msg = msg.rstrip()
        if not html:
            msg = msg.replace("<", "&lt;").replace(">", "&gt;")
        if len(msg) > self.mgr._maxLength:
            if self.mgr._tooBigMessage == ch.BigMessage.Cut:
                self.message(msg[:self.mgr._maxLength], html=html)
            elif self.mgr._tooBigMessage == ch.BigMessage.Multiple:
                while len(msg) > 0:
                    sect = msg[:self.mgr._maxLength]
                    msg = msg[self.mgr._maxLength:]
                    self.message(sect, html=html)
            return
        msg = "<n" + self.user.nameColor + "/>" + msg
        if self._currentname is not None and not self._currentname.startswith("!anon"):
            font_properties = "<f x%0.2i%s=\"%s\">" % (self.user.fontSize, self.user.fontColor, self.user.fontFace)
            if "\n" in msg:
                msg = msg.replace("\n", "</f></p><p>%s" % font_properties)
            msg = font_properties + msg
        msg.replace("~", "&#126;")
        self.rawMessage(msg, channel)

    def setBgMode(self, mode):
        """turn on/off bg"""
        self._sendCommand("msgbg", str(mode))

    def setRecordingMode(self, mode):
        """turn on/off rcecording"""
        self._sendCommand("msgmedia", str(mode))

    def addMod(self, user):
        """
        Add a moderator.

        @type user: User
        @param user: User to mod.
        """
        if self.getLevel(ch.User(self._currentname)) == 2:
            self._sendCommand("addmod", user.name)

    def removeMod(self, user):
        """
        Remove a moderator.

        @type user: User
        @param user: User to demod.
        """
        if self.getLevel(ch.User(self._currentname)) == 2:
            self._sendCommand("removemod", user.name)

    def flag(self, message):
        """
        Flag a message.

        @type message: Message
        @param message: message to flag
        """
        self._sendCommand("g_flag", message.msgid)

    def flagUser(self, user):
        """
        Flag a user.

        @type user: User
        @param user: user to flag

        @rtype: bool
        @return: whether a message to flag was found
        """
        msg = self.getLastMessage(user)
        if msg:
            self.flag(msg)
            return True
        return False

    def deleteMessage(self, message):
        """
        Delete a message. (Moderator only)

        @type message: Message
        @param message: message to delete
        """
        if self.getLevel(self.user) > 0:
            self._sendCommand("delmsg", message.msgid)

    def deleteUser(self, user):
        """
        Delete a message. (Moderator only)

        @type user: User
        @param user: delete user's last message
        """
        if self.getLevel(self.user) > 0:
            msg = self.getLastMessage(user)
            if msg:
                self._sendCommand("delmsg", msg.msgid)
            return True
        return False

    def delete(self, message):
        """
        compatibility wrapper for deleteMessage
        """
        print("[obsolete] the delete function is obsolete, please use deleteMessage")
        return self.deleteMessage(message)

    def rawClearUser(self, unid, ip, user):
        self._sendCommand("delallmsg", unid, ip, user)

    def clearUser(self, user):
        """
        Clear all of a user's messages. (Moderator only)

        @type user: User
        @param user: user to delete messages of

        @rtype: bool
        @return: whether a message to delete was found
        """
        if self.getLevel(self.user) > 0:
            msg = self.getLastMessage(user)
            if msg:
                if msg.user.name[0] in ["!", "#"]:
                    self.rawClearUser(msg.unid, msg.ip, "")
                else:
                    self.rawClearUser(msg.unid, msg.ip, msg.user.name)
                return True
        return False

    def clearall(self):
        """Clear all messages. (Owner only)"""
        if self.getLevel(self.user) == 2:
            self._sendCommand("clearall")

    def rawBan(self, name, ip, unid):
        """
        Execute the block command using specified arguments.
        (For advanced usage)

        @type name: str
        @param name: name
        @type ip: str
        @param ip: ip address
        @type unid: str
        @param unid: unid
        """
        self._sendCommand("block", unid, ip, name)

    def ban(self, msg):
        """
        Ban a message's sender. (Moderator only)

        @type msg: Message
        @param msg: message to ban sender of
        """
        if self.getLevel(self.user) > 0:
            self.rawBan(msg.user.name, msg.ip, msg.unid)

    def banUser(self, user):
        """
        Ban a user. (Moderator only)

        @type user: User
        @param user: user to ban

        @rtype: bool
        @return: whether a message to ban the user was found
        """
        msg = self.getLastMessage(user)
        if msg:
            self.ban(msg)
            return True
        return False

    def requestBanlist(self):
        """Request an updated banlist."""
        self._sendCommand("blocklist", "block", "", "next", "500")

    def requestUnBanlist(self):
        """Request an updated banlist."""
        self._sendCommand("blocklist", "unblock", "", "next", "500")

    def rawUnban(self, name, ip, unid):
        """
        Execute the unblock command using specified arguments.
        (For advanced usage)

        @type name: str
        @param name: name
        @type ip: str
        @param ip: ip address
        @type unid: str
        @param unid: unid
        """
        self._sendCommand("removeblock", unid, ip, name)

    def unban(self, user):
        """
        Unban a user. (Moderator only)

        @type user: User
        @param user: user to unban

        @rtype: bool
        @return: whether it succeeded
        """
        rec = self._getBanRecord(user)
        if rec:
            self.rawUnban(rec["target"].name, rec["ip"], rec["unid"])
            return True
        else:
            return False

    ####
    # Util
    ####
    def _getBanRecord(self, user):
        if user in self._banlist:
            return self._banlist[user]
        return None

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

    def getLevel(self, user):
        """get the level of user in a room"""
        if user == self._owner:
            return 2
        if user.name in self.modNames:
            return 1
        return 0

    def getPerms(self, user):
        return self._mods[user]

    def getLastMessage(self, user=None):
        """get last message said by user in a room"""
        if user:
            try:
                i = 1
                while True:
                    msg = self._history[-i]
                    if msg.user == user:
                        return msg
                    i += 1
            except IndexError:
                return None
        else:
            try:
                return self._history[-1]
            except IndexError:
                return None
        return None

    def findUser(self, name):
        """check if user is in the room

        return User(name) if name in room else None
        """
        name = name.lower()
        ul = self._userlist
        udi = dict(zip([u.name for u in ul], ul))
        cname = None
        for n in udi.keys():
            if name in n:
                if cname:
                    return None  # ambiguous!!
                cname = n
        if cname:
            return udi[cname]
        else:
            return None

    ####
    # History
    ####
    def _addHistory(self, msg):
        """
        Add a message to history.

        @type msg: Message
        @param msg: message
        """
        self._history.append(msg)
        if len(self._history) > self.mgr._maxHistoryLength:
            rest = self._history[:-self.mgr._maxHistoryLength]
            self._history = self._history[-self.mgr._maxHistoryLength:]
            for msg in rest:
                msg.detach()

    def __repr__(self):
        return "<Room: %s>" % self.name
