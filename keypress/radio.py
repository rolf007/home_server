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
from micro_service import MicroServiceHandler

class Radio():
    def __init__(self, logger, exc_cb, inputter):
        self.logger = logger
        self.comm = Comm(5000, "buttons", {}, self.logger, exc_cb)
        self.inputter = inputter
        self.menu_linger_time = 5.0
        self.main_menu = KeyPress.mkUnion([
            KeyPress.compile(".A.a<match>", match=lambda: self.go_to_playlist_menu()),
            KeyPress.compile(".B.b<match>", match=lambda: self.multicast_play({"artist": ["bryan adams"], "title": ["summer of 69"]})),
            KeyPress.compile(".C.c<match>", match=lambda: self.go_to_radio_menu()),
            KeyPress.compile(".D.d<match>", match=lambda: self.multicast_play({"artist": ["volbeat"], "title": ["for evigt"]})),
            KeyPress.compile(".E.e<match>", match=lambda: self.knightrider()),
            KeyPress.compile(".F.f<match>", match=lambda: self.go_to_podcast_menu()),
            KeyPress.compile(".H.h<match>", match=lambda: self.go_to_flow_menu()),
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
            KeyPress.compile(".A.a<match>", match=lambda: self.go_to_users_playlist_menu("user_k")),
            KeyPress.compile(".B.b<match>", match=lambda: self.go_to_users_playlist_menu("user_r")),
            KeyPress.compile(".C.c<match>", match=lambda: self.go_to_users_playlist_menu("user_c")),
            KeyPress.compile(".D.d<match>", match=lambda: self.go_to_users_playlist_menu("user_h")),
            KeyPress.compile(".E.e<match>", match=lambda: self.go_to_users_playlist_menu("user_a")),
            KeyPress.compile(".F.f<match>", match=lambda: self.go_to_users_playlist_menu("user_s")),
        ])
        self.user_playlist_menu = {}
        self.user_playlist_menu["user_k"] = KeyPress.mkUnion([
            KeyPress.compile(".A.a<match>", match=lambda: self.multicast_play({"source":"list", "query":"svensk"})),
        ])
        self.user_playlist_menu["user_r"] = KeyPress.mkUnion([
            KeyPress.compile(".A.a<match>", match=lambda: self.multicast_play({"source":"list", "query":"metal"})),
        ])
        self.user_playlist_menu["user_c"] = KeyPress.mkUnion([
        ])
        self.user_playlist_menu["user_h"] = KeyPress.mkUnion([
        ])
        self.user_playlist_menu["user_a"] = KeyPress.mkUnion([
        ])
        self.user_playlist_menu["user_s"] = KeyPress.mkUnion([
        ])
        print("==== press 'A' for playlists")
        print("==== press 'B' for youtube play")
        print("==== press 'C' for radio")
        print("==== press 'D' for Volbeat - For Evigt")
        print("==== press 'E' for Knight Rider")
        print("==== press 'F' for Pod cast")
        print("==== press 'H' for Flow control")
        print("==== press 'q' to quit")
        self.go_to_main_menu()
        self.inputter.click_NAD_button(1)

    def go_to_main_menu(self):
        print("going to main menu...")
        self.inputter.set_key_press(KeyPress(self.main_menu))
        self.startup_timer = None

    def go_to_playlist_menu(self):
        res = self.comm.call("led", "set", {"anim": ["playlist_menu"]})
        res = self.comm.call("stream_receiver", "multicast", {})
        self.inputter.set_key_press(KeyPress(self.playlist_menu))
        self.startup_timer = threading.Timer(self.menu_linger_time, self.leave_submenu)
        self.startup_timer.start()

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
#---
    def go_to_users_playlist_menu(self, user):
        res = self.comm.call("led", "set", {"anim": [user + "_menu"]})
        self.inputter.set_key_press(KeyPress(self.user_playlist_menu[user]))
        if self.startup_timer != None:
            self.startup_timer.cancel()
        self.startup_timer = threading.Timer(self.menu_linger_time, self.leave_submenu)
        self.startup_timer.start()
#---
    def leave_submenu(self):
        if self.startup_timer != None:
            self.startup_timer.cancel()
            self.startup_timer = None
        res = self.comm.call("led", "set", {"anim": ["clear_submenu"]})
        self.go_to_main_menu()

    def multicast_play(self, query):
        self.inputter.click_NAD_button(1)
        print("requesting '%s'" % query)
        res = self.comm.call("music_server", "play", query)
        print("res = %d %s" % res)
        res = self.comm.call("stream_receiver", "multicast", {})
        res = self.comm.call("led", "set", {"anim": ["mp"]})
        self.leave_submenu()

    def radio_channel(self, channel):
        self.inputter.click_NAD_button(1)
        res = self.comm.call("stream_receiver", "radio", {"channel": [channel]})
        res = self.comm.call("led", "set", {"anim": ["tu"]})
        self.leave_submenu()

    def start_podcast(self, program):
        self.inputter.click_NAD_button(1)
        res = self.comm.call("led", "set", {"anim": ["vi_wait"]})
        print("requesting program '%s'" % program)
        res = self.comm.call("music_server", "podcast", {"program": [program]})
        print("res = %d %s" % res)
        res = self.comm.call("stream_receiver", "multicast", {})
        res = self.comm.call("led", "set", {"anim": ["vi"]})
        self.leave_submenu()

    def flow(self, skip):
        res = self.comm.call("music_server", "skip", skip)
        self.leave_submenu()

    def knightrider(self):
        print("knightrider!")
        res = self.comm.call("led", "set", {"anim": ["knightrider"]})

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
    MicroServiceHandler("buttons", Radio, inputter)
