#!/usr/bin/env python3

# suresms.dk
# http://developer.suresms.com/https/
# https://api.suresms.com/Script/SendSMS.aspx?login=Rolf&password=xxxxxxxx&to=+4526857540&Text=Test001
#Send Sms
# curl "https://api.suresms.com/Script/SendSMS.aspx?login=Rolf&password=xxxxxxxx&to=+4526857540&Text=Test002"
#Receive Sms:
# curl "http://asmund.dk:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=from&receivedbyphonenumber=by&body=body"
# curl "http://127.0.0.1:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=+4526857540&receivedbyphonenumber=by&body=foo+.h.

import argparse
import json
import os
import requests
import sys
import time
import urllib
import re

home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])
sys.path.append(os.path.join(home_server_root, "comm"))
sys.path.append(os.path.join(home_server_root, "utils"))
from comm import Comm
from comm import UnicastListener
from argpkarse import ArgpKarse, ArgpKarseError
from micro_service import MicroServiceHandler

##res = requests.get("https://api.suresms.com/Script/SendSMS.aspx?login=Rolf&password=xxxxxxxx&to=+4526857540&Text=%s" % "outofmoney", timeout=2)
##print("res '%s'" % res)
##exit(0)

class SmsPortal():
    def __init__(self, logger, exc_cb):
        self.logger = logger
        self.comm = Comm(5003, "sms_portal", {"send_sms": self.send_sms}, self.logger, exc_cb)
        self.external_port = 5100
        self.unicast_listener = UnicastListener(self.sms_received, self.external_port, self.logger, exc_cb)
        self.sms_password = self.load_obj("sms_password")[0]
        parser = argparse.ArgumentParser()
        parser.add_argument('--pay', action='store_true')
        self.args = parser.parse_args()
        if self.args.pay:
            self.logger.log("you must pay!")
        else:
            self.logger.log("WARNING, you can't send SMS'es")
        self.sms_cmds = {
                "p": self.Cmd_p(self.logger, self.comm, 0, False, 0),
                "py": self.Cmd_py(self.logger, self.comm, 0, False, 0),
                "pl": self.Cmd_pl(self.logger, self.comm, 0, False, 0),
                "er": self.Cmd_emoji_receive(self.logger, self.comm, 1, False, 0),
                "es": self.Cmd_emoji_send(self.logger, self.comm, 1, False, 0),
                "ping": self.Cmd_ping(self.logger, self.comm, 1, True, 0),
                "pinglog": self.Cmd_pinglog(self.logger, self.comm, 1, True, 0),
                "radio": self.Cmd_radio(self.logger, self.comm, 0, False, 0),
                "skip": self.Cmd_skip(self.logger, self.comm, 0, False, 0),
                "pod": self.Cmd_podcast(self.logger, self.comm, 0, False, 0),
                "wiki": self.Cmd_wiki(self.logger, self.comm, 1, False, 0)
                }

    def fixup_phone_number(self, phonenumber):
        fixed_number = phonenumber
        if re.match("^  [0-9]{10}$", phonenumber):
            fixed_number = phonenumber[1:]
        elif re.match("^[0-9]{10}$", phonenumber):
            fixed_number = ' ' + phonenumber
        if fixed_number != phonenumber:
            self.logger.log("fixing phone number '%s' -> '%s'" % (phonenumber, fixed_number))
        return fixed_number

    class Cmd():
        def __init__(self, logger, comm, default_mobile, default_tail, default_error):
            self.logger = logger
            self.comm = comm
            self.parser = ArgpKarse()
            self.parser.add_argument('.m', type=int, default=default_mobile, empty=1)
            self.parser.add_argument('..tail', type=bool, default=default_tail, empty=True)
            self.parser.add_argument('..err', type=int, default=default_error, empty=1)
        def parse_args(self, arglist):
            self.args = self.parser.parse_args(arglist)
        def mobile(self):
            return self.args.m
        def tail(self):
            return self.args.tail
        def err(self):
            return self.args.err


