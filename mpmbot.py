import re

from irc import IRCBot, run_bot

class MPMBot(IRCBot):

    def ticket_info(self, sender, message, channel, number=None):
        if number:
            reply = '%s: #%s' % (sender, number)
        else:
            reply = '%s: could not find that ticket' % sender
        return reply

    def command_patterns(self):
        return(
            ('.*#ticket (?P<number>\d+)', self.ticket_info),
            #('.*#ticket', self.ticket_info),
        )

host = 'irc.freenode.net'
port = 6667
nick = 'mpmbot'
channels = ['#mpmbot',]

run_bot(MPMBot, host, port, nick, channels)
