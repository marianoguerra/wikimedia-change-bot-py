#! /usr/bin/env python3
from __future__ import print_function
import irc.bot
import irc.strings

import re
import pprint
import traceback

def print_change(data):
    """default on_change handler"""
    print("Change")
    pprint.pprint(data)
    print()

def print_error(error, msg):
    """default on_error handler"""
    print("Error")
    print(error, msg)
    print()

class WikiChangeBot(irc.bot.SingleServerIRCBot):
    """irc bot that listends to live changes from wikimedia projects"""
    def __init__(self, channel, nickname, server, port=6667,
            listen_nick="rc-pmtpa", on_change=print_change,
            on_error=print_error, logger=print):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.listen_nick = listen_nick
        self.on_change = on_change
        self.on_error = on_error
        self.logger = logger

    def on_nicknameinuse(self, c, e):
        self.logger("nick in use", c.get_nickname())
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        self.logger("welcome", self.channel)
        c.join(self.channel)

    def on_pubmsg(self, c, e):
        nick = e.source.nick
        msg = e.arguments[0]
        if self.listen_nick == nick:
            data = self.handle_message(msg)
            if data is not None:
                self.on_change(data)
            else:
                self.on_error(dict(reason="Error parsing", error=None, msg=msg))
        else:
            self.logger("ignore message", msg, "from", nick)

    def handle_message(self, msg):
        try:
            return parse_change(msg)
        except Exception as error:
            self.on_error(dict(reason="Error parsing", error=error, msg=msg))
            traceback.print_exc()

COLOR_RE = re.compile(r'(?:\x02|\x03(?:\d{1,2}(?:,\d{1,2})?)?)')


def strip_formatting(message):
    """Strips colors and formatting from IRC messages"""
    return COLOR_RE.sub('', message)

ACTION_RE = re.compile(r'\[\[(.+)\]\] (?P<log>.+)  \* (?P<user>.+) \*  (?P<summary>.+)')

DIFF_RE = re.compile(r'''
    \[\[(?P<page>.*)\]\]\        # page title
    (?P<patrolled>!|)            # patrolled
    (?P<new>N|)                  # new page
    (?P<minor>M|)                # minor edit
    (?P<bot>B|)\                 # bot edit
    (?P<url>.*)\                 # diff url
    \*\ (?P<user>.*?)\ \*\       # user
    \((?P<diff>(\+|-)\d*)\)\     # diff size
    ?(?P<summary>.*)             # edit summary
''', re.VERBOSE)


BOOL_FIELDS = ["bot", "minor", "new", "patrolled"]
TEXT_FIELDS = ["page", "summary", "url", "user"]
INT_FIELDS = ["diff"]

ACTION_TEXT_FIELDS = ["log", "user", "summary"]

def convert_fields(src, dest, fields, converter, default):
    for field in fields:
        if src.get(field) is not None:
            dest[field] = converter(src[field])
        else:
            dest[field] = default

def parse_change(message):
    cleaned_message = strip_formatting(message)
    edit_match = DIFF_RE.match(cleaned_message)
    action_match = ACTION_RE.match(cleaned_message)
    match = edit_match or action_match

    if not match:
        print('%s was not matched' % repr(cleaned_message))
        return None

    diff = match.groupdict()
    result = {}

    if action_match:
        convert_fields(diff, result, ACTION_TEXT_FIELDS, str, "")
        result["type"] = "action"
    else:
        convert_fields(diff, result, BOOL_FIELDS, bool, None)
        convert_fields(diff, result, TEXT_FIELDS, str, "")
        convert_fields(diff, result, INT_FIELDS, int, None)
        result["type"] = "edit"

    return result

def main():
    import sys
    if len(sys.argv) != 5:
        print("Usage: testbot <server[:port]> <channel> <nickname> <listen-nick>")
        sys.exit(1)

    s = sys.argv[1].split(":", 1)
    server = s[0]
    if len(s) == 2:
        try:
            port = int(s[1])
        except ValueError:
            print("Error: Erroneous port.")
            sys.exit(1)
    else:
        port = 6667
    channel = sys.argv[2]
    nickname = sys.argv[3]
    listen_nick = sys.argv[4]

    print("connecting", channel, nickname, server, port, "listen to", listen_nick)
    bot = WikiChangeBot(channel, nickname, server, port, listen_nick)
    bot.start()

if __name__ == "__main__":
    main()