# http://192.168.0.100:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=p%20metallica
#sms: 'p metallica jump in the fire'
    class Cmd_p(Cmd):
        def __init__(self, logger, comm, default_mobile, default_tail, default_error):
            super(SmsPortal.Cmd_p, self).__init__(logger, comm, default_mobile, default_tail, default_error)
            self.parser.add_argument('.r..artist', type=str, default=None, empty=None)
            self.parser.add_argument('.l..album', type=str, default=None, empty=None)
            self.parser.add_argument('.c..track', type=str, default=None, empty=None)
            self.parser.add_argument('.g..genre', type=str, default=None, empty=None)
            self.parser.add_argument('.e..release', type=str, default=None, empty=None)
        def exe(self):
            arguments = {"source": ["collection"]}
            if self.args.remain != "":
                arguments["title"] = self.args.remain
            if self.args.artist != None:
                arguments["artist"] = self.args.artist
            if self.args.album != None:
                arguments["album"] = self.args.album
            if self.args.track != None:
                arguments["track"] = self.args.track
            if self.args.genre != None:
                arguments["genre"] = self.args.genre
            if self.args.release != None:
                arguments["release"] = self.args.release
            self.logger.log("sms portal asking for: %s" % arguments)
            res = self.comm.call("music_server", "play", arguments)
            if res[0] != 200:
                return res
            res = self.comm.call("stream_receiver", "multicast", {})
            res = self.comm.call("led", "set", {"anim": ["mp"]})
            return res

# http://192.168.0.100:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=p%20metallica
#sms: 'py metallica jump in the fire'
    class Cmd_py(Cmd):
        def exe(self):
            res = self.comm.call("music_server", "play", {"query": [self.args.remain], "source": ["youtube"]})
            if res[0] != 200:
                return res
            res = self.comm.call("stream_receiver", "multicast", {})
            res = self.comm.call("led", "set", {"anim": ["mp"]})
            return res

# http://192.168.0.100:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=pl%20best%20of%20metal
#sms: 'pl best of metal'
    class Cmd_pl(Cmd):
        def exe(self):
            res = self.comm.call("music_server", "play", {"query": [self.args.remain], "source": ["list"]})
            if res[0] != 200:
                return res
            res = self.comm.call("stream_receiver", "multicast", {})
            res = self.comm.call("led", "set", {"anim": ["mp"]})
            return res

# http://192.168.0.100:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=stop
#sms: 'stop'
    class Cmd_stop(Cmd):
        def exe(self):
            res = self.comm.call("music_server", "stop", {})
            if res[0] != 200:
                return res
            res = self.comm.call("stream_receiver", "off", {})
            res = self.comm.call("led", "set", {"anim": ["off"]})
            return res

    class Cmd_emoji_receive(Cmd):
        def exe(self):
            res = self.comm.call("emoji", "receive", {"text": [self.args.remain]})
            return res

# http://192.168.0.100:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=es .dolphin. .dolphin.
#sms: 'es hello .UNICORN.'
    class Cmd_emoji_send(Cmd):
        def exe(self):
            res = self.comm.call("emoji", "send", {"text": [self.args.remain]})
            return res

#sms: 'ping'
    class Cmd_ping(Cmd):
        def exe(self):
            res = self.comm.call("ping_server", "status", {})
            return res

# http://192.168.0.100:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=pinglog%20SG
#sms: 'pinglog SG'
    class Cmd_pinglog(Cmd):
        def exe(self):
            res = self.comm.call("ping_server", "log", {"user": [self.args.remain]})
            return res


#web: http://192.168.0.100:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=radio 24syv
#sms: 'radio 24syv'
#sms: 'radio p3'
    class Cmd_radio(Cmd):
        def exe(self):
            res = self.comm.call("stream_receiver", "radio", {"channel": [self.args.remain]})
            res = self.comm.call("led", "set", {"anim": ["tu"]})
            return res

#web: http://192.168.0.100:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=skip random
#sms: 'skip 1'       go to next item
#sms: 'skip'         go to next item
#sms: 'skip -1'      go to previous item
#sms: 'skip =0'      go to item 0
#sms: 'skip last'    go to last item
#sms: 'skip random'  go to random item
    class Cmd_skip(Cmd):
        def exe(self):
            if self.args.remain == "last":
                res = self.comm.call("music_server", "skip", {"to": ["last"]})
            if self.args.remain == "random":
                res = self.comm.call("music_server", "skip", {"to": ["random"]})
            if len(self.args.remain) > 0:
                if self.args.remain[0] == "-":
                    res = self.comm.call("music_server", "skip", {"prev": [self.args.remain[1:]]})
                elif self.args.remain[0] == "=":
                    res = self.comm.call("music_server", "skip", {"to": [self.args.remain[1:]]})
                else:
                    res = self.comm.call("music_server", "skip", {"next": [self.args.remain]})
            else:
                res = self.comm.call("music_server", "skip", {"next": ["1"]})
            return res


