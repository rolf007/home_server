#!/usr/bin/env python

#https://wiki.videolan.org/Documentation:Streaming_HowTo/Advanced_Streaming_Using_the_Command_Line/#Examples
#import unicodedata
#print(unicodedata.name(chr(128514)))
#FACE WITH TEARS OF JOY
#emerge -av1 qdbus

import subprocess
import os
import sys
import json
import eyed3

from time import strftime, localtime, sleep

import time
from os import listdir
from os.path import isfile, join


import threading

sys.path.append("../comm")
from comm import Comm

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

#my_ip = server_shared.get_ip()

devnull = open(os.devnull, 'w')

music_collection = [
    {"artist":"metallica", "title":"orion"},
    {"artist":"metallica", "title":"for whom the bells toll"},
    {"artist":"acdc",      "title":"for those about to rock"},
    ]

def fuzzy_substring(needle, haystack):
    """Calculates the fuzzy match of needle in haystack,
    using a modified version of the Levenshtein distance
    algorithm.
    The function is modified from the levenshtein function
    in the bktree module by Adam Hupp"""

    m, n = len(needle), len(haystack)

    # base cases
    if m == 1:
        return not needle in haystack
    if not n:
        return m

    row1 = [0] * (n+1)
    for i in range(0,m):
        row2 = [i+1]
        for j in range(0,n):
            cost = ( needle[i] != haystack[j] )

            row2.append( min(row1[j+1]+1, # deletion
                               row2[j]+1, #insertion
                               row1[j]+cost) #substitution
                           )
        row1 = row2
    return min(row1)


class VlcThread(object):
    def __init__(self):

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self):
        subprocess.call("vlc -vvv  --intf dummy --sout '#transcode{acodec=mpga,ab=128}:rtp{mux=ts,dst=239.255.12.42,sdp=sap,name=\"TestStream\"}'", shell=True, stdout=devnull, stderr=devnull)
        print("VLC unexpectedly exited")
        #playback:
        #vlc rtp://239.255.12.42
        #play:
        #qdbus org.mpris.MediaPlayer2.vlc /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.OpenUri file:///home/rolf/Downloads/droid3_newfirmware.mp3


def scan_collection():
    music_collection = []
    mypath = "/home/rolf/sfx"
    urls = [os.path.join(mypath, f) for f in listdir(mypath) if isfile(join(mypath, f)) and f.endswith(".mp3")]
    for url in urls:
        audiofile = eyed3.load(url)
        if audiofile.tag:
            print("found : %s - %s (%s)" % ( audiofile.tag.artist, audiofile.tag.title, url))
            music_collection.append({"title":audiofile.tag.title, "artist":audiofile.tag.artist, "url":"file://"+url})
    return music_collection


music_collection = scan_collection()


#http://127.0.0.1:5002/play?query=sanitarium
def play(params):
    print("play: '%s'" % params[b"query"][0].decode('ascii'))
    query = params[b"query"][0].decode('ascii')
    best_match = {}
    best_score = -1.0
    for music in music_collection:
        title = music["title"]
        if not title:
            continue
        score = fuzzy_substring(query.lower(), title.lower())
        print("score = %s (%s)" % (score, title))
        if score < best_score or best_score == -1.0:
            best_score = score
            best_match = music
    if "artist" in best_match:
        print("artist: '%s'" % best_match["artist"])
    if "title" in best_match:
        print("title: '%s'" % best_match["title"])
    if "url" in best_match:
        print("url: '%s'" % best_match["url"])
        subprocess.call("qdbus org.mpris.MediaPlayer2.vlc /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.OpenUri \"%s\"" % best_match["url"], shell=True, stdout=devnull)
        return "playing: '" + best_match["artist"] + " - " + best_match["title"] + "'"
    return "no url!"


if __name__ == '__main__':
    vlc_thread = VlcThread()
    comm = Comm("music_server", {"play": play})
    while True:
        time.sleep(2.0)
