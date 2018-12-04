#!/usr/bin/env python3

# suresms.dk
# http://developer.suresms.com/https/
# https://api.suresms.com/Script/SendSMS.aspx?login=Rolf&password=xxxxxxxx&to=+4526857540&Text=Test001
#Send Sms
# curl "https://api.suresms.com/Script/SendSMS.aspx?login=Rolf&password=xxxxxxxx&to=+4526857540&Text=Test002"
#Receive Sms:
# curl "http://asmund.dk:5000/somepage?receivedutcdatetime=time&receivedfromphonenumber=from&receivedbyphonenumber=by&body=body"

import argparse
import json
import os
import requests
import sys
import time
import urllib


home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])
sys.path.append(os.path.join(home_server_root, "comm"))
from comm import Comm
from comm import UnicastListener

def debug_print(x):
    print(str(x).encode('unicode_escape').decode())

##res = requests.get("https://api.suresms.com/Script/SendSMS.aspx?login=Rolf&password=xxxxxxxx&to=+4526857540&Text=%s" % "outofmoney", timeout=2)
##print("res '%s'" % res)
##exit(0)

class SmsPortal():
    def __init__(self):
        self.comm = Comm(5003, "sms_portal", {"send": self.send_sms})
        self.external_port = 5100
        self.unicast_listener = UnicastListener(self.sms_received, self.external_port)
        self.sms_password = self.load_obj("sms_password")[0]
        parser = argparse.ArgumentParser()
        parser.add_argument('--pay', action='store_true')
        self.args = parser.parse_args()
        if self.args.pay:
            print("you must pay!")
        else:
            print("WARNING, you can't send SMS'es")
        self.sms_cmds = {
                "p": self.cmd_p,
                "er": self.cmd_emoji_receive,
                "es": self.cmd_emoji_send
                }

    def cmd_p(self, args, phonenumber):
        debug_print("executing p(%s)" % str(args))
        res = self.comm.call("music_server", "play", {"query": [args], "source": ["youtube"]})
        #self.do_send_sms(phonenumber, "Ok. Playing.+"+chr(129412))

    def cmd_emoji_receive(self, args, phonenumber):
        debug_print("executing emoji_receive(%s)" % str(args))
        res = self.comm.call("emoji", "receive", {"text": [args]})
        print(res)
        if res[0] == 200:
            self.do_send_sms(phonenumber, res[1])

    def cmd_emoji_send(self, args, phonenumber):
        debug_print("executing emoji_send(%s)" % str(args))
        res = self.comm.call("emoji", "send", {"text": [args]})
        debug_print("emoji send res: %s" % (res,))
        if res[0] == 200:
            self.do_send_sms(phonenumber, res[1])

# curl "http://asmund.dk:5100/somepage?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=body"
# http://127.0.0.1:5100/somepage?receivedutcdatetime=time&receivedfromphonenumber=12345678&receivedbyphonenumber=87654321&body=p%20metallica
    def sms_received(self, path, params, ip, port):
        debug_print("sms_received: '%s(%s)' from '%s:%d'" % (path, str(params), ip, port))
        if path != "somepage":
            return (200, "ok, but expected path == 'somepage', got '%s'" % path)
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

        space = body.find(' ')
        if space == -1:
            cmd = body
            args = ""
        else:
            cmd = body[:space]
            args = body[space+1:]

        if cmd in self.sms_cmds:
            self.sms_cmds[cmd](args, receivedfromphonenumber)
        else:
            print("Unknown command '%s', called with args '%s'" % (cmd, args))

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
        return self.do_send_sms(to, text)

    def do_send_sms(self, to, text):
        login = "Rolf"
        pw = self.sms_password
        function = "Script/SendSMS.aspx"
        args = {"login": login, "password": pw, "to": to, "Text": text}
        req = "%s?%s" % (function, urllib.parse.urlencode(args, doseq=True))
        if self.args.pay:
            print("sending sms: '%s' to '%s'" % (text, to))
            res = requests.get("https://api.suresms.com/%s" % req, timeout=2)
            print("res '%s'" % res)
            return (200, "sent sms!")
        else:
            print("would have sent sms: '%s'" % req)
            return (200, "would have sent sms! '%s' to '%s'" % (text, to))

    def shut_down(self):
        self.comm.shut_down()
        self.unicast_listener.stop()

sms_portal = SmsPortal()
try:
    while True:
        time.sleep(2.0)
except KeyboardInterrupt:
    pass
sms_portal.shut_down()
