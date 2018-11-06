#!/usr/bin/env python3
import pygame
import sys
from keypress import KeyPress
from threading import Timer
import requests
import subprocess
import time
import os
import re
sys.path.append("../comm")
from comm import Comm

devnull = open(os.devnull, 'w')
#seq0 = KeyPress.compile("Aa1000-3000*Aa<foo>", foo=lambda: print("SUCCES foo"))
#seq1 = KeyPress.compile("Bb1000-3000*Bb<bar>", bar=lambda: print("SUCCES bar"))
#seq2 = KeyPress.compile("BAa<one>Aa<two>Aa<three>b<tripple>", tripple=lambda: print("SUCCES tripple"), one=lambda: print("ONE"), two=lambda: print("TWO"), three=lambda: print("THREE"))
#seq3 = KeyPress.compile("Cc1000-3000<baz>", baz=lambda: print("SUCCES baz"))
#seq4 = KeyPress.compile(".C(.A.a<one>|.B.b<two>|(.A&.B)(.a&.b)<three>)*.c", one=lambda: print("cA"), two=lambda: print("cB"), three=lambda: print("cAB"))
#seq4 = KeyPress.compile(".C(.A1000-3000+a<one>|.A2000-4000+a<two>)*.c", one=lambda: print("one"), two=lambda: print("two"))
#seq4 = KeyPress.compile(".C1000-3000<one>3000-5000<two>5000-7000<three>.c", one=lambda: print("one"), two=lambda: print("two"), three=lambda: print("three"))

class RaspberryInputter:
    def __init__(self):
        super(RaspberryInputter, self).__init__()
        from gpiozero import LED, Button
        button2 = Button(2)
        button3 = Button(3)
        button4 = Button(4)
        
        button2.when_pressed = lambda: self.key_input('A', True)
        button2.when_released = lambda: self.key_input('a', False)
        button3.when_pressed = lambda: self.key_input('B', True)
        button3.when_released = lambda: self.key_input('b', False)
        button4.when_pressed = lambda: self.key_input('C', True)
        button4.when_released = lambda: self.key_input('c', False)

    def main_loop(self):
        while(True):
            time.sleep(1)
            print("...")

class PyGameInputter:
    def __init__(self):
        super(PyGameInputter, self).__init__()
        pygame.display.init()
        pygame.display.set_mode((100,100))

    def main_loop(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); #sys.exit() if sys is imported
                c = None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        c = 'A'
                    if event.key == pygame.K_b:
                        c = 'B'
                    if event.key == pygame.K_c:
                        c = 'C'
                    self.key_input(c, True)
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_q:
#                        if self.timer: self.timer.cancel()
#                        if self.relax_timer: self.relax_timer.cancel()
#                        return
                        sys.exit(0)
                    if event.key == pygame.K_a:
                        c = 'a'
                    if event.key == pygame.K_b:
                        c = 'b'
                    if event.key == pygame.K_c:
                        c = 'c'
                    self.key_input(c, False)

class BInputter:
    def __init__(self):
        super(BInputter, self).__init__()

    def main_loop(self):
        self.key_input('B', True)
        self.key_input('b', False)
        while True:
            time.sleep(1)

class MorseMaker:
    def __init__(self, down, up, t0, t1):
        self.down = down
        self.up = up
        self.t0 = t0
        self.t1 = t1

    def mkMorse(self, seq, l):
        s = ""
        i = "."
        for c in seq:
            if c == '.': s += i+self.down+"0-"+str(self.t0)   +"+"+self.up
            if c == '-': s += i+self.down+str(self.t0)+"-1000"+"+"+self.up
            i = "0-500"
        s += str(self.t1)+"-2000<match>"
        return KeyPress.compile(s, match=l)

    def mkAll(self, l):
        return [
            self.mkMorse(".-",   lambda: l("a")),
            self.mkMorse("-...", lambda: l("b")),
            self.mkMorse("-.-.", lambda: l("c")),
            self.mkMorse("-..",  lambda: l("d")),
            self.mkMorse(".",    lambda: l("e")),
            self.mkMorse("..-.", lambda: l("f")),
            self.mkMorse("--.",  lambda: l("g")),
            self.mkMorse("....", lambda: l("h")),
            self.mkMorse("..",   lambda: l("i")),
            self.mkMorse(".---", lambda: l("j")),
            self.mkMorse("-.-",  lambda: l("k")),
            self.mkMorse(".-..", lambda: l("l")),
            self.mkMorse("--",   lambda: l("m")),
            self.mkMorse("-.",   lambda: l("n")),
            self.mkMorse("---",  lambda: l("o")),
            self.mkMorse(".--.", lambda: l("p")),
            self.mkMorse("--.-", lambda: l("q")),
            self.mkMorse(".-.",  lambda: l("r")),
            self.mkMorse("...",  lambda: l("s")),
            self.mkMorse("-",    lambda: l("t")),
            self.mkMorse("..-",  lambda: l("u")),
            self.mkMorse("...-", lambda: l("v")),
            self.mkMorse(".--",  lambda: l("w")),
            self.mkMorse("-..-", lambda: l("x")),
            self.mkMorse("-.--", lambda: l("y")),
            self.mkMorse("--..", lambda: l("z")),
        ]


