#!/usr/bin/env python3

from music_server import VlcThread
from logger import Logger
import unittest
import time
import os
import sys

class TestLogger():
    def log(self, s):
        print("TestLogger: %s" % s)
        pass

home_server_root = os.path.split(sys.path[0])[0]
class TestVlcThread(unittest.TestCase):

    def setUp(self):
        logger = TestLogger()
        self.vlc_thread = VlcThread(logger)
        self.assertEqual("stopped", self.vlc_thread.get_status())

    def tearDown(self):
        self.vlc_thread.shut_down()
        time.sleep(1)

    def test_enqueue_at_end_of_playlist__q(self):
        pass

    def test_clear_playlist_Then_play_this__c(self):
        pass

    def test_play_NOW__n(self):
        pass

    def test_play_next__x(self):
        pass

    def test_simple_enqueue(self):
        self.vlc_thread.enqueue([os.path.join(home_server_root, "1.mp3")], 'c')
        time.sleep(1)
        self.vlc_thread.enqueue([os.path.join(home_server_root, "1.mp3")], 'q')
        time.sleep(1)
        #debug = self.vlc_thread.debug_playlist()
        #print(debug)

        self.assertEqual("playing", self.vlc_thread.get_status())
        self.assertEqual([3,4], self.vlc_thread.get_playlist())
        self.assertEqual("1.mp3", self.vlc_thread.get_filename(3))
        self.assertEqual("1.mp3", self.vlc_thread.get_filename(4))

if __name__ == '__main__':
    unittest.main()
