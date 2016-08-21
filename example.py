#!/usr/bin/python
import ch
import ch.precheck

if __debug__:
    import warnings
    warnings.simplefilter("always")


class TestBot(ch.roommanager.RoomManager, metaclass=ch.precheck.SignatureCheckerMeta):
    def onConnect(self, room):
        print("Connected to " + room.name)

    def onReconnect(self, room):
        print("Reconnected to " + room.name)

    def onDisconnect(self, room):
        print("Disconnected from " + room.name)

    def onMessage(self, room, user, message):
        print(user.name + ': ' + message.body)

        # channel white, default if channel arg isn't pass
        #   ch.Channel.White or "0"
        if message.body.startswith("!a"):
            room.message("AAAAAAAAAAAAAA", channel=ch.common.Channel.White)

        # channel red
        #  ch.Channel.Red or "256"
        if message.body.startswith("!b"):
            room.message("BBBBBBBBBBBBBB", channel=ch.common.Channel.Red)

        # channel blue
        # ch.Channel.Blue or "2048"
        if message.body.startswith("!c"):
            room.message("CCCCCCCCCCCCCC", channel=ch.common.Channel.Blue)

        # channel mod
        # ch.Channel.Mod or Mod = "32768"
        if message.body.startswith("!d"):
            room.message("DDDDDDDDDDDDDD", channel=ch.common.Channel.Mod)

    def onFloodBan(self, room, seconds):
        print("You are flood banned in " + room.name)

    def onPMMessage(self, pm, user, body):
        print('PM: ' + user.name + ': ' + body)
        pm.message(user, body)  # echo

if __name__ == "__main__":
    TestBot.easy_start()
