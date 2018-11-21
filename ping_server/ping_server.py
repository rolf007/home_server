#!/usr/bin/env python3

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
    def __init__(self, interval, alarm_cb, ping_func=None):
        super().__init__()
        if ping_func == None:
            self.ping_func = self.real_ping
        else:
            self.ping_func = ping_func
        self.ip_list = []
        self.alarms = []
        self.last_time = None
        self.alarm_cb = alarm_cb

        if ping_func == None:
            self.kill = threading.Event()
            self.interval = interval
            self.start()

    def add_ip(self, user, ip):
        self.ip_list.append({"user": user, "ip": ip, "online": None, "log": [], "log_end":None})

    def human_time_to_minutes(self, s):
        c = s.find(':')
        if c != -1:
            h = int(s[:c])
            m = int(s[c+1:])
            return h*60+m
        return 0


    def add_alarm_timeofday(self, user, to, start, end, weekdays="0123456"):
        # alarm, if user is online on a given time
        self.alarms.append({"type": "timeofday", "user": user, "weekdays": weekdays, "active": True, "to": to, "start": self.human_time_to_minutes(start), "end": self.human_time_to_minutes(end)})

    def add_alarm_dayamount(self, user, to, amount, weekdays="0123456"):
        # alarm, if user exceeds daily limit
        self.alarms.append({"type": "dayamount", "user": user, "weekdays": weekdays, "active": True, "to": to, "amount": amount})

    def add_alarm_onoffline(self, user, to, onoff="-+", weekdays="0123456"):
        # alarm, if user changes online status
        self.alarms.append({"type": "onoffline", "user": user, "weekdays": weekdays, "active": True, "to": to, "onoff": onoff})

    def real_ping(self, ip):
        ping_result = subprocess.call("ping -c1 -w1 %s" % ip, shell=True, stdout=devnull) == 0
        #print("ping '%s'. Result: %s" % (ip, ping_result))
        return ping_result

    def run(self):
        while True:
            self.do_something(localtime())

            is_killed = self.kill.wait(self.interval)
            if is_killed:
                break

    def do_something(self, now):
        for ip in self.ip_list:
            if self.last_time != None:
                old_amount = self.calc_amount(ip)
            else:
                old_amount = 0.0
            if self.last_time and now.tm_mday != self.last_time.tm_mday:
                # it's a new day.
                if ip["online"]:
                    midnight_yesterday = time.struct_time((self.last_time.tm_year, self.last_time.tm_mon, self.last_time.tm_mday, 24, 0, 0, self.last_time.tm_wday, self.last_time.tm_yday, self.last_time.tm_isdst))
                    ip["log"].append((midnight_yesterday, False))
                    midnight_today = time.struct_time((now.tm_year, now.tm_mon, now.tm_mday, 0, 0, 0, now.tm_wday, now.tm_yday, now.tm_isdst))
                    ip["log"].append((midnight_today, True))

            ip["log_end"] = now
            online = self.ping_func(ip["ip"])
            went_online = ip["online"] == False and online == True
            went_offline = ip["online"] == True and online == False
            if ip["online"] != True and online == True:
                ip["log"].append((now, True))
            if went_offline:
                ip["log"].append((now, False))
            amount = self.calc_amount(ip)
            for a in self.alarms:
                if (ip["user"] == a["user"]) and (str(now.tm_wday) in a["weekdays"]) and (a["active"]):
                    if a["type"] == "onoffline":
                        if (went_online) and ('+' in a["onoff"]):
                            self.alarm_cb("%s went online" % ip["user"], a["to"])
                        if (went_offline) and ('-' in a["onoff"]):
                            self.alarm_cb("%s went offline" % ip["user"], a["to"])
                    elif a["type"] == "timeofday":
                        if (went_online):
                            if (now.tm_hour*60+now.tm_min >= a["start"]) and (now.tm_hour*60+now.tm_min < a["end"]):
                                self.alarm_cb("%s went online at %d:%d" % (ip["user"], now.tm_hour, now.tm_min), a["to"])
                    elif a["type"] == "dayamount":
                        if amount >= a["amount"] and old_amount < a["amount"]:
                            self.alarm_cb("%s exceeded amount %s" % (ip["user"], a["amount"]), a["to"])
            ip["online"] = online
        self.last_time = now

    def calc_amount(self, ip, day=None):
        if ip["log_end"] == None:
            return 0.0
        if day == None:
            day = (ip["log_end"].tm_year, ip["log_end"].tm_mon, ip["log_end"].tm_mday)
        amount = 0.0
        online_time = None
        for entry in ip["log"]:
            if entry[0].tm_year == day[0] and entry[0].tm_mon == day[1] and entry[0].tm_mday == day[2]:
                if entry[1] == True:
                    online_time = (entry[0].tm_hour, entry[0].tm_min)
                if entry[1] == False and online_time != None:
                    amount += (entry[0].tm_hour - online_time[0])*60 + (entry[0].tm_min - online_time[1])
                    online_time = None
        if online_time:
            amount += (ip["log_end"].tm_hour - online_time[0])*60 + (ip["log_end"].tm_min - online_time[1])
        return amount



    def get_log(self, user, day=None):
        for ip in self.ip_list:
            if ip["user"] == user:
                if ip["log_end"] == None:
                    return []
                full_log = ip["log"]
                if day == None:
                    day = (ip["log_end"].tm_year, ip["log_end"].tm_mon, ip["log_end"].tm_mday)
                day_log = []
                for entry in full_log:
                    if entry[0].tm_year == day[0] and entry[0].tm_mon == day[1] and entry[0].tm_mday == day[2]:
                        day_log.append(entry)
                return day_log
        return None

    def m_get_log(self, user, day=None):
        log = self.get_log(user, day)
        if log == None:
            return "unknown user '%s'" % user
        mlog = ""
        for entry in log:
            if entry[1] == True:
                mlog += '\n+'
            else:
                mlog += '-'
            mlog += "%d:%02d" % (entry[0].tm_hour, entry[0].tm_min)
        for ip in self.ip_list:
            if ip["user"] == user:
                mlog += "\n=%d" % self.calc_amount(ip, day)
        mlog = mlog[1:]
        return mlog[-120:]

    def m_get_status(self):
        mlog = ""
        for ip in self.ip_list:
            if ip["online"]:
                if mlog != "":
                    mlog += ", "
                mlog += "%s %d" % (ip["user"], self.calc_amount(ip))
        return mlog[-120:]

    def shut_down(self):
        print("stopping serving ping...")
        self.kill.set()
        self.join()

