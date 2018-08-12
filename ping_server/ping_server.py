#!/usr/bin/env python
# suresms.dk
# http://developer.suresms.com/https/
# https://api.suresms.com/Script/SendSMS.aspx?login=Rolf&password=L8wS8C77&to=+4526857540&Text=Test001
#Send Sms
# curl "https://api.suresms.com/Script/SendSMS.aspx?login=Rolf&password=L8wS8C77&to=+4526857540&Text=Test002"
#Receive Sms:
# curl "http://asmund.dk:5000/somepage?receivedutcdatetime=time&receivedfromphonenumber=from&receivedbyphonenumber=by&body=body"

import subprocess
import os
import sys
import json

from time import strftime, localtime, sleep

import time
import socket

from flask import Flask, request
app = Flask(__name__)

import threading
import requests

sys.path.append("../server_shared")
import server_shared

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

my_port = 5001
my_ip = server_shared.get_ip()
my_commands = ["ping"]
sms_portal_ip = ""
sms_portal_port = 0

ip_list = [{"name": "alpha", "ip": "172.16.4.73", "online": False},
        {"name": "beta", "ip": "172.16.4.74", "online": False},
        {"name": "gamma", "ip": "172.16.4.75", "online": False}]
ip_list = [{"name": "S", "ip": "192.168.0.44", "online": False},
        {"name": "A", "ip": "192.168.0.20", "online": False}]
devnull = open(os.devnull, 'w')

def send_sms(text):
    print("sending sms '%s'..." % text)
    if sms_portal_ip == "" or sms_portal_port == 0:
        print("Can't send sms. Sms portal ip/port unknown %s:%d" % (sms_portal_ip, sms_portal_port))
        return
    try:
        res = requests.get('http://%s:%d/send_sms?body=%s' % (sms_portal_ip, sms_portal_port, text), timeout=2)
    except requests.ConnectionError as e:
        print("failed to send %s" % e)

def ip_went_online(name):
    send_sms("%s%%20went%%20online" % name)

def file_was_created():
    send_sms("%s%%20was%%20created" % "file")

class PingThread(object):
    def __init__(self, interval=1):
        self.interval = interval

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self):
        while True:
            file_name  = "ping_server.log"
            with open(file_name, 'a') as f:
                for ip in ip_list:
                    x = subprocess.call("ping -c1 -w1 %s" % ip["ip"], shell=True, stdout=devnull)
                    if x == 0:
                        if "online" not in ip or ip["online"] == False:
                            ip_went_online(ip["name"])
                        ip["online"] = True
                    else:
                        ip["online"] = False
                f.write(strftime("%Y-%m-%d_%H:%M:%S", localtime()))
                for r in ip_list:
                    f.write(" %d" % (1 if r["online"] else 0))
                f.write("\n")

            time.sleep(self.interval)

class CheckFileThread(object):
    def __init__(self, interval=1):
        self.interval = interval
        self.exists = False

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self):
        while True:
            exists = os.path.exists("check")
            if self.exists == False and exists == True:
                file_was_created()
            if self.exists == True and exists == False:
                print("file was deleted")
            self.exists = exists

            time.sleep(self.interval)

class BroadcastListener(object):
    def __init__(self, interval=1):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.client.bind(("", 37020))

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self):
        sleep(4)
        while True:
            data, addr = self.client.recvfrom(1024)
            data = data.decode('ascii')
            sms_portal = "sms_portal: "
            if data.startswith(sms_portal):
                d = json.loads(data[len(sms_portal):])
                global sms_portal_ip
                global sms_portal_port
                sms_portal_ip = d["ip"]
                sms_portal_port = d["port"]
                dictToSend = {'commands':my_commands, 'port':my_port, 'ip':my_ip}
                try:
                    res = requests.get("http://%s:%d/register_service" % (sms_portal_ip, sms_portal_port), json=dictToSend, timeout=2)
                except requests.ConnectionError as e:
                    print("failed to send %s" % e)

@app.route("/ping")
def hello():
    str = ""
    for r in ip_list:
        str += " %s" % (r["name"] if r["online"] else "")
    return "Hello World!" + str


if __name__ == '__main__':
    ping_thread = PingThread(60)
    #check_file_thread = CheckFileThread(3)
    broadcastListener = BroadcastListener();
    app.run(host="0.0.0.0", port=my_port)
