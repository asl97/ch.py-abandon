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
import ch


################################################################
# User factory
################################################################
_users = dict()


def User(name, **kw):
    if not name:
        return

    lname = name.lower()

    user = _users.get(lname)
    if not user:
        user = _User(name)
        _users[lname] = user

    if kw:
        user.update(**kw)

    return user


class _User:
    """Class that represents a user."""

    ####
    # Init
    ####
    def __init__(self, name):
        self.name = name
        self.puid = None
        self.puids = set()
        self.ip = None
        self.ips = set()
        self.perms = dict()
        self.room = None
        self.sids = dict()
        self.msgs = list()
        self.nameColor = "000"
        self.fontSize = 12
        self.fontFace = "0"
        self.fontColor = "000"
        self.mbg = False
        self.mrec = False

    ####
    # Update Handler
    ####
    def update(self, **kw):
        for attr, val in kw.items():
            if val is None:
                continue
            if hasattr(self, "_h_" + attr):
                getattr(self, "_h_" + attr)(val)
            else:
                setattr(self, attr, val)

    def _h_ip(self, val):
        self.ip = val
        self.ips.add(val)

    def _h_puid(self, val):
        self.puid = val
        self.puids.add(val)

    def _h_perm(self, val):
        self.perms[val[0]] = ch.common.Perm(val[1])

    def _h_participant(self, val):
        if val[0] == '1':  # join
            if val[1] not in self.sids:
                self.sids[val[1]] = set()
            self.sids[val[1]].add(val[2])
        elif val[0] == '0':  # leave
            if val[1] in self.sids:
                self.sids[val[1]].remove(val[2])
                if not self.sids[val[1]]:
                    del self.sids[val[1]]

    ####
    # Properties
    ####
    @property
    def sessionids(self):
        return set.union(*self.sids.values())

    @property
    def rooms(self):
        return list(self.sids.keys())

    @property
    def roomNames(self):
        return [room.name for room in self.sids.keys()]

    ####
    # Util
    ####

    def getPerm(self, room):
        return self.perms[room].perm

    def getPerms(self, room):
        return self.perms[room].perms

    ####
    # Repr
    ####
    def __repr__(self):
        return "<User: %s>" % self.name
