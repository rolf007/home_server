#!/usr/bin/env python

# suresms.dk
# http://developer.suresms.com/https/
# https://api.suresms.com/Script/SendSMS.aspx?login=Rolf&password=L8wS8C77&to=+4526857540&Text=Test001
#Send Sms
# curl "https://api.suresms.com/Script/SendSMS.aspx?login=Rolf&password=L8wS8C77&to=+4526857540&Text=Test002"
#Receive Sms:
# curl "http://asmund.dk:5000/somepage?receivedutcdatetime=time&receivedfromphonenumber=from&receivedbyphonenumber=by&body=body"


import socket

from time import strftime, localtime, sleep

import time

from flask import Flask, request
app = Flask(__name__)

import threading
import requests
import sys
import argparse

sys.path.append("../server_shared")
import server_shared

##res = requests.get("https://api.suresms.com/Script/SendSMS.aspx?login=Rolf&password=L8wS8C77&to=+4526857540&Text=%s" % "outofmoney", timeout=2)
##print("res '%s'" % res)
##exit(0)


import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

commands = {}
my_port = 5000
my_ip = server_shared.get_ip()

parser = argparse.ArgumentParser()
parser.add_argument('--pay', action='store_true')
args = parser.parse_args()
if args.pay:
    print("you must pay!")
else:
    print("WARNING, you can't send SMS'es")

class Broadcaster(object):

    def __init__(self, interval=1):

        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Set a timeout so the socket does not block
        # indefinitely when trying to receive data.
        self.server.settimeout(0.2)
        self.server.bind(("", 44444))

        self.interval = interval

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution


    def run(self):
        while True:
            message = "sms_portal: {\"port\":%d, \"ip\":\"%s\"}" % ( my_port, my_ip)
            self.server.sendto(bytes(message, 'ascii'), ('<broadcast>', 37020))

            time.sleep(self.interval)


@app.route("/register_service")
def register_service():
    payload = request.get_json()
    if "commands" in payload and "port" in payload and "ip" in payload:
        for cmd in payload["commands"]:
            if cmd not in commands:
                commands[cmd] = {'port':payload["port"], 'ip':payload["ip"]}
                print("service registered. %s %s" % (cmd, commands[cmd]))
    return "service registered"

@app.route("/send_sms")
def send_sms():
    body = request.args.get('body')
    if args.pay:
        print("sending sms: '" + body + "'")
        res = requests.get("https://api.suresms.com/Script/SendSMS.aspx?login=Rolf&password=L8wS8C77&to=+4526857540&Text=%s" % body, timeout=2)
        print("res '%s'" % res)
    else:
        print("would have sent sms: '" + body + "'")
    return "message sent"

@app.route("/somepage")
def somepage():
    receivedutcdatetime = request.args.get('receivedutcdatetime')
    receivedfromphonenumber = request.args.get('receivedfromphonenumber')
    receivedbyphonenumber = request.args.get('receivedbyphonenumber')
    body = request.args.get('body')
    space = body.find(' ')
    if space == -1:
        cmd = body
        args = ""
    else:
        cmd = body[:space]
        args = body[space+1:]

    return "Hello World! cmd = '" + cmd + "', args = '" + args + "' sure!\n"


if __name__ == '__main__':


    example = Broadcaster(3)
    app.run(host="0.0.0.0", port=5000, threaded=True)

