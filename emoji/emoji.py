#!/usr/bin/env python3

import unicodedata
import os
import sys
import time

home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])
sys.path.append(os.path.join(home_server_root, "comm"))
sys.path.append(os.path.join(home_server_root, "logger"))
sys.path.append(os.path.join(home_server_root, "utils"))
from comm import Comm
from logger import Logger
from fuzzy_substring import fuzzy_substring
#import unicodedata
#print(unicodedata.name(chr(128514)))
#FACE WITH TEARS OF JOY
# UNICODE FACE
# &#129412;
# &#x1F984;
# %F0%9F%A6%84

class EmojiParser():
    def __init__(self, logger):
        self.logger = logger
        self.blocks = [
            #(0x13000, 0x1342F, "Egyptian Hieroglyphs"),
            (0x1F300, 0x1F600, "Miscellaneous Symbols and Pictographs"),
            (0x1F600, 0x1F650, "Emoticons"),
            (0x1F680, 0x1F700, "Transport and Map Symbols"),
            (0x1F900, 0x1FA00, "Supplemental Symbols and Pictographs")# <- unicorn goes here
            ]
        self.shortcuts = {
                'h': chr( 0x2764) + chr(0xfe0f),#heart
                'u': chr(0x1F984),#unicorn
                's': chr(0x1F642),#smile
                'g': chr(0x1F641),#grief
                'b': chr(0x1F6B4),#bike
                }

    def send(self, text):
        ret = ""
        i = 0
        while i < len(text):
            if text[i] == '.' and i+1 < len(text) and text[i+1].isalpha():
                i, name = self.parse(i+1, text)
                ret += name
            else:
                ret += text[i]
                i = i + 1
        return ret

    def parse(self, i, text):
        h = i
        while i < len(text) and text[i] != '.':
            i = i + 1
        query = text[h:i]
        if query in self.shortcuts:
            return i+1, self.shortcuts[query]
        best_match = "?"
        best_score = -1
        best_len = -1
        for block in self.blocks:
            for u in range(block[0], block[1]):
                try:
                    name = unicodedata.name(chr(u))
                    score = fuzzy_substring(query.lower(), name.lower())
                    if score < best_score or best_score == -1 or (score == best_score and len(name) < best_len)
                        best_score = score
                        best_match = chr(u)
                        best_len = len(name)
                except:
                    pass
        self.logger(unicodedata.name(best_match))
        return i+1, best_match

class Emoji():

    def __init__(self):
        self.logger = Logger("emoji")
        self.logger.log("Started emoji")
        self.comm = Comm(5004, "emoji", {"receive": self.receive, "send": self.send}, self.logger)
        self.emoji_parser = EmojiParser(self.logger.log)
    # http://127.0.0.1:5004/receive?text=uni%F0%9F%A6%84corn
    def receive(self, params):
        if "text" not in params:
            return (404, "function 'receive' requires 'text'")
        text = params["text"][0]
        ret = ""
        for c in text:
            if ord(c) >=32 and ord(c) < 254:
                ret += c;
            else:
                ret += '.' + unicodedata.name(c) + '.'
        return (200, "%s" % ret)

    # http://127.0.0.1:5004/send?text=See this. uni.UNICORN FACE.corn. I know you liked it.
    def send(self, params):
        if "text" not in params:
            return (404, "function 'send' requires 'text'")
        text = params["text"][0]
        ret = self.emoji_parser.send(text)

        self.logger.log("emoji send %s" % ret)
        return (200, "%s" % ret)


    def shut_down(self):
        self.comm.shut_down()

if __name__ == '__main__':
    emoji = Emoji()
    try:
        while True:
            time.sleep(2.0)
    except KeyboardInterrupt:
        pass
    emoji.shut_down()
