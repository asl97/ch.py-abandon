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
# User class
################################################################
# noinspection PyProtectedMember,PyProtectedMember,PyUnusedLocal
class User:
    _users = dict()

    def __getattr__(self, key):
        return getattr(self.user, key)

    def __eq__(self, other):
        return self.user == getattr(other, "user", other)

    def __hash__(self):
        return hash(self.user)

    def __init__(self, name, *args, **kw):
        if not name:
            return
        name = name.lower()
        user = self._users.get(name)
        if not user:
            user = _User(name)
            self._users[name] = user

        self.user = user

        for attr, val in kw.items():
            if val is None:
                continue
            if hasattr(self, "_h_" + attr):
                getattr(self, "_h_" + attr)(val)
            else:
                setattr(user, "_" + attr, val)

    def _h_ip(self, val):
        self.user._ip = val
        self.user._ips.add(val)

    def _h_puid(self, val):
        self.user._puid = val
        self.user._puids.add(val)

    def _h_perm(self, val):
        self.user._perms[val[0]] = ch._Perms(val[1])

    def _h_participant(self, val):
        if val[0] == '1':  # join
            if val[1] not in self.user._sids:
                self.user._sids[val[1]] = set()
            self.user._sids[val[1]].add(val[2])
        elif val[0] == '0':  # leave
            if val[1] in self.user._sids:
                self.user._sids[val[1]].remove(val[2])
                if not self.user._sids[val[1]]:
                    del self.user._sids[val[1]]


class _User:
    """Class that represents a user."""

    ####
    # Init
    ####
    def __init__(self, name):
        self._name = name.lower()
        self._puid = None
        self._puids = set()
        self._ip = None
        self._ips = set()
        self._perms = dict()
        self._room = None
        self._sids = dict()
        self._msgs = list()
        self._nameColor = "000"
        self._fontSize = 12
        self._fontFace = "0"
        self._fontColor = "000"
        self._mbg = False
        self._mrec = False

    ####
    # Properties
    ####
    @property
    def name(self):
        return self._name

    @property
    def puid(self):
        return self._puid

    @property
    def puids(self):
        return self._puids

    @property
    def ip(self):
        return self._ip

    @property
    def ips(self):
        return self._ips

    @property
    def room(self):
        return self._room

    @property
    def sessionids(self):
        return set.union(*self._sids.values())

    @property
    def rooms(self):
        return list(self._sids.keys())

    @property
    def roomNames(self):
        return [room.name for room in self._sids.keys()]

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

    ####
    # Util
    ####

    def getPerm(self, room):
        return self._perms[room].perm

    def getPerms(self, room):
        return self._perms[room].perms

    ####
    # Repr
    ####
    def __repr__(self):
        return "<User: %s>" % self.name
