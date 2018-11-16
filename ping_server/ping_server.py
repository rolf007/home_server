#!/usr/bin/env python
# suresms.dk
# http://developer.suresms.com/https/
# https://api.suresms.com/Script/SendSMS.aspx?login=Rolf&password=L8wS8C77&to=+4526857540&Text=Test001
#Send Sms
# curl "https://api.suresms.com/Script/SendSMS.aspx?login=Rolf&password=L8wS8C77&to=+4526857540&Text=Test002"
#Receive Sms:
# curl "http://asmund.dk:5000/somepage?receivedutcdatetime=time&receivedfromphonenumber=from&receivedbyphonenumber=by&body=body"

import json
import os
import subprocess
import sys
import threading
from time import strftime, localtime, sleep
import time

home_server_root = os.path.split(sys.path[0])[0]
sys.path.append(os.path.join(home_server_root, "comm"))
from comm import Comm

#ip_list = [{"name": "alpha", "ip": "172.16.4.73"},
#        {"name": "beta", "ip": "172.16.4.74"},
#        {"name": "gamma", "ip": "172.16.4.75"}]
#ip_list = [{"name": "S", "ip": "192.168.0.44"},
#        {"name": "A", "ip": "192.168.0.20"},
#        {"name": "Rxfce", "ip": "192.168.0.11"}]
devnull = open(os.devnull, 'w')

def send_sms(text):
    print("sending sms '%s'..." % text)

def ip_went_online(name):
    send_sms("%s%%20went%%20online" % name)

def file_was_created():
    send_sms("%s%%20was%%20created" % "file")

class PingThread(threading.Thread):
    def __init__(self, interval=1):
        super().__init__()

        self.ip_list = self.load_obj("ip_list")
        self.kill = threading.Event()
        self.interval = interval
        self.start()

    def load_obj(self, name):
        with open(home_server_root + "/ping_server/" + name + '.json', 'rb') as f:
            return json.load(f)

    def run(self):
        while True:
            print("Do somthoing....!")

            file_name  = home_server_root + "/ping_server/ping_server.log"
            with open(file_name, 'a') as f:
                for ip in self.ip_list:
                    x = subprocess.call("ping -c1 -w1 %s" % ip["ip"], shell=True, stdout=devnull)
                    if x == 0:
                        if "online" in ip and ip["online"] == False:
                            ip_went_online(ip["name"])
                        ip["online"] = True
                    else:
                        ip["online"] = False
                f.write(strftime("%Y-%m-%d_%H:%M:%S", localtime()))
                for r in self.ip_list:
                    f.write(" %d" % (1 if "online" in r and r["online"] else 0))
                f.write("\n")

            is_killed = self.kill.wait(self.interval)
            if is_killed:
                break

    def shut_down(self):
        print("stopping serving ping...")
        self.kill.set()
        self.join()

class CheckFileThread(threading.Thread):
    def __init__(self, interval=1):
        super().__init__()
        self.kill = threading.Event()
        self.interval = interval
        self.exists = None
        self.start()

    def run(self):
        while True:
            exists = os.path.exists("check")
            if self.exists == False and exists == True:
                file_was_created()
            if self.exists == True and exists == False:
                print("file was deleted")
            self.exists = exists

            is_killed = self.kill.wait(self.interval)
            if is_killed:
                break

    def shut_down(self):
        print("stopping serving check file...")
        self.kill.set()
        self.join()


class PingServer():

    def __init__(self):
        self.comm = Comm(5002, "ping_server", {"status": self.status})
        self.ping_thread = PingThread(6)
        #self.check_file_thread = CheckFileThread(3)

    def status(self, params):
        return (200, "All is fine!")

    def shut_down(self):
        #self.check_file_thread.shut_down()
        self.ping_thread.shut_down()
        self.comm.shut_down()



ping_server = PingServer()
try:
    while True:
        time.sleep(2.0)
        print(".....")
except KeyboardInterrupt:
    pass
ping_server.shut_down()
