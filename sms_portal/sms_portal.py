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
sys.path.append(os.path.join(home_server_root, "logger"))
from comm import Comm
from comm import UnicastListener
from logger import Logger

##res = requests.get("https://api.suresms.com/Script/SendSMS.aspx?login=Rolf&password=xxxxxxxx&to=+4526857540&Text=%s" % "outofmoney", timeout=2)
##print("res '%s'" % res)
##exit(0)

class SmsPortal():
    def __init__(self):
        self.logger = Logger("sms_portal")
        self.logger.log("started SmsPortal")
        self.comm = Comm(5003, "sms_portal", {"send_sms": self.send_sms}, self.logger)
        self.external_port = 5100
        self.unicast_listener = UnicastListener(self.sms_received, self.external_port, self.logger)
        self.sms_password = self.load_obj("sms_password")[0]
        parser = argparse.ArgumentParser()
        parser.add_argument('--pay', action='store_true')
        self.args = parser.parse_args()
        if self.args.pay:
            self.logger.log("you must pay!")
        else:
            self.logger.log("WARNING, you can't send SMS'es")
        self.sms_cmds = {
                "p": self.cmd_p,
                "py": self.cmd_py,
                "er": self.cmd_emoji_receive,
                "es": self.cmd_emoji_send,
                "ping": self.cmd_ping,
                "pinglog": self.cmd_pinglog,
                "radio": self.cmd_radio,
                "pod": self.cmd_podcast,
                "wiki": self.cmd_wiki
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


# http://192.168.0.100:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=p%20metallica
#sms: 'p metallica jump in the fire'
    def cmd_p(self, args):
        self.logger.log("executing p(%s)" % str(args))
        res = self.comm.call("music_server", "play", {"title": [args], "source": ["collection"]})
        res = self.comm.call("stream_receiver", "multicast", {})
        return None, None

# http://192.168.0.100:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=p%20metallica
#sms: 'py metallica jump in the fire'
    def cmd_py(self, args):
        self.logger.log("executing py(%s)" % str(args))
        res = self.comm.call("music_server", "play", {"query": [args], "source": ["youtube"]})
        res = self.comm.call("stream_receiver", "multicast", {})
        return None, None

    def cmd_emoji_receive(self, args):
        self.logger.log("executing emoji_receive(%s)" % str(args))
        res = self.comm.call("emoji", "receive", {"text": [args]})
        self.logger.log(res)
        if res[0] == 200:
            return res[1], False
        return None, None

# http://192.168.0.100:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=es .dolphin. .dolphin.
#sms: 'es hello .UNICORN.'
    def cmd_emoji_send(self, args):
        self.logger.log("executing emoji_send(%s)" % str(args))
        res = self.comm.call("emoji", "send", {"text": [args]})
        self.logger.log("emoji send res: %s" % (res,))
        if res[0] == 200:
            return res[1], False
        return None, None

#sms: 'ping'
    def cmd_ping(self, args):
        self.logger.log("pinging")
        res = self.comm.call("ping_server", "status", {})
        if res[0] == 200:
            return res[1], True
        return None, None

# http://192.168.0.100:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=pinglog%20SG
#sms: 'pinglog SG'
    def cmd_pinglog(self, args):
        self.logger.log("ping log %s" % args)
        res = self.comm.call("ping_server", "log", {"user": [args]})
        if res[0] == 200:
            return res[1], True
        return None, None


#web: http://192.168.0.100:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=radio 24syv
#sms: 'radio 24syv'
#sms: 'radio p3'
    def cmd_radio(self, args):
        self.logger.log("radio")
        self.logger.log(args)
        res = self.comm.call("stream_receiver", "radio", {"channel": [args]})
        return None, None

#web: http://192.168.0.100:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=pod%20prev
#sms: 'pod baelte'
#sms: 'pod prev'
    def cmd_podcast(self, args):
        self.logger.log("podcasting")
        if args == "next":
            res = self.comm.call("music_server", "podcast", {"next": ["1"]})
        elif args == "prev":
            res = self.comm.call("music_server", "podcast", {"prev": ["1"]})
        else:
            splt = args.split(' ')
            if len(splt) == 1:
                res = self.comm.call("music_server", "podcast", {"program": [splt[0]]})
            elif len(splt) == 2:
                res = self.comm.call("music_server", "podcast", {"program": [splt[0]], "episode": [splt[1]]})
        res = self.comm.call("stream_receiver", "multicast", {})
        return None, None

#web: http://192.168.0.100:5100/suresms?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=wiki%20greta%20thunberg
    def cmd_wiki(self, args):
        res = self.comm.call("wiki", "wiki", {"query": [args]})
        if res[0] == 200:
            return res[1], False
        return None, None

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
            args = ""
        else:
            cmd = body[:space]
            args = body[space+1:]

        args, mobile = self.parse_mobile_arg(args, "m", "1")
        mobile = int(mobile)
        if cmd in self.sms_cmds:
            return_sms, tail = self.sms_cmds[cmd](args)
            if return_sms != None:
                self.do_send_sms(receivedfromphonenumber, return_sms, mobile, tail)
        else:
            err = "Unknown command '%s', called with args '%s'" % (cmd, args)
            self.do_send_sms(receivedfromphonenumber, err, 1, False)
            self.logger.log("Error: " + err)

        return (200, "sms handled ok")

    def parse_mobile_arg(self, args, arg_name, default_value = "1"):
        value = default_value
        s = re.search("^(?:(.*)\s)?\.%s([0-9]?)(?:\s(.*))?$" % arg_name, args)
        if s:
            value = s[2]
            if s[1] and s[3]:
                args = s[1] + " " + s[3]
            elif s[1]:
                args = s[1]
            elif s[3]:
                args = s[3]
            else:
                args = ""
        return args, value

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
    sms_portal = SmsPortal()
    try:
        while True:
            time.sleep(2.0)
    except KeyboardInterrupt:
        pass
    sms_portal.shut_down()
