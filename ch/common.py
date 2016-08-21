import enum
import functools

################################################################
# Constants
################################################################
import socket


class StrEnum(str, enum.Enum):
    """Enum where members are also (and must be) strs"""


class Channel(StrEnum):
    White = "0"
    Red = "256"
    Blue = "2048"
    Mod = "32768"


class Nlp(enum.IntEnum):
    Spam = 2
    Short = 8
    Nonsense = 16


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


class Perm(int):
    def __getattr__(self, val):
        if val in Perms.__members__:
            return bool(self.perm & Perms[val])

    def __new__(cls, value=0):
        i = int.__new__(cls, value)
        i.perm = value
        return i


class DummyConnection:
    name = "#dummy"  # room can't start with '#' on chatango

    def __init__(self):
        self.sock_pair = socket.socketpair()
        self.sock = self.sock_pair[0]

    # noinspection PyUnusedLocal
    def recv(self, num):
        return self.sock_pair[0].recv(1)

    def notify(self):
        self.sock_pair[1].sendall(b'x')

    def feed(self, data):
        pass

    def disconnect(self):
        pass


def resplit(new, old=":"):
    def decorator(func):
        @functools.wraps(func)
        def internal(cls, *args):
            func(cls, *old.join(args).split(new))
        return internal
    return decorator


def check_not_empty(func):
    @functools.wraps(func)
    def internal(cls, *args):
        if any(args):
            func(cls, *args)
    return internal


def stop_on_error(func):
    @functools.wraps(func)
    def internal(cls, *args):
        try:
            func(cls, *args)
        except:
            cls.stop()
            raise
    return internal


def grouper(number):
    def decorator(func):
        @functools.wraps(func)
        def internal(cls, *args):
            func(cls, zip(*([iter(args)]*number)))
        return internal
    return decorator