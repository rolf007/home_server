#!/usr/bin/env python3

from emoji import EmojiParser
import os
import sys
import time
import unittest

class TestEmoji(unittest.TestCase):

    def setUp(self):
        pass

    def test_send(self):
        emoji = EmojiParser(lambda l: print("debug:", l))
        self.assertEqual('foo bar', emoji.send('foo bar'))
        self.assertEqual('foo \U0001f3c8', emoji.send('foo .foot ball.'))
        self.assertEqual('\U0001f42c \U0001f42c', emoji.send('.dolphin. .dolphin.'))
        self.assertEqual('\u2764\ufe0f', emoji.send('.h.'))

if __name__ == '__main__':
    unittest.main()