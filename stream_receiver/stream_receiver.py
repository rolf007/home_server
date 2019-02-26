#!/usr/bin/env python3
import os
import signal
import sys
import subprocess
import time

home_server_root = os.path.split(sys.path[0])[0]
sys.path.append(os.path.join(home_server_root, "comm"))
sys.path.append(os.path.join(home_server_root, "utils"))
from comm import Comm
from micro_service import MicroServiceHandler

devnull = open(os.devnull, 'w')

class StreamReceiver():
    def __init__(self, logger, exc_cb):
        self.logger = logger
        self.comm = Comm(5005, "stream_receiver", {"multicast": self.multicast, "radio": self.radio, "off": self.off}, self.logger, exc_cb)
        self.radio = RadioReceiver()
        self.multicast_receiver = MulticastReceiver()
        self.running = True
        self.source = None

# http://127.0.0.1:5005/radio
# http://127.0.0.1:5005/radio 24syv
    def radio(self, params):
        if "channel" in params:
            channel = params["channel"][0]
            self.radio.set_channel(channel)
        self.set_source("radio")
        return (200, "switched to radio ok")

# http://127.0.0.1:5005/multicast
    def multicast(self, params):
        self.set_source("multicast")
        return (200, "switched to multicast ok")

# http://127.0.0.1:5005/off
    def off(self, params):
        self.set_source(None)
        return (200, "switched off")

    def shut_down(self):
        self.set_source(None)
        self.comm.shut_down()
        self.running = False

    def set_source(self, source):
        print("setting source: '%s'" % source)
        if source == self.source:
            return
        self.source = source
        if source == "radio":
            self.multicast_receiver.stop()
            self.radio.start()
        elif source == "multicast":
            self.radio.stop()
            self.multicast_receiver.start()
        else:
            self.radio.stop()
            self.multicast_receiver.stop()

class MulticastReceiver():
    def __init__(self):
        self.p = None

    def start(self):
        if self.p:
            self.stop()
        print("starting multicast...")
        self.p = subprocess.Popen(["vlc", "--intf", "dummy", "rtp://239.255.12.42"], stdout=devnull, stderr=devnull)

    def stop(self):
        if self.p == None:
            return
        print("stopping multicast...")
        self.p.terminate()
        print("vlc multicast stopped: %s %s" % self.p.communicate())
        self.p = None


class RadioReceiver():
    def __init__(self):
        self.channels = {
                #0: 'http://streaming.radio24syv.dk/pls/24syv_96_IR.pls',
                "24syv": 'http://stream.taleradio.dk/web128',
                "p1": 'http://live-icy.gss.dr.dk/A/A03L.mp3.m3u',
                "p2": 'http://live-icy.gss.dr.dk/A/A04L.mp3.m3u',
                "p3": 'http://live-icy.gss.dr.dk/A/A05L.mp3.m3u',
                }
        self.channel = "p1"
        self.p = None

    def set_channel(self, channel):
        print("radio channel %s" % channel)
        if channel in self.channels:
            if channel != self.channel:
                self.channel = channel
                self.stop()
                self.start()

    def start(self):
        print("starting radio...")
        if self.p:
            self.stop()
        self.p = subprocess.Popen(["vlc", "--intf", "dummy", self.channels[self.channel]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#https://www.radio24syv.dk/hoer-radio-paa-din-computer
#24syv vlc http://streaming.radio24syv.dk/pls/24syv_96_IR.pls
#https://www.dr.dk/hjaelp/digtal-radio/direkte-links-til-dr-radio-paa-nettet
#P1 vlc http://live-icy.gss.dr.dk/A/A03L.mp3.m3u
#P2 vlc http://live-icy.gss.dr.dk/A/A04L.mp3.m3u
#P3 vlc http://live-icy.gss.dr.dk/A/A05L.mp3.m3u

    def stop(self):
        if self.p == None:
            return
        print("stopping radio...")
        self.p.terminate()
        print("radio stopped!")
        print("vlc radio stopped: %s %s" % self.p.communicate())
        self.p = None

if __name__ == '__main__':
    MicroServiceHandler("streamer", StreamReceiver)
