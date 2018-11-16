#!/usr/bin/env python

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
sys.path.append(os.path.join(home_server_root, "comm"))
from comm import Comm
from comm import UnicastListener

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

# curl "http://asmund.dk:5100/somepage?receivedutcdatetime=time&receivedfromphonenumber=from&receivedbyphonenumber=by&body=body"
# http://127.0.0.1:5100/somepage?receivedutcdatetime=time&receivedfromphonenumber=from&receivedbyphonenumber=by&body=body%20p=metallica
    def sms_received(self, data):
        print("sms_received '%s'" % data)
        query = urllib.parse.urlsplit(data).query.decode('ascii')
        func  = urllib.parse.urlsplit(data).path.decode('ascii')
        if func != "somepage":
            return (404, "not available")
        params = urllib.parse.parse_qs(query)
        receivedutcdatetime = params['receivedutcdatetime'][0]
        receivedfromphonenumber = params['receivedfromphonenumber'][0]
        receivedbyphonenumber = params['receivedbyphonenumber'][0]
        body = params['body'][0]

        space = body.find(' ')
        if space == -1:
            cmd = body
            args = ""
        else:
            cmd = body[:space]
            args = body[space+1:]

        print("cmd = '%s'" % cmd)
        print("args = '%s'" % args)

        return (200, "sms handled ok")

    def load_obj(self, name):
        with open(home_server_root + "/sms_portal/" + name + '.json', 'rb') as f:
            return json.load(f)

    # http://127.0.0.1:5003/send?text=hemmelig_token&to=+4526857540
    def send_sms(self, params):
        if "text" not in params:
            return (404, "sending sms requires a 'text'")
        if "to" not in params:
            return (404, "sending sms requires a 'to'")
        text = params["text"][0]
        to = params["to"][0]
        #to = "+4526857540"
        #to = "+4540216259"
        login = "Rolf"
        pw = self.sms_password
        if self.args.pay:
            print("sending sms: '%s' to '%s'" % (text, to))
            res = requests.get("https://api.suresms.com/Script/SendSMS.aspx?login=%s&password=%s&to=%s&Text=%s" % (login, pw, to, text), timeout=2)
            print("res '%s'" % res)
            return (200, "send sms!")
        else:
            print("would have sent sms: '%s' to '%s'" % (text, to))
            return (200, "would have sent sms!")

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
