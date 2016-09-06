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


# noinspection PyMethodMayBeStatic
class BotCallback:
    ####
    # Virtual methods
    ####
    def onInit(self):
        """Called on init."""
        pass

    def onFinishStartup(self):
        """Called at the end of startup"""
        pass

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

    def onLogin(self, room):
        """
        Called on login.

        @type room: Room
        @param room: room where the event occurred
        """
        pass

    def onLogout(self, room):
        """
        Called on logout.

        @type room: Room
        @param room: room where the event occurred
        """
        pass

    def onFloodBan(self, room, seconds):
        """
        Called when either flood banned or flagged.

        @type room: Room
        @param room: room where the event occurred
        @type seconds: int
        @param seconds: temporary ban duration in number of seconds
        """
        pass

    def onFloodBanRepeat(self, room, seconds):
        """
        Called when trying to send something when floodbanned.

        @type room: Room
        @param room: room where the event occurred
        @type seconds: int
        @param seconds: temporary ban duration in number of seconds
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

    def onGotMoreHistory(self, room):
        """
        Called when finish getting more message from history.

        @type room: Room
        @param room: room where the event occurred
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
        @type body: str
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
        @type body: str
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


################################################################
# RoomManager class
################################################################
class RoomManager(BotCallback):
    """Class that manages multiple connections."""
    ####
    # Config
    ####
    Room = ch.Room
    PM = ch.PM
    PMHost = "c1.chatango.com"
    PMPort = 5222
    TimerResolution = 0.2  # at least x second per tick
    pingDelay = 20
    userlistMode = ch.common.Userlist.Recent
    userlistUnique = True
    userlistMemory = 50
    userlistEventUnique = False
    tooBigMessage = ch.common.BigMessage.Multiple
    maxLength = 700
    maxHistoryLength = 150

    ####
    # Init
    ####
    def __init__(self, name=None, password=None, pm=True):
        self.name = name
        self.password = password
        self.running = False
        self.tasks = set()
        self.rooms = dict()
        self.rooms_queue = queue.Queue()
        self.sock_write_queue = queue.Queue()
        self.tick_thread = None
        self.send_thread = None
        self.recv_thread = None
        self.join_thread = None
        self.dummy_con = ch.common.DummyConnection()
        if pm:
            if self.password:
                self.pm = self.PM(mgr=self)
            else:
                self.pm = self.ANON_PM(mgr=self)
        else:
            self.pm = None

    ####
    # Util
    ####
    def write(self, room, data):
        self.sock_write_queue.put((room.sock, data))

    def callEvent(self, room, evt, *args, **kw):
        getattr(self, evt)(room, *args, **kw)
        self.onEventCalled(room, evt, *args, **kw)

    def getConnections(self):
        li = list(self.rooms.values())
        if self.pm:
            li.extend(self.pm.getConnections())
        li.append(self.dummy_con)
        return {c.sock: c for c in li if c.sock is not None}

    def start_threads(self):
        self.tick_thread = threading.Thread(target=self.tick_worker, name='tick_worker')
        self.tick_thread.start()
        self.send_thread = threading.Thread(target=self.send_worker, name='send_worker')
        self.send_thread.start()
        self.recv_thread = threading.Thread(target=self.recv_worker, name='recv_worker')
        self.recv_thread.start()
        self.join_thread = threading.Thread(target=self.join_worker, name='join_worker', daemon=True)
        self.join_thread.start()

    ####
    # Main
    ####
    def main(self):
        self.onInit()
        self.running = True
        self.start_threads()
        self.onFinishStartup()

    @ch.common.stop_on_error
    def tick_worker(self):
        while self.running:
            self._tick()

    @ch.common.stop_on_error
    def send_worker(self):
        for sock, data in iter(self.sock_write_queue.get, None):
            # print(data)
            try:
                sock.sendall(data)
            except OSError:
                pass

    @ch.common.stop_on_error
    def recv_worker(self):
        while self.running:
            conns = self.getConnections()
            rd, wr, sp = select.select(conns, [], [])
            for sock in rd:
                con = conns[sock]
                try:
                    data = sock.recv(1024)
                    if len(data) > 0:
                        con.feed(data)
                    else:
                        con.disconnect()
                except socket.error:
                    pass

    @ch.common.stop_on_error
    def join_worker(self):
        for room, callback in iter(self.rooms_queue.get, None):
            con = self.Room(room, mgr=self)
            self.rooms[room] = con
            callback(room)
            self.dummy_con.notify()

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
        if rooms is None:
            rooms = str(input("Room names separated by semicolons: ")).split(";")
        if len(rooms) == 1 and rooms[0] == "":
            rooms = []
        if name is None:
            name = str(input("User name: "))
        if name == "":
            name = None
        if password is None:
            password = str(input("User password: "))
        if password == "":
            password = None
        self = cls(name, password, pm=pm)
        for room in rooms:
            self.joinRoom(room)
        self.main()

    def stop(self):
        self.running = False
        for conn in self.getConnections().values():
            conn.disconnect()
        self.sock_write_queue.put(None)
        self.rooms_queue.put(None)
        self.dummy_con.notify()

    ####
    # Properties
    ####
    @property
    def user(self):
        return ch.User(self.name)

    @property
    def roomNames(self):
        return set(self.rooms)

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
        for task in set(self.tasks):
            if task.target <= now:
                task.func(*task.args, **task.kw)
                if task.isInterval:
                    task.target = now + task.timeout
                else:
                    self.tasks.remove(task)

        time.sleep(self.TimerResolution)

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
        self.tasks.add(task)
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
        self.tasks.add(task)
        return task

    def removeTask(self, task):
        """
        Cancel a task.

        @type task: _Task
        @param task: task to cancel
        """
        self.tasks.remove(task)

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
        thread = threading.Thread(target=self.delayCallback, name='deferred thread',
                                  args=(callback, func) + args, kwargs=kw, daemon=True)
        thread.start()

    def delayCallback(self, callback, func, *args, **kw):
        self.setTimeout(0, callback, func(*args, **kw))

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
        if room not in self.rooms:
            self.rooms_queue.put((room, callback))

    def leaveRoom(self, room):
        """
        Leave a room.

        @type room: str
        @param room: room to leave
        """
        room = room.lower()
        if room in self.rooms:
            con = self.rooms[room]
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
        return self.rooms.get(room)

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
        self.user._fontSize = min(max(size, 9), 22)