class PingServer():

    def __init__(self):
        ip_list = self.load_obj("ip_list")
        alarms = self.load_obj("alarms")
        self.comm = Comm(5002, "ping_server", {"status": self.status, "log": self.log})
        self.ping_thread = PingThread(3, self.alarm_received, None)
        for ip in ip_list:
            self.ping_thread.add_ip(ip["name"], ip["ip"])
        for a in alarms:
            if a["type"] == "timeofday":
                self.ping_thread.add_alarm_timeofday(a["user"], a["to"], a["start"], a["end"], a["weekdays"])
            elif a["type"] == "dayamount":
                self.ping_thread.add_alarm_dayamount(a["user"], a["to"], a["amount"], a["weekdays"])
            elif a["type"] == "onoffline":
                self.ping_thread.add_alarm_onoffline(a["user"], a["to"], a["onoff"], a["weekdays"])

    def alarm_received(self, alarm, to):
        res = self.comm.call("sms_portal", "send", {"text": [alarm], "to": [to]})
        print("PingServer::alarm_received: %s " % alarm)

    def load_obj(self, name):
        with open(home_server_root + "/ping_server/" + name + '.json', 'rb') as f:
            return json.load(f)

    def status(self, params):
        return (200, self.ping_thread.m_get_status())

    def log(self, params):
        if "user" not in params:
            return (404, "function 'log' requires 'user'")
        user = params["user"][0]
        return (200, self.ping_thread.m_get_log(user))

    def shut_down(self):
        self.ping_thread.shut_down()
        self.comm.shut_down()



if __name__ == '__main__':
    ping_server = PingServer()
    try:
        while True:
            time.sleep(2.0)
    except KeyboardInterrupt:
        pass
    ping_server.shut_down()
