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
# Message class
################################################################
# noinspection PyProtectedMember
class Message:
    """Class that represents a message."""

    ####
    # Attach/detach
    ####
    def attach(self, room, msgid):
        """
        Attach the Message to a message id.

        @type room: Room
        @param room: room where the message is receive

        @type msgid: str
        @param msgid: message id
        """
        if self._msgid is None:
            self._room = room
            self._msgid = msgid
            self._room._msgs[msgid] = self

    def detach(self):
        """Detach the Message."""
        if self._msgid is not None and self._msgid in self._room._msgs:
            del self._room._msgs[self._msgid]
            self._msgid = None

    def delete(self):
        self._room.deleteMessage(self)

    ####
    # Init
    ####
    def __init__(self, **kw):
        """init, don't overwrite"""
        self._msgid = None
        self._time = None
        self._user = None
        self._body = None
        self._room = None
        self._raw = ""
        self._ip = None
        self._channel = ""
        self._unid = ""
        self._puid = ""
        self._nameColor = "000"
        self._fontSize = 12
        self._fontFace = "0"
        self._fontColor = "000"
        for attr, val in kw.items():
            if val is None:
                continue
            setattr(self, "_" + attr, val)

    ####
    # Properties
    ####
    @property
    def msgid(self):
        return self._msgid

    @property
    def time(self):
        return self._time

    @property
    def user(self):
        return self._user

    @property
    def body(self):
        return self._body

    @property
    def ip(self):
        return self._ip

    @property
    def channel(self):
        return self._channel

    @property
    def fontColor(self):
        return self._fontColor

    @property
    def fontFace(self):
        return self._fontFace

    @property
    def fontSize(self):
        return self._fontSize

    @property
    def nameColor(self):
        return self._nameColor

    @property
    def room(self):
        return self._room

    @property
    def raw(self):
        return self._raw

    @property
    def unid(self):
        return self._unid

    @property
    def puid(self):
        return self._puid

    @property
    def nid(self):
        return self._puid
