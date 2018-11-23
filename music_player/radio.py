#!/usr/bin/env python3
import os
import sys
import subprocess

home_server_root = os.path.split(sys.path[0])[0]
sys.path.append(os.path.join(home_server_root, "comm"))
from comm import Comm
sys.path.append(os.path.join(home_server_root, "keypress"))
from pygame_inputter import PyGameInputter
from raspberry_inputter import RaspberryInputter
from b_inputter import BInputter
from keypress import KeyPress
from morse_maker import MorseMaker

devnull = open(os.devnull, 'w')

class Radio():
    def __init__(self, inputter):
        self.comm = Comm(5000, "player", {})
        self.inputter = inputter
        self.main_menu = KeyPress.mkUnion([
            KeyPress.compile(".A.a<match>", match=lambda: self.youtube_play("metallica judas kiss")),
            KeyPress.compile(".B.b<match>", match=lambda: self.radio_play()),
            KeyPress.compile(".D.d<match>", match=lambda: self.podcast("d6m")),
            KeyPress.compile(".D.A.a.d<match>", match=lambda: self.podcast("baelte")),
            KeyPress.compile(".D.A.a.A.a.d<match>", match=lambda: self.podcast("orientering")),
            KeyPress.compile(".D.C.c.d<match>", match=lambda: self.podcast_next()),
            KeyPress.compile(".D.B.b.d<match>", match=lambda: self.podcast_prev()),
            KeyPress.compile(".B.A.a.b<match>", match=lambda: self.radio_channel(0)),
            KeyPress.compile(".B.C.c.b<match>", match=lambda: self.radio_channel(1)),
            KeyPress.compile(".C.c<match>", match=lambda: self.multicast_play(None)),
            KeyPress.compile(".C.A.a.c<match>", match=lambda: self.multicast_play("DROID-3 plays tough!")),
            KeyPress.compile(".C.A.a.A.a.c<match>", match=lambda: self.multicast_play("DROID-3 new firmware")),
            KeyPress.compile(".C.A.a.A.a.A.a.c<match>", match=lambda: self.go_to_morse()),
        ])
        morse_maker = MorseMaker('C', 'c', 200, 500)
        self.morse_menu = KeyPress.mkUnion(morse_maker.mkAll(lambda c: self.morse_append(c)) +
                [KeyPress.compile(".A.a<match>", match = lambda: self.end_morse())]
                )
        print("==== press 'A' for youtube")
        print("==== press 'B' for radio")
        print("==== press 'CA' for music collection")
        print("==== press 'CAAA' for morse")
        print("==== press 'D' for podcast (DC=next, DB = prev)")
        self.radio = RadioReceiver()
        self.multicast_receiver = MulticastReceiver()
        self.go_to_main_menu()

    def go_to_main_menu(self):
        self.inputter.key_press = KeyPress(self.main_menu)

    def go_to_morse(self):
        print("going to morse...")
        self.inputter.key_press = KeyPress(self.morse_menu)
        self.morse_input = ""


    def end_morse(self):
        self.go_to_main_menu()
        self.multicast_play(self.morse_input)

    def morse_append(self, c):
        print("=== %s" % c)
        self.morse_input += c

    def radio_channel(self, channel):
        self.radio.set_channel(channel)
        self.set_source("radio")

    def radio_play(self):
        self.set_source("radio")

    def podcast(self, program):
        if program:
            print("requesting program '%s'" % program)
            try:
                res = self.comm.call("music_server", "podcast", {"program": [program]})
                print("res = %d %s" % res)
            except requests.ConnectionError as e:
                print("failed to send %s" % e)
        self.set_source("podcast")

    def podcast_next(self):
        try:
            res = self.comm.call("music_server", "podcast", {"next": [1]})
            print("res = %d %s" % res)
        except requests.ConnectionError as e:
            print("failed to send %s" % e)
        self.set_source("podcast")

    def podcast_prev(self):
        try:
            res = self.comm.call("music_server", "podcast", {"prev": [1]})
            print("res = %d %s" % res)
        except requests.ConnectionError as e:
            print("failed to send %s" % e)
        self.set_source("podcast")

    def multicast_play(self, query):
        if query:
            print("requesting '%s'" % query)
            try:
                res = self.comm.call("music_server", "play", {"query": [query]})
                print("res = %d %s" % res)
            except requests.ConnectionError as e:
                print("failed to send %s" % e)
        self.set_source("multicast")

    def youtube_play(self, query):
        if query:
            print("requesting '%s'" % query)
            try:
                res = self.comm.call("music_server", "play", {"query": [query], "source": "youtube"})
                print("res = %d %s" % res)
            except requests.ConnectionError as e:
                print("failed to send %s" % e)
        self.set_source("youtube")

    def main_loop(self):
        self.inputter.main_loop()

    def shut_down(self):
        self.set_source(None)
        self.comm.shut_down()
        self.inputter.shut_down()

    def set_source(self, source):
        print("setting source: '%s'" % source)
        if source == "radio":
            self.multicast_receiver.stop()
            self.radio.start()
        elif source == "multicast":
            self.radio.stop()
            self.multicast_receiver.start()
        elif source == "youtube":
            self.radio.stop()
            self.multicast_receiver.start()
        elif source == "podcast":
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
        self.p = subprocess.Popen("vlc --intf dummy rtp://239.255.12.42", shell=True, stdout=devnull, stderr=devnull)

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
                0: 'http://stream.taleradio.dk/web128',
                1: 'http://live-icy.gss.dr.dk/A/A03L.mp3.m3u',
                2: 'http://live-icy.gss.dr.dk/A/A04L.mp3.m3u',
                3: 'http://live-icy.gss.dr.dk/A/A05L.mp3.m3u',
                }
        self.channel = 0
        self.p = None

    def set_channel(self, channel):
        print("radio channel %s" % channel)
        if channel in self.channels:
            if channel != self.channel:
                self.channel = channel

    def start(self):
        print("starting radio...")
        if self.p:
            self.stop()
        self.p = subprocess.Popen("vlc --intf dummy %s" % self.channels[self.channel], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
        print("vlc radio stopped: %s %s" % self.p.communicate())
        self.p = None

inputter = PyGameInputter()

radio = Radio(inputter)
try:
    radio.main_loop()
except KeyboardInterrupt:
    pass
radio.shut_down()
