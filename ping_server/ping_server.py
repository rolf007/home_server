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

class PingThread(threading.Thread):
    def __init__(self, interval=1, ping_func=None):
        super().__init__()
        if ping_func == None:
            ping_func = self.real_ping

        self.ping_func = ping_func
        self.ip_list = []
        self.alarms = []
        self.interval = interval

        if ping_func == None:
            self.kill = threading.Event()
            self.start()

    def add_ip(self, user, ip):
        self.ip_list.append({"user": user, "ip": ip, "online": None, "amount": 0.0})

    def human_time_to_minutes(self, s):
        c = s.find(':')
        if c != -1:
            h = int(s[:c])
            m = int(s[c+1:])
            return h*60+m
        return 0


    def add_alarm_timeofday(self, user, start, end, weekdays="0123456"):
        # alarm, if user is online on a given time
        self.alarms.append({"type": "timeofday", "user": user, "weekdays": weekdays, "active": True, "start": self.human_time_to_minutes(start), "end": self.human_time_to_minutes(end)})

    def add_alarm_dayamount(self, user, amount, weekdays="0123456"):
        # alarm, if user exceeds daily limit
        self.alarms.append({"type": "dayamount", "user": user, "weekdays": weekdays, "active": True, "amount": amount})

    def add_alarm_onoffline(self, user, onoff="-+", weekdays="0123456"):
        # alarm, if user changes online status
        self.alarms.append({"type": "onoffline", "user": user, "weekdays": weekdays, "active": True, "onoff": onoff})

    def real_ping(self, ip):
        print("pinging...")
        return subprocess.call("ping -c1 -w1 %s" % ip, shell=True, stdout=devnull) == 0

    def run(self):
        while True:
            print("Do somthoing....!")
            self.do_something(localtime())

            is_killed = self.kill.wait(self.interval)
            if is_killed:
                break

    def do_something(self, now):
        alarm_msgs = []
        for ip in self.ip_list:
            online = self.ping_func(ip["ip"])
            if online:
                ip["amount"] += self.interval/60.0
            for a in self.alarms:
                if (ip["user"] == a["user"]) and (str(now.tm_wday) in a["weekdays"]) and (a["active"]):
                    if a["type"] == "onoffline":
                        if (ip["online"] == False) and (online) and ('+' in a["onoff"]):
                            alarm_msgs.append("%s went online" % ip["user"])
                        if (ip["online"] == True) and (not online) and ('-' in a["onoff"]):
                            alarm_msgs.append("%s went offline" % ip["user"])
                    elif a["type"] == "timeofday":
                        if (ip["online"] == False) and (online):
                            if (now.tm_hour*60+now.tm_min >= a["start"]) and (now.tm_hour*60+now.tm_min < a["end"]):
                                alarm_msgs.append("%s went online at %d:%d" % (ip["user"], now.tm_hour, now.tm_min))
                    elif a["type"] == "dayamount":
                        if ip["amount"] >= a["amount"]:
                            alarm_msgs.append("%s exceeded amount %s" % (ip["user"], a["amount"]))
                        pass
            ip["online"] = online
        return alarm_msgs

    def shut_down(self):
        print("stopping serving ping...")
        self.kill.set()
        self.join()

class PingServer():

    def __init__(self):
        ip_list = self.load_obj("ip_list")
        self.comm = Comm(5002, "ping_server", {"status": self.status})
        self.ping_thread = PingThread(3, None)
        for ip in ip_list:
            self.ping_thread.add_ip(ip["name"], ip["ip"])

    def load_obj(self, name):
        with open(home_server_root + "/ping_server/" + name + '.json', 'rb') as f:
            return json.load(f)

    def status(self, params):
        return (200, "All is fine!")

    def shut_down(self):
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
