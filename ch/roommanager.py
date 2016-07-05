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
import queue
import select
import socket
import threading
import time

import ch


################################################################
# RoomManager class
################################################################
# noinspection PyProtectedMember,PyMethodMayBeStatic,PyShadowingNames
class RoomManager:
    """Class that manages multiple connections."""
    ####
    # Config
    ####
    _Room = ch.Room
    _PM = ch.PM
    _ANON_PM = ch.ANON_PM
    _anonPMHost = "b1.chatango.com"
    _PMHost = "c1.chatango.com"
    _PMPort = 5222
    _TimerResolution = 0.2  # at least x second per tick
    _pingDelay = 20
    _userlistMode = ch.Userlist.Recent
    _userlistUnique = True
    _userlistMemory = 50
    _userlistEventUnique = False
    _tooBigMessage = ch.BigMessage.Multiple
    _maxLength = 1800
    _maxHistoryLength = 150

    ####
    # Init
    ####
    def __init__(self, name=None, password=None, pm=True):
        self._name = name
        self._password = password
        self._running = False
        self._tasks = set()
        self._rooms = dict()
        self._rooms_queue = queue.Queue()
        self._sock_write_queue = queue.Queue()
        self.tick_thread = None
        self.send_thread = None
        if pm:
            if self._password:
                self._pm = self._PM(mgr=self)
            else:
                self._pm = self._ANON_PM(mgr=self)
        else:
            self._pm = None

    ####
    # Join/leave
    ####
    def joinRoom(self, room, callback=lambda x: None):
        """
        Join a room or return None if already joined.

        @type room: str
        @param room: room to join

        @type callback: func
        @param callback: function to call with the room object
        """
        room = room.lower()
        if room not in self._rooms:
            self._rooms_queue.put((room, callback))

    def leaveRoom(self, room):
        """
        Leave a room.

        @type room: str
        @param room: room to leave
        """
        room = room.lower()
        if room in self._rooms:
            con = self._rooms[room]
            con.disconnect()

    def getRoom(self, room):
        """
        Get room with a name, or None if not connected to this room.

        @type room: str
        @param room: room

        @rtype: Room
        @return: the room
        """
        room = room.lower()
        if room in self._rooms:
            return self._rooms[room]
        else:
            return None

    ####
    # Properties
    ####
    @property
    def user(self):
        return ch.User(self._name)

    @property
    def name(self):
        return self._name

    @property
    def password(self):
        return self._password

    @property
    def rooms(self):
        return set(self._rooms.values())

    @property
    def roomNames(self):
        return set(self._rooms.keys())

    @property
    def pm(self):
        return self._pm

    ####
    # Virtual methods
    ####
    def onInit(self):
        """Called on init."""
        pass

    def safePrint(self, text):
        """Use this to safely print text with unicode"""
        while True:
            try:
                print(text)
                break
            except UnicodeEncodeError as ex:
                text = (text[0:ex.start] + '(unicode)' + text[ex.end:])

    def onConnect(self, room):
        """
        Called when connected to the room.

        @type room: Room
        @param room: room where the event occurred
        """
        pass

    def onReconnect(self, room):
        """
        Called when reconnected to the room.

        @type room: Room
        @param room: room where the event occurred
        """
        pass

    def onConnectFail(self, room):
        """
        Called when the connection failed.

        @type room: Room
        @param room: room where the event occurred
        """
        pass

    def onDisconnect(self, room):
        """
        Called when the client gets disconnected.

        @type room: Room
        @param room: room where the event occurred
        """
        pass

    def onLoginFail(self, room):
        """
        Called on login failure, disconnects after.

        @type room: Room
        @param room: room where the event occurred
        """
        pass

    def onFloodBan(self, room):
        """
        Called when either flood banned or flagged.

        @type room: Room
        @param room: room where the event occurred
        """
        pass

    def onFloodBanRepeat(self, room):
        """
        Called when trying to send something when floodbanned.

        @type room: Room
        @param room: room where the event occurred
        """
        pass

    def onFloodWarning(self, room):
        """
        Called when an overflow warning gets received.

        @type room: Room
        @param room: room where the event occurred
        """
        pass

    def onMessageDelete(self, room, user, message):
        """
        Called when a message gets deleted.

        @type room: Room
        @param room: room where the event occurred
        @type user: User
        @param user: owner of deleted message
        @type message: Message
        @param message: message that got deleted
        """
        pass

    def onModChange(self, room):
        """
        Called when the moderator list changes.

        @type room: Room
        @param room: room where the event occurred
        """
        pass

    def onModAdd(self, room, user):
        """
        Called when a moderator gets added.

        @type room: Room
        @param room: room where the event occurred

        @type user: User
        @param user: user who was added as mod
        """
        pass

    def onModRemove(self, room, user):
        """
        Called when a moderator gets removed.

        @type room: Room
        @param room: room where the event occurred

        @type user: User
        @param user: user who was added as mod
        """
        pass

    def onMessage(self, room, user, message):
        """
        Called when a message gets received.

        @type room: Room
        @param room: room where the event occurred
        @type user: User
        @param user: owner of message
        @type message: Message
        @param message: received message
        """
        pass

    def onHistoryMessage(self, room, user, message):
        """
        Called when a message gets received from history.

        @type room: Room
        @param room: room where the event occurred
        @type user: User
        @param user: owner of message
        @type message: Message
        @param message: the message that got added
        """
        pass

    def onJoin(self, room, user, puid):
        """
        Called when a user joins. Anonymous users get ignored here.

        @type room: Room
        @param room: room where the event occurred
        @type user: User
        @param user: the user that has joined
        @type puid: str
        @param puid: the user puid
        """
        pass

    def onLeave(self, room, user, puid):
        """
        Called when a user leaves. Anonymous users get ignored here.

        @type room: Room
        @param room: room where the event occurred
        @type user: User
        @param user: the user that has left
        @type puid: str
        @param puid: the user puid
        """
        pass

    def onRaw(self, room, raw):
        """
        Called before any command parsing occurs.

        @type room: Room
        @param room: room where the event occurred
        @type raw: str
        @param raw: raw command data
        """
        pass

    def onPing(self, room):
        """
        Called when a ping gets sent.

        @type room: Room
        @param room: room where the event occurred
        """
        pass

    def onUserCountChange(self, room):
        """
        Called when the user count changes.

        @type room: Room
        @param room: room where the event occurred
        """
        pass

    def onBan(self, room, user, target):
        """
        Called when a user gets banned.

        @type room: Room
        @param room: room where the event occurred
        @type user: User
        @param user: user that banned someone
        @type target: User
        @param target: user that got banned
        """
        pass

    def onUnban(self, room, user, target):
        """
        Called when a user gets unbanned.

        @type room: Room
        @param room: room where the event occurred
        @type user: User
        @param user: user that unbanned someone
        @type target: User
        @param target: user that got unbanned
        """
        pass

    def onBanlistUpdate(self, room):
        """
        Called when a banlist gets updated.

        @type room: Room
        @param room: room where the event occurred
        """
        pass

    def onUnBanlistUpdate(self, room):
        """
        Called when a unbanlist gets updated.

        @type room: Room
        @param room: room where the event occurred
        """
        pass

    def onPMConnect(self, pm):
        """
        Called when connected to the pm

        @type pm: PM
        @param pm: the pm
        """
        pass

    def onAnonPMDisconnect(self, pm, user):
        """
        Called when disconnected from the pm

        @type pm: PM
        @param pm: the pm

        @type user: User
        @param user: the user that was disconnected
        """
        pass

    def onPMDisconnect(self, pm):
        """
        Called when disconnected from the pm

        @type pm: PM
        @param pm: the pm
        """
        pass

    def onPMPing(self, pm):
        """
        Called when sending a ping to the pm

        @type pm: PM
        @param pm: the pm
        """
        pass

    def onPMMessage(self, pm, user, body):
        """
        Called when a message is received

        @type pm: PM
        @param pm: the pm
        @type user: User
        @param user: owner of message
        @type body: Message
        @param body: received message
        """
        pass

    def onPMOfflineMessage(self, pm, user, body):
        """
        Called when connected if a message is received while offline

        @type pm: PM
        @param pm: the pm
        @type user: User
        @param user: owner of message
        @type body: Message
        @param body: received message
        """
        pass

    def onPMContactlistReceive(self, pm):
        """
        Called when the contact list is received

        @type pm: PM
        @param pm: the pm
        """
        pass

    def onPMBlocklistReceive(self, pm):
        """
        Called when the block list is received

        @type pm: PM
        @param pm: the pm
        """
        pass

    def onPMContactAdd(self, pm, user):
        """
        Called when the contact added message is received

        @type pm: PM
        @param pm: the pm
        @type user: User
        @param user: the user that gotten added
        """
        pass

    def onPMContactRemove(self, pm, user):
        """
        Called when the contact remove message is received

        @type pm: PM
        @param pm: the pm
        @type user: User
        @param user: the user that gotten remove
        """
        pass

    def onPMBlock(self, pm, user):
        """
        Called when successfully block a user

        @type pm: PM
        @param pm: the pm
        @type user: User
        @param user: the user that gotten block
        """
        pass

    def onPMUnblock(self, pm, user):
        """
        Called when successfully unblock a user

        @type pm: PM
        @param pm: the pm
        @type user: User
        @param user: the user that gotten unblock
        """
        pass

    def onPMContactOnline(self, pm, user):
        """
        Called when a user from the contact come online

        @type pm: PM
        @param pm: the pm
        @type user: User
        @param user: the user that came online
        """
        pass

    def onPMContactOffline(self, pm, user):
        """
        Called when a user from the contact go offline

        @type pm: PM
        @param pm: the pm
        @type user: User
        @param user: the user that went offline
        """
        pass

    def onEventCalled(self, room, evt, *args, **kw):
        """
        Called on every room-based event.

        @type room: Room
        @param room: room where the event occurred
        @type evt: str
        @param evt: the event
        """
        pass

    ####
    # Deferring
    ####
    def deferToThread(self, callback, func, *args, **kw):
        """
        Defer a function to a thread and callback the return value.

        @type callback: function
        @param callback: function to call on completion

        @type func: function
        @param func: function to call

        @param args: arguments to get supplied to the callback
        @param kw: arguments to get supplied to the callback
        """

        def f(func, callback, *args, **kw):
            ret = func(*args, **kw)
            self.setTimeout(0, callback, ret)

        threading._start_new_thread(f, (func, callback) + args, kw)

    ####
    # Scheduling
    ####
    # noinspection PyPep8Naming
    class _Task:
        def __init__(self, mgr, isInterval, timeout, func, *args, **kw):
            self.mgr = mgr
            self.target = time.time() + timeout
            self.timeout = timeout
            self.func = func
            self.isInterval = isInterval
            self.args = args
            self.kw = kw

        def cancel(self):
            """Sugar for removeTask."""
            self.mgr.removeTask(self)

    def _tick(self):

        now = time.time()
        for task in set(self._tasks):
            if task.target <= now:
                task.func(*task.args, **task.kw)
                if task.isInterval:
                    task.target = now + task.timeout
                else:
                    self._tasks.remove(task)

        if not self._rooms_queue.empty():
            room, callback = self._rooms_queue.get()
            con = self._Room(room, mgr=self)
            self._rooms[room] = con
            callback(room)
        else:
            time.sleep(self._TimerResolution)

    def setTimeout(self, timeout, func, *args, **kw):
        """
        Call a function after at least timeout seconds with specified arguments.

        @type timeout: int
        @param timeout: timeout

        @type func: function
        @param func: function to call

        @rtype: _Task
        @return: object representing the task
        """
        task = self._Task(self, False, timeout, func, *args, **kw)
        self._tasks.add(task)
        return task

    def setInterval(self, timeout, func, *args, **kw):
        """
        Call a function at least every timeout seconds with specified arguments.

        @type timeout: int
        @param timeout: timeout
        @type func: function
        @param func: function to call

        @rtype: _Task
        @return: object representing the task
        """
        task = self._Task(self, True, timeout, func, *args, **kw)
        self._tasks.add(task)
        return task

    def removeTask(self, task):
        """
        Cancel a task.

        @type task: _Task
        @param task: task to cancel
        """
        self._tasks.remove(task)

    ####
    # Util
    ####
    def _write(self, room, data):
        self._sock_write_queue.put((room._sock, data))

    def getConnections(self):
        li = list(self._rooms.values())
        if self._pm:
            li.extend(self._pm.getConnections())
        return {c._sock: c for c in li if c._sock is not None}

    def start_threads(self):
        self.tick_thread = threading.Thread(target=self.tick_worker, name='tick_worker')
        self.tick_thread.start()
        self.send_thread = threading.Thread(target=self.send_worker, name='send_worker')
        self.send_thread.start()

    ####
    # Main
    ####
    def main(self):
        self.onInit()
        self._running = True
        self.start_threads()
        while self._running:
            conns = self.getConnections()
            rd, wr, sp = select.select(conns, [], [])
            for sock in rd:
                con = conns[sock]
                try:
                    data = sock.recv(1024)
                    if len(data) > 0:
                        con._feed(data)
                    else:
                        con.disconnect()
                except socket.error:
                    pass
            self._tick()

    def tick_worker(self):
        while self._running:
            self._tick()

    def send_worker(self):
        for sock, data in iter(self._sock_write_queue.get, None):
            sock.sendall(data)

    @classmethod
    def easy_start(cls, rooms=None, name=None, password=None, pm=True):
        """
        Prompts the user for missing info, then starts.

        @type rooms: list
        @param rooms: rooms to join

        @type name: str
        @param name: name to join as ("" = None, None = unspecified)

        @type password: str
        @param password: password to join with ("" = None, None = unspecified)

        @type pm: bool
        @param pm: whether to connect to pm
        """
        if not rooms:
            rooms = str(input("Room names separated by semicolons: ")).split(";")
        if len(rooms) == 1 and rooms[0] == "":
            rooms = []
        if not name:
            name = str(input("User name: "))
        if name == "":
            name = None
        if not password:
            password = str(input("User password: "))
        if password == "":
            password = None
        self = cls(name, password, pm=pm)
        for room in rooms:
            self.joinRoom(room)
        self.main()

    def stop(self):
        for conn in list(self._rooms.values()):
            conn.disconnect()
        self._sock_write_queue.put(None)
        self._running = False

    ####
    # Commands
    ####
    def enableBg(self):
        """Enable background if available."""
        self.user._mbg = True
        for room in self.rooms:
            room.setBgMode(1)

    def disableBg(self):
        """Disable background."""
        self.user._mbg = False
        for room in self.rooms:
            room.setBgMode(0)

    def enableRecording(self):
        """Enable recording if available."""
        self.user._mrec = True
        for room in self.rooms:
            room.setRecordingMode(1)

    def disableRecording(self):
        """Disable recording."""
        self.user._mrec = False
        for room in self.rooms:
            room.setRecordingMode(0)

    def setNameColor(self, color3x):
        """
        Set name color.

        @type color3x: str
        @param color3x: a 3-char RGB hex code for the color
        """
        self.user._nameColor = color3x

    def setFontColor(self, color3x):
        """
        Set font color.

        @type color3x: str
        @param color3x: a 3-char RGB hex code for the color
        """
        self.user._fontColor = color3x

    def setFontFace(self, face):
        """
        Set font face/family.

        @type face: str
        @param face: the font face
        """
        self.user._fontFace = face

    def setFontSize(self, size):
        """
        Set font size.

        @type size: int
        @param size: the font size (limited: 9 to 22)
        """
        if size < 9:
            size = 9
        if size > 22:
            size = 22
        self.user._fontSize = size
