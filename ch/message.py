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
class Message:
    """Class that represents a message."""

    ####
    # Attach/detach
    ####
    def attach(self, mid):
        """
        Attach the Message to a message id.

        @type mid: str
        @param mid: message id
        """
        if self.mid is None:
            self.mid = mid
            self.room.msgs[mid] = self

    def detach(self):
        """Detach the Message."""
        if self.mid is not None and self.mid in self.room.msgs:
            del self.room.msgs[self.mid]
            self.mid = None

    def delete(self):
        self.room.deleteMessage(self)

    ####
    # Init
    ####
    def __init__(self, **kw):
        """init, don't overwrite"""
        self.mid = None
        self.time = None
        self.user = None
        self.body = None
        self.room = None
        self.raw = ""
        self.ip = None
        self.channel = ""
        self.mid = ""
        self.puid = ""
        self.nameColor = "000"
        self.fontSize = 12
        self.fontFace = "0"
        self.fontColor = "000"
        for attr, val in kw.items():
            if val is None:
                continue
            setattr(self, attr, val)
