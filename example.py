#!/usr/bin/python
import ch


class TestBot(ch.roommanager.RoomManager):
    def onConnect(self, room):
        print("Connected to " + room.name)

    def onReconnect(self, room):
        print("Reconnected to " + room.name)

    def onDisconnect(self, room):
        print("Disconnected from " + room.name)

    def onMessage(self, room, user, message):
        # Use with PsyfrBot framework? :3
        self.safePrint(user.name + ': ' + message.body)

        # channel white, default if channel arg isn't pass
        #   ch.Channel.White or "0"
        if message.body.startswith("!a"):
            room.message("AAAAAAAAAAAAAA", channel=ch.Channel.White)

        # channel red
        #  ch.Channel.Red or "256"
        if message.body.startswith("!b"):
            room.message("BBBBBBBBBBBBBB", channel=ch.Channel.Red)

        # channel blue
        # ch.Channel.Blue or "2048"
        if message.body.startswith("!c"):
            room.message("CCCCCCCCCCCCCC", channel=ch.Channel.Blue)

        # channel mod
        # ch.Channel.Mod or Mod = "32768"
        if message.body.startswith("!d"):
            room.message("DDDDDDDDDDDDDD", channel=ch.Channel.Mod)

    def onFloodBan(self, room):
        print("You are flood banned in " + room.name)

    def onPMMessage(self, pm, user, body):
        self.safePrint('PM: ' + user.name + ': ' + body)
        pm.message(user, body)  # echo


if __name__ == "__main__":
    TestBot.easy_start()
