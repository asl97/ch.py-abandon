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
import html

import ch


################################################################
# Room class
################################################################
# noinspection PyPep8Naming
class Room:
    """Manages a connection with a Chatango room."""

    ####
    # Init
    ####
    def __init__(self, room, uid=None, server=None, port=None, mgr=None):
        """init, don't overwrite"""
        # Basic stuff
        self.name = room
        self.server = server or ch.getServer(room)
        self.port = port or 443
        self.mgr = mgr

        # Under the hood
        self.user = self.mgr.user
        self.connected = False
        self.reconnecting = False
        self.uid = uid or ch.genUid()
        self.n = "000"
        self.logged = False
        self.rbuf = ""
        self.wbuf = b""
        self.wlockbuf = b""
        self.owner = None
        self.mods = dict()
        self.mqueue = dict()
        self.history = list()
        self.userlist = list()
        self.connectAmmount = 0
        self.premium = False
        self.userCount = 0
        self.sock = None
        self.pingTask = None
        self.botname = None
        self.currentname = None
        self.users = dict()
        self.msgs = dict()
        self.i_log = list()
        self.wlock = False
        self.silent = False
        self.banlist = dict()
        self.unbanlist = dict()
        self.sendCommand = self._firstSendCommand
        self.write = self._writeUnlocked
        self.more = True
        self.more_i = "0"
        self.participant_lock = True
        self.participant_queue = list()
        self.process = self._process

        # Inited vars
        if self.mgr:
            self._connect()

    ####
    # Received Commands
    ####
    def _rcmd_ok(self, owner, uid, success, name, ok_time, ip, mods, _):
        self.uid = uid
        self.puid = uid[0:8]
        self.ip = ip
        # if no name, join room as anon and no password
        if success == "N" and self.mgr.password is None and self.mgr.name is None:
            n = ok_time.rsplit('.', 1)[0][-4:]
            name = "!anon" + ch.getAnonId(n, self.puid)
            self.n = n
            self.user = ch.User(name)
            self.user.nameColor = n
        # if got name, join room as name and no password
        elif success == "N" and self.mgr.password is None:
            self.sendCommand("blogin", self.mgr.name)
            self.user = ch.User("#"+name)
        # if got password but fail to login
        elif success != "M":  # unsuccessful login
            self._callEvent("onLoginFail")
            self.disconnect()
        else:
            self.logged = True
            self.user = ch.User(name)

        self.owner = ch.User(
            name=owner,
            perm=(self.name, 1048575)
        )

        self.mods = dict()
        if mods:
            for x in mods.split(";"):
                name, perm = x.split(",")
                self.mods[ch.User(name=name, perm=(self.name, int(perm)))] = perm

        self.i_log = list()

    def _rcmd_denied(self):
        self._disconnect()
        self._callEvent("onConnectFail")

    def _rcmd_inited(self):
        self.sendCommand("g_participants")
        self.sendCommand("getpremium", "1")
        self.requestBanlist()
        self.requestUnBanlist()
        if self.connectAmmount == 0:
            self._callEvent("onConnect")
            for msg in reversed(self.i_log):
                user = msg.user
                self._callEvent("onHistoryMessage", user, msg)
                self._addHistory(msg)
            self.i_log = list()
        else:
            self._callEvent("onReconnect")
        self.connectAmmount += 1
        self._setWriteLock(False)

    def _rcmd_premium(self, _, ptime):
        ptime = float(ptime)
        if ptime > time.time():
            self.premium = ptime
            if self.user.mbg:
                self.setBgMode(1)
            if self.user.mrec:
                self.setRecordingMode(1)
        else:
            self.premium = False

    def _rcmd_mods(self, *args):
        premods = set(self.mods)
        self.mods = dict()
        for x in args:
            perm = int(x.split(",")[1])
            self.mods[ch.User(name=x.split(",")[0], perm=(self.name, perm))] = perm
        mods = set(self.mods)
        for user in mods - premods:  # modded
            self._callEvent("onModAdd", user)
        for user in premods - mods:  # demodded
            self._callEvent("onModRemove", user)
        self._callEvent("onModChange")

    def _rcmd_b(self, mtime, name, anon_name, puid, mid, i, ip, channel, _, *rawmsgs):
        mtime = float(mtime)
        rawmsg = ":".join(rawmsgs)
        msg, n, f = ch.clean_message(rawmsg)
        if name == "":
            nameColor = None
            name = "#" + (anon_name or "!anon" + ch.getAnonId(n, puid))
        else:
            nameColor = ch.parseNameColor(n)

        if f:
            fontColor, fontFace, fontSize = ch.parseFont(f)
        else:
            fontColor, fontFace, fontSize = None, None, None

        user = ch.User(
            name=name,
            puid=puid,
            ip=ip,
            nameColor=nameColor,
            fontColor=fontColor,
            fontFace=fontFace,
            fontSize=fontSize,
        )
        # Create an anonymous message and queue it because mid is unknown.
        msg = ch.Message(
            time=mtime,
            user=user,
            body=msg,
            raw=rawmsg,
            ip=ip,
            i=i,
            channel=channel,
            nameColor=nameColor,
            fontColor=fontColor,
            fontFace=fontFace,
            fontSize=fontSize,
            mid=mid,
            puid=puid,
            room=self
        )
        self.mqueue[i] = msg

    def _rcmd_u(self, i, mid):
        msg = self.mqueue.get(i, None)
        if msg:
            del self.mqueue[i]
            msg.attach(mid)
            self._addHistory(msg)
            self._callEvent("onMessage", msg.user, msg)

    def _rcmd_i(self, mtime, name, anon_name, puid, mid, i, ip, channel, _, *rawmsgs):
        mtime = float(mtime)
        rawmsg = ":".join(rawmsgs)
        msg, n, f = ch.clean_message(rawmsg)
        if name == "":
            nameColor = "000"
            name = "#" + (anon_name or "!anon" + ch.getAnonId(n, puid))
        else:
            nameColor = ch.parseNameColor(n)
        # Create an anonymous message and queue it because mid is unknown.
        if f:
            fontColor, fontFace, fontSize = ch.parseFont(f)
        else:
            fontColor, fontFace, fontSize = None, None, None
        user = ch.User(
            name=name,
            puid=puid,
            ip=ip,
            nameColor=nameColor,
            fontColor=fontColor,
            fontFace=fontFace,
            fontSize=fontSize,
        )
        msg = ch.Message(
            time=mtime,
            user=user,
            body=msg,
            raw=rawmsg,
            ip=ip,
            i=i,
            channel=channel,
            nameColor=nameColor,
            fontColor=fontColor,
            fontFace=fontFace,
            fontSize=fontSize,
            mid=mid,
            puid=puid,
            room=self
        )
        self.i_log.append(msg)

    @ch.common.resplit(";")
    def _rcmd_g_participants(self, *items):
        for item in items:
            sid, ctime, puid, name, anon_name, unknown = item.split(":")
            if name == "None":
                n = ctime.rsplit('.', 1)[0][-4:]
                name = "#" + (anon_name if anon_name != "None" else "!anon" + ch.getAnonId(n, puid))
            user = ch.User(
                name=name,
                room=self,
                puid=puid,
                participant=('1', self, sid)
            )
            self.userlist.append(user)
        self.participant_lock = False
        for participant in self.participant_queue:
            self._rcmd_participant(*participant)
        self._participant_queue = list()

    def _rcmd_participant(self, status, sid, puid, name, anon_name, unknown, ctime):
        if self.participant_lock:
            self.participant_queue.append((status, sid, puid, name, anon_name, unknown, ctime))
            return

        if name == "None":
            n = ctime.rsplit('.', 1)[0][-4:]
            name = "#" + (anon_name if anon_name != "None" else "!anon" + ch.getAnonId(n, puid))
        user = ch.User(
            name=name,
            puid=puid,
            participant=(status, self, sid)
        )

        if status == "0":  # leave
            self.userlist.remove(user)
            if not self.mgr.userlistEventUnique or user not in self.userlist:
                self._callEvent("onLeave", user, puid)
        else:  # join
            self.userlist.append(user)
            if not self.mgr.userlistEventUnique or user not in self.userlist:
                self._callEvent("onJoin", user, puid)

    def _rcmd_show_fw(self):
        self._callEvent("onFloodWarning")

    def _rcmd_show_tb(self, seconds):
        self._callEvent("onFloodBan", int(seconds))

    def _rcmd_tb(self, seconds):
        self._callEvent("onFloodBanRepeat", int(seconds))

    def _rcmd_delete(self, mid):
        msg = self.msgs.get(mid)
        if msg and msg in self.history:
            self.history.remove(msg)
            self._callEvent("onMessageDelete", msg.user, msg)
            msg.detach()

    def _rcmd_deleteall(self, args):
        for mid in args:
            self.delete(mid)

    def _rcmd_n(self, count):
        self.userCount = int(count, 16)
        self._callEvent("onUserCountChange")

    @ch.common.check_not_empty
    @ch.common.resplit(';')
    def _rcmd_blocklist(self, *items):
        self.banlist = dict()
        for item in items:
            mid, ip, banned, btime, banner = item.split(":")
            if banned == "":
                continue
            user = ch.User(banned)
            self.banlist[user] = {
                "mid": mid,
                "ip": ip,
                "target": user,
                "time": float(btime),
                "src": ch.User(banner)
            }
        self._callEvent("onBanlistUpdate")

    @ch.common.check_not_empty
    @ch.common.resplit(';')
    def _rcmd_unblocklist(self, *items):
        self.unbanlist = dict()
        for item in items:
            mid, ip, unbanned, ubtime, unbanner = item.split(":")
            if unbanned == "":
                continue
            user = ch.User(unbanned)
            self.unbanlist[user] = {
                "mid": mid,
                "ip": ip,
                "target": unbanned,
                "time": float(ubtime),
                "src": ch.User(unbanner)
            }
        self._callEvent("onUnBanlistUpdate")

    def _rcmd_blocked(self, mid, ip, banned, banner, btime):
        if banned == "":
            return
        target = ch.User(banned)
        user = ch.User(banner)
        self.banlist[target] = {"mid": mid, "ip": ip, "target": target, "time": float(btime), "src": user}
        self._callEvent("onBan", user, target)

    def _rcmd_unblocked(self, mid, ip, unbanned, unbanner, btime):
        if unbanned == "":
            return
        target = ch.User(unbanned)
        user = ch.User(unbanner)
        del self.banlist[target]
        self.unbanlist[user] = {"mid": mid, "ip": ip, "target": target, "time": float(btime), "src": user}
        self._callEvent("onUnban", user, target)

    def _rcmd_logoutok(self):
        self.logged = False
        self._callEvent("onLogout")

    def _rcmd_pwdok(self):
        self.logged = True
        self._callEvent("onLogin")

    def _rcmd_aliasok(self):
        pass

    def _rcmd_nomore(self):
        self.more = False

    def _rcmd_gotmore(self, i):
        self.more_i = str(int(i) + 1)
        for msg in reversed(self.i_log):
            user = msg.user
            self._callEvent("onHistoryMessage", user, msg)
            self._addHistory(msg)
        self.i_log = list()
        self._callEvent('onGotMoreHistory')

    ####
    # Connect/disconnect
    ####
    def _connect(self):
        """Connect to the server."""
        self.sock = socket.socket()
        self.sock.connect((self.server, self.port))
        self.sendCommand = self._firstSendCommand
        self.write = self._writeUnlocked
        self.participant_lock = True
        self.participant_queue = list()
        self.process = self._process
        self.wbuf = b""
        self._auth()
        self.pingTask = self.mgr.setInterval(self.mgr.pingDelay, self.ping)
        if not self.reconnecting:
            self.connected = True

    def reconnect(self):
        """Reconnect."""
        self._reconnect()

    def _reconnect(self):
        """Reconnect."""
        self.reconnecting = True
        if self.connected:
            self._disconnect()
        self.uid = ch.genUid()
        self._connect()
        self.reconnecting = False

    def disconnect(self):
        """Disconnect."""
        self._disconnect()
        self._callEvent("onDisconnect")

    def _disconnect(self):
        """Disconnect from the server."""
        if not self.reconnecting:
            self.connected = False
        for user in self.userlist:
            if self in user.sids:
                del user.sids[self]
        self.userlist = list()
        self.pingTask.cancel()
        self.sock.close()
        self.process = lambda x: x
        if not self.reconnecting:
            del self.mgr.rooms[self.name]

    def _auth(self):
        """Authenticate."""
        # login as name with password
        if self.mgr.name and self.mgr.password:
            self.sendCommand("bauth", self.name, self.uid, self.mgr.name, self.mgr.password)
            self.currentname = self.mgr.name
        # login as anon
        else:
            self.sendCommand("bauth", self.name, '', '', '')

        self._setWriteLock(True)

    ####
    # Properties
    ####
    @property
    def botName(self):
        if self.mgr.name and self.mgr.password:
            return self.mgr.name
        elif self.mgr.name and self.mgr.password is None:
            return "#" + self.mgr.name
        elif self.mgr.name is None:
            return self.botname

    @property
    def currentName(self):
        return self.currentname

    @property
    def userList(self):
        if self.mgr.userlistMode == ch.common.Userlist.Recent:
            ul = (x.user for x in self.history[-self.mgr.userlistMemory:])
        else:
            ul = self.userlist

        if self.mgr.userlistUnique:
            return list(set(ul))
        else:
            return ul

    @property
    def usernames(self):
        return [x.name for x in self.userlist]

    @property
    def ownerName(self):
        return self.owner.name

    @property
    def modNames(self):
        return [x.name for x in self.mods]

    @property
    def banList(self):
        return list(self.banlist.keys())

    @property
    def unBanList(self):
        return [[record["target"], record["src"]] for record in self.unbanlist.values()]

    ####
    # Feed/process
    ####
    def feed(self, data):
        """
        Feed data to the connection.

        @type data: bytes
        @param data: data to be fed
        """
        *foods, self.rbuf = (self.rbuf + data.decode('utf-8', errors="replace")).split("\x00")
        for food in foods:
            food = food.rstrip("\r\n")
            if food:
                self.process(food)

    def _process(self, data):
        """
        Process a command string.

        @type data: str
        @param data: the command string
        """
        self._callEvent("onRaw", data)
        cmd, *args = data.split(":")
        func = "_rcmd_"+cmd
        if hasattr(self, func):
            getattr(self, func)(*args)
        else:
            if __debug__:
                print("[unknown] data: " + str(data))

    ####
    # Commands
    ####
    def login(self, NAME, PASS=None):
        """login as a user or set a name in room"""
        if PASS:
            self.sendCommand("blogin", NAME, PASS)
        else:
            self.sendCommand("blogin", NAME)
        self.currentname = NAME

    def logout(self):
        """logout of user in a room"""
        self.sendCommand("blogout")
        self.currentname = self.botname

    def ping(self):
        """Send a ping."""
        self.sendCommand("")
        self._callEvent("onPing")

    def rawMessage(self, msg, channel="0"):
        """
        Send a message without n and f tags.

        @type msg: str
        @param msg: message

        @type channel: str
        @param channel: channel mode
        """
        if not self.silent:
            self.sendCommand("bm:tl2r", channel, msg)

    def formatMessage(self, msg):
        msg = "<n" + self.user.nameColor + "/>" + msg
        if self.logged:
            font_properties = "<f x%0.2i%s=\"%s\">" % (self.user.fontSize, self.user.fontColor, self.user.fontFace)
            if "\n" in msg:
                msg = msg.replace("\n", "</f></p><p>%s" % font_properties)
            msg = font_properties + msg
        return msg

    def message(self, msg, escape_html=True, channel="0"):
        """
        Send a message. (Use "\n" for new line)

        @type msg: str
        @param msg: message

        @type escape_html: bool
        @param escape_html: interpret message as html

        @type channel: str
        @param channel: channel mode
        """
        if msg is None:
            return
        msg = msg.rstrip()
        if escape_html:
            msg = html.escape(msg)
        if len(msg) > self.mgr.maxLength and self.mgr.tooBigMessage == ch.common.BigMessage.Cut:
            self.rawMessage(self.formatMessage(msg[:self.mgr.maxLength]), channel)
        else:
            while len(msg) > 0:
                sect, msg = msg[:self.mgr.maxLength], msg[self.mgr.maxLength:]
                self.rawMessage(self.formatMessage(sect), channel)

    def setBgMode(self, mode):
        """turn on/off bg"""
        self.sendCommand("msgbg", str(mode))

    def setRecordingMode(self, mode):
        """turn on/off rcecording"""
        self.sendCommand("msgmedia", str(mode))

    def addMod(self, user):
        """
        Add a moderator.

        @type user: User
        @param user: User to mod.
        """
        if self.getLevel(ch.User(self.currentname)) == 2:
            self.sendCommand("addmod", user.name)

    def removeMod(self, user):
        """
        Remove a moderator.

        @type user: User
        @param user: User to demod.
        """
        if self.getLevel(ch.User(self.currentname)) == 2:
            self.sendCommand("removemod", user.name)

    def flag(self, message):
        """
        Flag a message.

        @type message: Message
        @param message: message to flag
        """
        self.sendCommand("g_flag", message.mid)

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
            self.sendCommand("delmsg", message.mid)

    def deleteUser(self, user):
        """
        Delete a message. (Moderator only)

        @type user: User
        @param user: delete user's last message
        """
        if self.getLevel(self.user) > 0:
            msg = self.getLastMessage(user)
            if msg:
                self.sendCommand("delmsg", msg.mid)
            return True
        return False

    def delete(self, message):
        """
        compatibility wrapper for deleteMessage
        """
        print("[obsolete] the delete function is obsolete, please use deleteMessage")
        return self.deleteMessage(message)

    def rawClearUser(self, unid, ip, user):
        self.sendCommand("delallmsg", unid, ip, user)

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
            self.sendCommand("clearall")

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
        self.sendCommand("block", unid, ip, name)

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
        self.sendCommand("blocklist", "block", "", "next", "500")

    def requestUnBanlist(self):
        """Request an updated banlist."""
        self.sendCommand("blocklist", "unblock", "", "next", "500")

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
        self.sendCommand("removeblock", unid, ip, name)

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

    def get_more(self):
        if self.more:
            self.sendCommand('get_more', '20', self.more_i)

    ####
    # Util
    ####
    def _getBanRecord(self, user):
        return self.banlist.get(user)

    def _callEvent(self, evt, *args, **kw):
        self.mgr.callEvent(self, evt, *args, **kw)

    def _writeLocked(self, data):
        self.wlockbuf += data

    def _writeUnlocked(self, data):
        self.mgr.write(self, data)

    def _setWriteLock(self, lock):
        self.wlock = lock
        if self.wlock is False:
            self.write = self._writeUnlocked
            self.write(self.wlockbuf)
            self.wlockbuf = b""
        else:
            self.write = self._writeLocked

    def _firstSendCommand(self, *args):
        """
        Send a command.

        @type args: [str, str, ...]
        @param args: command and list of arguments
        """
        self.sendCommand = self._otherSendCommand
        self.write(":".join(args).encode() + b"\x00")

    def _otherSendCommand(self, *args):
        """
        Send a command.

        @type args: [str, str, ...]
        @param args: command and list of arguments
        """
        self.write(":".join(args).encode() + b"\r\n\x00")

    def getLevel(self, user):
        """get the level of user in a room"""
        if user == self.owner:
            return 2
        elif user in self.mods:
            return 1
        return 0

    def getPerms(self, user):
        return self.mods[user]

    def getLastMessage(self, user=None):
        """get last message said by user in a room"""
        for msg in self.history[::-1]:
            if not user or msg.user == user:
                return msg

    def findUser(self, name):
        """check if user is in the room

        return User(name) if name in room else None
        """
        name = name.lower()
        for user in self.userlist:
            if user.name == name:
                return user

    ####
    # History
    ####
    def _addHistory(self, msg):
        """
        Add a message to history.

        @type msg: Message
        @param msg: message
        """
        self.history.append(msg)
        if len(self.history) > self.mgr.maxHistoryLength:
            rest, self.history = self.history[:-self.mgr.maxHistoryLength], self.history[-self.mgr.maxHistoryLength:]
            for msg in rest:
                msg.detach()

    def __repr__(self):
        return "<Room: %s>" % self.name
