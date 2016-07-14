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
# import asyncio
import random
import html
import re

# import sys
import enum

################################################################
# Debug stuff
################################################################
debug = False


################################################################
# Constants
################################################################
class Channel:
    White = "0"
    Red = "256"
    Blue = "2048"
    Mod = "32768"


class Userlist(enum.IntEnum):
    Recent = 0
    All = 1


class BigMessage(enum.IntEnum):
    Multiple = 0
    Cut = 1


################################################################
# Perms stuff
################################################################

class Perms(enum.IntEnum):
    deleted = 1
    edit_mods = 2
    edit_mod_visibility = 4
    edit_bw = 8
    edit_restrictions = 16
    edit_group = 32
    see_counter = 64
    see_mod_channel = 128
    see_mod_actions = 256
    edit_nlp = 512
    edit_gp_annc = 1024
    no_sending_limitations = 8192
    see_ips = 16384
    close_group = 32768
    can_broadcast = 65536
    should_not_be_logged_mod_icon_vis = 131072
    is_staff = 262144
    should_not_be_logged_staff_icon_vis = 524288


# really ugly and hackish stuff
class _Perms:
    # noinspection PyPep8Naming
    class _internal:
        def __getattr__(self, val):
            if hasattr(Perms, val):
                return bool(self._perms.perm & Perms[val])

        def __init__(self, _perms):
            self._perms = _perms

    def __init__(self, perm):
        self.perm = perm
        self.perms = self._internal(self)


################################################################
# Tagserver stuff
################################################################
specials = {'mitvcanal': 56, 'animeultimacom': 34, 'cricket365live': 21, 'pokemonepisodeorg': 22, 'animelinkz': 20,
            'sport24lt': 56, 'narutowire': 10, 'watchanimeonn': 22, 'cricvid-hitcric-': 51, 'narutochatt': 70,
            'leeplarp': 27, 'stream2watch3': 56, 'ttvsports': 56, 'ver-anime': 8, 'vipstand': 21, 'eafangames': 56,
            'soccerjumbo': 21, 'myfoxdfw': 67, 'kiiiikiii': 21, 'de-livechat': 5, 'rgsmotrisport': 51,
            'dbzepisodeorg': 10, 'watch-dragonball': 8, 'peliculas-flv': 69, 'tvanimefreak': 54, 'tvtvanimefreak': 54}
tsweights = [['5', 75], ['6', 75], ['7', 75], ['8', 75], ['16', 75], ['17', 75], ['18', 75], ['9', 95], ['11', 95],
             ['12', 95], ['13', 95], ['14', 95], ['15', 95], ['19', 110], ['23', 110], ['24', 110], ['25', 110],
             ['26', 110], ['28', 104], ['29', 104], ['30', 104], ['31', 104], ['32', 104], ['33', 104], ['35', 101],
             ['36', 101], ['37', 101], ['38', 101], ['39', 101], ['40', 101], ['41', 101], ['42', 101], ['43', 101],
             ['44', 101], ['45', 101], ['46', 101], ['47', 101], ['48', 101], ['49', 101], ['50', 101], ['52', 110],
             ['53', 110], ['55', 110], ['57', 110], ['58', 110], ['59', 110], ['60', 110], ['61', 110], ['62', 110],
             ['63', 110], ['64', 110], ['65', 110], ['66', 110], ['68', 95], ['71', 116], ['72', 116], ['73', 116],
             ['74', 116], ['75', 116], ['76', 116], ['77', 116], ['78', 116], ['79', 116], ['80', 116], ['81', 116],
             ['82', 116], ['83', 116], ['84', 116]]

wgts = []

maxnum = sum(l[1] for l in tsweights)
cumfreq = 0
for nwgt in tsweights:
    cumfreq += nwgt[1] / maxnum
    wgts.append((cumfreq, nwgt[0]))


# noinspection PyPep8Naming
def getServerNum(group):
    group = group.replace("_", "q")
    group = group.replace("-", "q")
    lnv = int(group[6:9] or 'rs', 36)
    num = (int(group[:5], 36) % lnv) / lnv
    for wgt, s in wgts:
        if num <= wgt:
            return s


# noinspection PyPep8Naming
def getServer(group):
    """
      Get the server host for a certain room.

      @type group: str
      @param group: room name

      @rtype: str
      @return: the server's hostname
      """
    sn = specials.get(group) or getServerNum(group)
    return "s" + str(sn) + ".chatango.com"


################################################################
# Uid
################################################################
def _genUid():
    """
  generate a uid
  """
    return str(random.randrange(10 ** 15, 10 ** 16))


################################################################
# Message stuff
################################################################
def _clean_message(msg):
    """
  Clean a message and return the message, n tag and f tag.

  @type msg: str
  @param msg: the message

  @rtype: str, str, str
  @returns: cleaned message, n tag contents, f tag contents
  """
    n = re.search("<n(.*?)/>", msg)
    if n:
        n = n.group(1)
    f = re.search("<f(.*?)>", msg)
    if f:
        f = f.group(1)
    msg = re.sub("<n.*?/>", "", msg)
    msg = re.sub("<f.*?>", "", msg)
    msg = _strip_html(msg)
    msg = html.unescape(msg)
    return msg, n, f


def _strip_html(msg):
    """Strip HTML."""
    li = msg.split("<")
    if len(li) == 1:
        return li[0]
    else:
        ret = list()
        for data in li:
            data = data.split(">", 1)
            if len(data) == 1:
                ret.append(data[0])
            elif len(data) == 2:
                ret.append(data[1])
        return "".join(ret)


def _parseNameColor(n):
    """This just returns its argument, should return the name color."""
    # probably is already the name
    return n


# noinspection PyBroadException
def _parseFont(f):
    """Parses the contents of a f tag and returns color, face and size."""
    # ' xSZCOL="FONT"'
    try:  # TODO: remove quick hack
        sizecolor, fontface = f.split("=", 1)
        sizecolor = sizecolor.strip()
        size = int(sizecolor[1:3])
        col = sizecolor[3:6]
        if col == "":
            col = None
        face = f.split("\"", 2)[1]
        return col, face, size
    except:
        return None, None, None


################################################################
# Anon id
################################################################
def _getAnonId(n, ssid):
    """Gets the anon's id."""
    if n is None:
        n = "5504"
    try:
        return "".join("%d" % (int(ssid[i+4])+int(n[i]) % 10) for i in range(4))
    except ValueError:
        return "NNNN"


# noinspection PyPep8
from ch.pm import PM
# noinspection PyPep8
from ch.anonpm import ANON_PM
# noinspection PyPep8
from ch.room import Room
# noinspection PyPep8
from ch.roommanager import RoomManager
# noinspection PyPep8
from ch.user import User
# noinspection PyPep8
from ch.message import Message
