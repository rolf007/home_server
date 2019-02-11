import os
import sys

home_server_root = os.path.split(sys.path[0])[0]
sys.path.append(os.path.join(home_server_root, "comm"))
sys.path.append(os.path.join(home_server_root, "keypress"))
sys.path.append(os.path.join(home_server_root, "logger"))
from comm import Comm
from keypress import KeyPress
from morse_maker import MorseMaker
from logger import Logger

class Radio():
    def __init__(self, inputter):
        self.logger = Logger("radio")
        self.logger.log("Started radio")
        self.comm = Comm(5000, "player", {}, self.logger)
        self.inputter = inputter
        self.main_menu = KeyPress.mkUnion([
            #KeyPress.compile(".A.a<match>", match=lambda: self.multicast_play("DROID-3 new firmware")),
            KeyPress.compile(".A.a<match>", match=lambda: self.multicast_play("for evigt")),
            KeyPress.compile(".B.b<match>", match=lambda: self.youtube_play("metallica judas kiss")),
            KeyPress.compile(".C.c<match>", match=lambda: self.radio_play()),
            KeyPress.compile(".D.d<match>", match=lambda: self.podcast("d6m")),
            KeyPress.compile(".E.e<match>", match=lambda: self.knightrider()),
            KeyPress.compile(".F.f<match>", match=lambda: self.podcast("baelte")),
            #KeyPress.compile(".D.A.a.A.a.d<match>", match=lambda: self.podcast("orientering")),
            #KeyPress.compile(".D.C.c.d<match>", match=lambda: self.podcast_next()),
            #KeyPress.compile(".D.B.b.d<match>", match=lambda: self.podcast_prev()),
            #KeyPress.compile(".B.A.a.b<match>", match=lambda: self.radio_channel(0)),
            #KeyPress.compile(".B.C.c.b<match>", match=lambda: self.radio_channel(1)),
            #KeyPress.compile(".C.c<match>", match=lambda: self.multicast_play(None)),
            #KeyPress.compile(".C.A.a.c<match>", match=lambda: self.multicast_play("DROID-3 plays tough!")),
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
        self.go_to_main_menu()

    def go_to_main_menu(self):
        print("going to main menu...")
        self.inputter.set_key_press(KeyPress(self.main_menu))

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
        self.inputter.click_NAD_button(1)
        res = self.comm.call("stream_receiver", "radio", {channel})
        res = self.comm.call("led", "set", {"anim": ["tu"]})

    def radio_play(self):
        print("playing radio")
        self.inputter.click_NAD_button(1)
        res = self.comm.call("stream_receiver", "radio", {})
        res = self.comm.call("led", "set", {"anim": ["tu"]})

    def podcast(self, program):
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

    def podcast_next(self):
        try:
            res = self.comm.call("music_server", "podcast", {"next": [1]})
            print("res = %d %s" % res)
        except requests.ConnectionError as e:
            print("failed to send %s" % e)
        self.inputter.click_NAD_button(1)
        res = self.comm.call("stream_receiver", "multicast", {})
        res = self.comm.call("led", "set", {"anim": ["vi"]})

    def podcast_prev(self):
        try:
            res = self.comm.call("music_server", "podcast", {"prev": [1]})
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

    def main_loop(self):
        self.inputter.main_loop()

    def shut_down(self):
        self.comm.shut_down()
        self.inputter.shut_down()
