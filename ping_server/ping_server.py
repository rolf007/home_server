#!/usr/bin/env python

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
    def __init__(self, interval=1, ping_func=None):
        super().__init__()
        if ping_func == None:
            ping_func = self.real_ping

        self.ping_func = ping_func
        self.ip_list = []
        self.alarms_timeofday = [] # alarm, if user is online on a given time
        self.alarms_dayamount = [] # alarm, if user exceeds daily limit
        self.alarms_onoffline = [] # alarm, if user changes online status

        if interval != 0:
            self.kill = threading.Event()
            self.interval = interval
            self.start()

    def add_ip(self, user, ip):
        self.ip_list.append({"user": user, "ip": ip, "online": None})

    def add_alarm_timeofday(self, user, start, end, weekdays="0123456"):
        self.alarms_timeofday.append({"user": user, "weekdays": weekdays, "active": True, "start": start, "end": end})
        print("alarms : %s" % self.alarms_timeofday)

    def add_alarm_dayamount(self, user, amount, weekdays="0123456"):
        self.alarms_dayamount.append({"user": user, "weekdays": weekdays, "active": True, "amount": amount})
        print("alarms : %s" % self.alarms_dayamount)

    def add_alarm_onoffline(self, user, onoff, weekdays="0123456"):
        self.alarms_onoffline.append({"user": user, "weekdays": weekdays, "active": True, "onoff": onoff})
        print("alarms : %s" % self.alarms_onoffline)

    def alarm(self, msg):
        print("msg: %s" % msg)

    def real_ping(self, ip):
        print("pinging...")
        return subprocess.call("ping -c1 -w1 %s" % ip, shell=True, stdout=devnull)

    def run(self):
        while True:
            print("Do somthoing....!")
            self.do_something(localtime())

            is_killed = self.kill.wait(self.interval)
            if is_killed:
                break

    def do_something(self, now):
        file_name  = home_server_root + "/ping_server/ping_server.log"
        with open(file_name, 'a') as f:
            for ip in self.ip_list:
                x = self.ping_func(ip["ip"])
                if x == 0:
                    if ip["online"] == False:
                        for a in self.alarms_onoffline:
                            if (ip["user"] == a["user"]) and (str(now.tm_wday) in a["weekdays"]) and (a["active"]):
                                self.alarm("%s went online" % ip["user"])
                    ip["online"] = True
                else:
                    ip["online"] = False
            f.write(strftime("%Y-%m-%d_%H:%M:%S", now))
            for r in self.ip_list:
                f.write(" %d" % (1 if "online" in r and r["online"] else 0))
            f.write("\n")

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
        ip_list = self.load_obj("ip_list")
        self.comm = Comm(5002, "ping_server", {"status": self.status})
        self.ping_thread = PingThread(3, None)
        for ip in ip_list:
            self.ping_thread.add_ip(ip["name"], ip["ip"])
        #self.check_file_thread = CheckFileThread(3)

    def load_obj(self, name):
        with open(home_server_root + "/ping_server/" + name + '.json', 'rb') as f:
            return json.load(f)

    def status(self, params):
        return (200, "All is fine!")

    def shut_down(self):
        #self.check_file_thread.shut_down()
        self.ping_thread.shut_down()
        self.comm.shut_down()



if __name__ == '__main__':
    ping_server = PingServer()
    try:
        while True:
            time.sleep(2.0)
            print(".....")
    except KeyboardInterrupt:
        pass
    ping_server.shut_down()
