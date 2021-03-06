#!/usr/bin/env python
'''An IRC bot that listens on TCP port 4321 for messages delimited by \n.
Messages sent to it will be proxied through to IRC.'''
from twisted.words.protocols import irc
from twisted.internet import protocol, reactor

from settings import *

def message(string):
    '''Send a message to a twisted server listening on port 4321.
    It expects multiple messages to be separated with "\n".
    '''
    import socket
    print string
    host, port = 'localhost', 4321
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
        sock.send(string)
    except socket.error, exc:
        print "ERROR:", exc
    sock.close()

class SpewBot(irc.IRCClient):
    def _get_nickname(self):
        return self.factory.nickname
    nickname = property(_get_nickname)

    def register(self, nickname):
        if self.factory.password is not None:
            self.sendLine("PASS %s" % self.factory.password)
        self.setNick(nickname)
        self.sendLine("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))

    def signedOn(self):
        self.join(self.factory.channel)
        print "Signed on as %s." % (self.nickname,)

    def joined(self, channel):
        print "Joined %s." % (channel,)
        reactor.callLater(1, self.send_queue)

    def send_queue(self):
        # Send any messages we've been sent.
        while self.factory.messages:
            msg = self.factory.messages.pop().strip()
            if msg:
                self.msg(self.factory.channel, msg)
        reactor.callLater(0.1, self.send_queue)

    def privmsg(self, user, channel, msg):
        print msg


class SpewBotFactory(protocol.ClientFactory):
    protocol = SpewBot
    messages = []

    def __init__(self, channel, nickname='SpewBot', serverpass=None):
        self.channel = channel
        self.nickname = nickname
        self.password = serverpass

    def clientConnectionLost(self, connector, reason):
        print "Lost connection (%s), reconnecting." % (reason,)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Could not connect: %s" % (reason,)


class LineSocket(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def dataReceived(self, data):
        SpewBotFactory.messages.extend(data.split("\n"))


class LineSocketFactory(protocol.Factory):
    def __init__(self):
        self.echoers = []

    def buildProtocol(self, addr):
        return LineSocket(self)


if __name__ == "__main__":
    reactor.connectTCP(HOST, PORT, SpewBotFactory(CHANNEL, nickname=NICK, serverpass=PASSWORD))
    reactor.listenTCP(4321, LineSocketFactory())
    reactor.run()