#web: http://192.168.0.100:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=pod%20prev
#sms: 'pod baelte'
    class Cmd_podcast(Cmd):
        def exe(self):
            res = (404, "unknown podcast command '%s'" % self.args.remain)
            splt = self.args.remain.split(' ')
            if len(splt) == 1:
                res = self.comm.call("music_server", "podcast", {"program": [splt[0]]})
            elif len(splt) == 2:
                res = self.comm.call("music_server", "podcast", {"program": [splt[0]], "episode": [splt[1]]})

            if res[0] != 200:
                return res

            res = self.comm.call("stream_receiver", "multicast", {})
            res = self.comm.call("led", "set", {"anim": ["vi"]})
            return res

#web: http://192.168.0.100:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=wiki%20greta%20thunberg
    class Cmd_wiki(Cmd):
        def exe(self):
            res = self.comm.call("wiki", "wiki", {"query": [self.args.remain]})
            return res

# curl "http://asmund.dk:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=body"
    def sms_received(self, path, params, ip, port):
        self.logger.log("sms_received: '%s(%s)' from '%s:%d'" % (path, str(params), ip, port))
        if path != "suresms":
            return (200, "ok, but expected path == 'suresms', got '%s'" % path)
        if "receivedfromphonenumber" not in params:
            return (200, "ok, but expected parameter 'receivedfromphonenumber'")
        receivedfromphonenumber = params['receivedfromphonenumber'][0]
        if "body" not in params:
            return (200, "ok, but expected parameter 'body'")
        body = params['body'][0]
        if "receivedutcdatetime" not in params:
            receivedutcdatetime = None
        else:
            receivedutcdatetime = params['receivedutcdatetime'][0]
        if "receivedbyphonenumber" not in params:
            receivedbyphonenumber = None
        else:
            receivedbyphonenumber = params['receivedbyphonenumber'][0]
        receivedbyphonenumber = self.fixup_phone_number(receivedbyphonenumber)
        receivedfromphonenumber = self.fixup_phone_number(receivedfromphonenumber)

        space = body.find(' ')
        if space == -1:
            cmd = body
            arglist = ""
        else:
            cmd = body[:space]
            arglist = body[space+1:]

        if cmd in self.sms_cmds:
            cmd_inst = self.sms_cmds[cmd]
            try:
                cmd_inst.parse_args(arglist)
            except ArgpKarseError as e:
                self.logger.log("Error: ArgpKarse: %s" % e)
                return (200, "ok, but %s" %e)
            res = cmd_inst.exe()
            if res[1] != None and res[1] != "":
                if res[0] == 200:
                    mobile = cmd_inst.mobile()
                    tail = cmd_inst.tail()
                    if mobile > 0:
                        self.do_send_sms(receivedfromphonenumber, res[1], mobile, tail)
                else:
                    err = cmd_inst.err()
                    if err > 0:
                        err_msg = "%d: %s" % (res[0], res[1])
                        self.do_send_sms(receivedfromphonenumber, err_msg, err, False)
                        self.logger.log("Error: " + err_msg)
        else:
            err_msg = "Unknown command '%s', called with '%s'" % (cmd, arglist)
            self.do_send_sms(receivedfromphonenumber, err_msg, 1, False)
            self.logger.log("Error: " + err_msg)

        return (200, "sms handled ok")

    def load_obj(self, name):
        with open(os.path.join(home_server_config, name + '.json'), 'rb') as f:
            return json.load(f)

    # http://127.0.0.1:5003/send?text=hemmelig_token&to=+4526857540
    def send_sms(self, params):
        if "text" not in params:
            return (404, "sending sms requires a 'text'")
        if "to" not in params:
            return (404, "sending sms requires a 'to'")
        text = params["text"][0]
        to = params["to"][0]
        return self.do_send_sms(to, text, 1, False)

    def do_send_sms(self, to, text, mobile, tail):
        if tail:
            text = text[-120*mobile:]
        else:
            text = text[:120*mobile]
        login = "Rolf"
        pw = self.sms_password
        function = "Script/SendSMS.aspx"
        args = {"login": login, "password": pw, "to": to, "Text": text}
        req = "%s?%s" % (function, urllib.parse.urlencode(args, doseq=True))
        if self.args.pay:
            self.logger.log("sending sms: '%s' to '%s'" % (ascii(text), to))
            res = requests.get("https://api.suresms.com/%s" % req, timeout=2)
            self.logger.log("res '%s'" % res)
            return (200, "sent sms!")
        else:
            self.logger.log("would have sent sms: '%s' to '%s'" % (text, to))
            return (200, "would have sent sms! '%s' to '%s'" % (text, to))

    def shut_down(self):
        self.comm.shut_down()
        self.unicast_listener.stop()

if __name__ == '__main__':
    MicroServiceHandler("sms_portal", SmsPortal)