class KeyPressRunner:
    def __init__(self):
        super(KeyPressRunner, self).__init__()
        self.keys = 0
        self.key_press = None
        self.timer = None
        self.relax_timer = None

    def key_input(self, c, down):
        if down:
            self.keys = self.keys + 1
        else:
            self.keys = self.keys - 1
        self.times = self.key_press.process_input(c)
        self.process(0)

    def timer_stuff(self, this_time):
        self.timer = None
        self.times |= self.key_press.process_input(this_time)
        self.times = { x for x in self.times if x > this_time }
        self.process(this_time)

    def done_relaxing(self):
        self.relax_timer = None
        self.key_press.reset()

    def process(self, this_time):
        status = self.key_press.status()
        if status == "in progress":
            if self.times:
                next_time = min(self.times)
                if self.timer: self.timer.cancel()
                self.timer = Timer((next_time-this_time)/1000.0, lambda: self.timer_stuff(next_time))
                self.timer.start()
        else:
            if self.keys == 0:
                if status == "match":
                    self.key_press.reset()
                else:
                    if self.relax_timer: self.relax_timer.cancel()
                    self.relax_timer = Timer(1, self.done_relaxing)
                    self.relax_timer.start()


class ItTest(KeyPressRunner, PyGameInputter):
    def __init__(self):
        super(ItTest, self).__init__()
        morse_maker = MorseMaker('C', 'c', 200, 500)
        self.morseAlphbeth = KeyPress.mkUnion(morse_maker.mkAll(lambda c: print("=== %s" % c)) +
                [KeyPress.compile(".A.a<go_to_normal>", go_to_normal = lambda: self.go_normal())]
                )
        
        
        self.main_menu = KeyPress.mkUnion([
            KeyPress.compile(".A.C.c.a<go_to_morse>", go_to_morse=lambda: self.go_morse()),
            KeyPress.compile(".A.a<A>", A=lambda: print("A")),
            KeyPress.compile(".B.b<B>", B=lambda: print("B")),
        ])
        self.go_normal()

    def go_morse(self):
        print("going morse")
        self.key_press = KeyPress(self.morseAlphbeth)
    
    def go_normal(self):
        print("going normal")
        self.key_press = KeyPress(self.main_menu)

    def shut_down(self):
        pass


class RaspberryRadio(KeyPressRunner, PyGameInputter):
    def __init__(self):
        super(RaspberryRadio, self).__init__()
        self.comm = Comm("player", {})
        self.main_menu = KeyPress.mkUnion([
            KeyPress.compile(".A.a<match>", match=lambda: self.youtube_play()),
            KeyPress.compile(".B.b<match>", match=lambda: self.radio_play()),
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
        self.radio = Radio()
        self.multicast_receiver = MulticastReceiver()
        self.youtube = Youtube()
        self.go_to_main_menu()

    def go_to_main_menu(self):
        self.key_press = KeyPress(self.main_menu)

    def go_to_morse(self):
        print("going to morse...")
        self.key_press = KeyPress(self.morse_menu)
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

    def multicast_play(self, query):
        if query:
            print("requesting '%s'" % query)
            try:
                res = self.comm.call("music_server", "play", {"query": [query]})
                #res = requests.get('http://127.0.0.1:5002/play?query=%s' % query, timeout=2)
                print("res = %s" % res)
            except requests.ConnectionError as e:
                print("failed to send %s" % e)
        self.set_source("multicast")

    def youtube_play(self):
        self.set_source("youtube")

    def shut_down(self):
        self.set_source(None)

    def set_source(self, source):
        print("setting source: '%s'" % source)
        if source == "radio":
            self.multicast_receiver.stop()
            self.youtube.stop()
            self.radio.start()
        elif source == "multicast":
            self.radio.stop()
            self.youtube.stop()
            self.multicast_receiver.start()
        elif source == "youtube":
            self.radio.stop()
            self.multicast_receiver.stop()
            self.youtube.start()
        else:
            self.radio.stop()
            self.multicast_receiver.stop()
            self.youtube.stop()

class MulticastReceiver(object):
    def __init__(self):
        self.p = None

    def start(self):
        if self.p:
            self.stop()
        self.p = subprocess.Popen("vlc --intf dummy rtp://239.255.12.42", shell=True, stdout=devnull, stderr=devnull)

    def stop(self):
        if self.p == None:
            return
        self.p.terminate()
        self.p = None

class Radio(object):
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
        print("playing radio...")
        if self.p:
            self.stop()
        #self.p = subprocess.Popen("vlc --intf dummy %s" % self.channels[self.channel], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.check_output("printenv > bad" , shell=True)
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
        print(self.p.communicate())
        self.p = None

class Youtube:
    def __init__(self):
        self.p = None

    def start(self):
        print("playing youtube...")
        search = "metallica+hit+the+lights"
        if self.p:
            self.stop()

        p = subprocess.Popen("wget \"https://www.youtube.com/results?search_query=%s\" -O -" % search, shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        stdout, stderr = p.communicate()
        #print("stdout = '%s'" % stdout)
        print("stderr = '%s'" % stderr)
        m = re.search('href="/watch\?v=([^"]*)"', stdout.decode('ascii', errors="ignore"))
        #cvlc https://www.youtube.com/watch?v=863fYC-Mb_QI
        # /etc/portage/package.use/vlc :
        #media-video/vlc live lua matroska theora upnp
        # https://github.com/rg3/youtube-dl
        # python -m youtube_dl -x --audio-format mp3 gsoNl0MzDFA -o '%(artist)s - %(title)s.%(ext)s'
        # python -m youtube_dl ytsearch:"metallica jump in the fire" -o 'foo2'

        
        if m:
            print('First number found = {}'.format(m.group()))
            print('First number found = {}'.format(m[1]))
            print("cvlc https://www.youtube.com/watch?v=%s" % m[1])
            self.p = subprocess.Popen("cvlc --intf dummy https://www.youtube.com/watch?v=%s" % m[1], shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        else:
            print('Not Found')

    def stop(self):
        if self.p == None:
            return
        print("stopping youtube...")
        self.p.terminate()
        print(self.p.communicate())
        self.p = None

it_test = RaspberryRadio()
it_test.main_loop()
it_test.shut_down()
