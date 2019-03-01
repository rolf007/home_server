#!/usr/bin/env python3

import os
import sys
import threading

home_server_root = os.path.split(sys.path[0])[0]
sys.path.append(os.path.join(home_server_root, "comm"))
sys.path.append(os.path.join(home_server_root, "keypress"))
sys.path.append(os.path.join(home_server_root, "utils"))
from comm import Comm
from keypress import KeyPress
from morse_maker import MorseMaker
from micro_service import MicroServiceHandler

class Radio():
    def __init__(self, logger, exc_cb, inputter):
        self.logger = logger
        self.comm = Comm(5000, "player", {}, self.logger, exc_cb)
        self.inputter = inputter
        self.menu_linger_time = 5.0
        self.main_menu = KeyPress.mkUnion([
            KeyPress.compile(".A.a<match>", match=lambda: self.go_to_playlist_menu()),
            KeyPress.compile(".B.b<match>", match=lambda: self.youtube_play("metallica judas kiss")),
            KeyPress.compile(".C.c<match>", match=lambda: self.go_to_radio_menu()),
            KeyPress.compile(".D.d<match>", match=lambda: self.multicast_play("for evigt")),
            KeyPress.compile(".E.e<match>", match=lambda: self.knightrider()),
            KeyPress.compile(".F.f<match>", match=lambda: self.go_to_podcast_menu()),
            KeyPress.compile(".H.h<match>", match=lambda: self.go_to_flow_menu()),

            #KeyPress.compile(".D.A.a.A.a.d<match>", match=lambda: self.podcast("orientering")),
            #KeyPress.compile(".B.A.a.b<match>", match=lambda: self.radio_channel(0)),
            #KeyPress.compile(".B.C.c.b<match>", match=lambda: self.radio_channel(1)),
            #KeyPress.compile(".C.c<match>", match=lambda: self.multicast_play(None)),
            #KeyPress.compile(".C.A.a.c<match>", match=lambda: self.multicast_play("DROID-3 plays tough!")),
            KeyPress.compile(".C.A.a.A.a.A.a.c<match>", match=lambda: self.go_to_morse()),
        ])
        self.radio_menu = KeyPress.mkUnion([
            KeyPress.compile(".A.a<match>", match=lambda: self.radio_channel("p1")),
            KeyPress.compile(".B.b<match>", match=lambda: self.radio_channel("p2")),
            KeyPress.compile(".C.c<match>", match=lambda: self.radio_channel("p3")),
            KeyPress.compile(".D.d<match>", match=lambda: self.radio_channel("24syv")),
        ])
        self.podcast_menu = KeyPress.mkUnion([
            KeyPress.compile(".A.a<match>", match=lambda: self.start_podcast("baelte")),
            KeyPress.compile(".B.b<match>", match=lambda: self.start_podcast("orientering")),
            KeyPress.compile(".C.c<match>", match=lambda: self.start_podcast("mads")),
            KeyPress.compile(".D.d<match>", match=lambda: self.start_podcast("d6m")),
        ])
        self.flow_menu = KeyPress.mkUnion([
            KeyPress.compile(".A.a<match>", match=lambda: self.flow({"to": ["0"]})),
            KeyPress.compile(".B.b<match>", match=lambda: self.flow({"prev": [1]})),
            KeyPress.compile(".C.c<match>", match=lambda: self.flow({"to": ["random"]})),
            KeyPress.compile(".D.d<match>", match=lambda: self.flow({"next": ["1"]})),
            KeyPress.compile(".E.e<match>", match=lambda: self.flow({"to": ["last"]})),
        ])
        self.playlist_menu = KeyPress.mkUnion([
            KeyPress.compile(".A.a<match>", match=lambda: self.go_to_users_playlist("karen")),
            KeyPress.compile(".B.b<match>", match=lambda: self.go_to_users_playlist("rolf")),
            KeyPress.compile(".C.c<match>", match=lambda: self.go_to_users_playlist("cecilia")),
            KeyPress.compile(".D.d<match>", match=lambda: self.go_to_users_playlist("helena")),
            KeyPress.compile(".E.e<match>", match=lambda: self.go_to_users_playlist("adam")),
            KeyPress.compile(".F.f<match>", match=lambda: self.go_to_users_playlist("samuel")),
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
        self.go_to_main_menu()

    def go_to_main_menu(self):
        print("going to main menu...")
        self.inputter.set_key_press(KeyPress(self.main_menu))
        self.startup_timer = None

    def go_to_morse(self):
        print("going to morse...")
        self.inputter.set_key_press(KeyPress(self.morse_menu))
        self.morse_input = ""

    def end_morse(self):
        self.go_to_main_menu()
        self.multicast_play(self.morse_input)

    def morse_append(self, c):
        print("=== %s" % c)
        self.morse_input += c

    def radio_channel(self, channel):
        print("setting radio channel %s" % channel)
        self.inputter.click_NAD_button(1)
        res = self.comm.call("stream_receiver", "radio", {"channel": [channel]})
        res = self.comm.call("led", "set", {"anim": ["tu"]})

    def go_to_radio_menu(self):
        res = self.comm.call("led", "set", {"anim": ["tu"]})
        res = self.comm.call("led", "set", {"anim": ["radio_menu"]})
        res = self.comm.call("stream_receiver", "radio", {})
        self.inputter.set_key_press(KeyPress(self.radio_menu))
        self.startup_timer = threading.Timer(self.menu_linger_time, self.leave_submenu)
        self.startup_timer.start()

    def go_to_podcast_menu(self):
        res = self.comm.call("led", "set", {"anim": ["podcast_menu"]})
        res = self.comm.call("music_server", "podcast", {})
        res = self.comm.call("stream_receiver", "multicast", {})
        self.inputter.set_key_press(KeyPress(self.podcast_menu))
        self.startup_timer = threading.Timer(self.menu_linger_time, self.leave_submenu)
        self.startup_timer.start()

    def go_to_flow_menu(self):
        res = self.comm.call("led", "set", {"anim": ["flow_menu"]})
        self.inputter.set_key_press(KeyPress(self.flow_menu))
        self.startup_timer = threading.Timer(self.menu_linger_time, self.leave_submenu)
        self.startup_timer.start()

    def go_to_playlist_menu(self):
        res = self.comm.call("led", "set", {"anim": ["playlist_menu"]})
        res = self.comm.call("stream_receiver", "multicast", {})
        self.inputter.set_key_press(KeyPress(self.playlist_menu))
        self.startup_timer = threading.Timer(self.menu_linger_time, self.leave_submenu)
        self.startup_timer.start()

    def go_to_users_playlist(self, user):
        if self.startup_timer != None:
            self.startup_timer.cancel
        self.startup_timer = threading.Timer(self.menu_linger_time, self.leave_submenu)
        self.startup_timer.start()

    def leave_submenu(self):
        res = self.comm.call("led", "set", {"anim": ["clear_submenu"]})
        self.go_to_main_menu()

    def radio_play(self):
        print("playing radio")
        self.inputter.click_NAD_button(1)
        res = self.comm.call("stream_receiver", "radio", {})
        res = self.comm.call("led", "set", {"anim": ["tu"]})

    def flow(self, skip):
        res = self.comm.call("music_server", "skip", skip)

    def start_podcast(self, program):
        res = self.comm.call("led", "set", {"anim": ["vi_wait"]})
        if program:
            print("requesting program '%s'" % program)
            try:
                res = self.comm.call("music_server", "podcast", {"program": [program]})
                print("res = %d %s" % res)
            except requests.ConnectionError as e:
                print("failed to send %s" % e)
        self.inputter.click_NAD_button(1)
        res = self.comm.call("stream_receiver", "multicast", {})
        res = self.comm.call("led", "set", {"anim": ["vi"]})

    def multicast_play(self, title):
        if title:
            print("requesting '%s'" % title)
            try:
                res = self.comm.call("music_server", "play", {"artist": ["volbeat"], "title": [title]})
                print("res = %d %s" % res)
            except requests.ConnectionError as e:
                print("failed to send %s" % e)
        self.inputter.click_NAD_button(1)
        res = self.comm.call("stream_receiver", "multicast", {})
        res = self.comm.call("led", "set", {"anim": ["mp"]})

    def knightrider(self):
        print("knightrider!")
        res = self.comm.call("led", "set", {"anim": ["knightrider"]})

    def youtube_play(self, query):
        if query:
            print("requesting '%s'" % query)
            try:
                res = self.comm.call("music_server", "play", {"query": [query], "source": "youtube"})
                print("res = %d %s" % res)
            except requests.ConnectionError as e:
                print("failed to send %s" % e)
        self.inputter.click_NAD_button(1)
        res = self.comm.call("stream_receiver", "multicast", {})
        res = self.comm.call("led", "set", {"anim": ["mp"]})

    def shut_down(self):
        if self.startup_timer != None:
            self.startup_timer.cancel()
        self.comm.shut_down()
        self.inputter.shut_down()

if __name__ == '__main__':
    try:
        from raspberry_inputter import RaspberryInputter
        inputter = RaspberryInputter()
    except (ImportError, RuntimeError):
        from pygame_inputter import PyGameInputter
        inputter = PyGameInputter()
    MicroServiceHandler("radio", Radio, inputter)
