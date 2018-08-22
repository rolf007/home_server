#!/usr/bin/env python

#https://wiki.videolan.org/Documentation:Streaming_HowTo/Advanced_Streaming_Using_the_Command_Line/#Examples
#import unicodedata
#print(unicodedata.name(chr(128514)))
#FACE WITH TEARS OF JOY

import subprocess
import os
import sys
import json
import eyed3

from time import strftime, localtime, sleep

import time
import socket
from os import listdir
from os.path import isfile, join

from flask import Flask, request
app = Flask(__name__)

import threading
import requests

sys.path.append("../server_shared")
import server_shared

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

my_port = 5002
my_ip = server_shared.get_ip()
my_commands = ["play"]
sms_portal_ip = ""
sms_portal_port = 0

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


def send_sms(text):
    print("sending sms '%s'..." % text)
    if sms_portal_ip == "" or sms_portal_port == 0:
        print("Can't send sms. Sms portal ip/port unknown %s:%d" % (sms_portal_ip, sms_portal_port))
        return
    try:
        res = requests.get('http://%s:%d/send_sms?body=%s' % (sms_portal_ip, sms_portal_port, text), timeout=2)
    except requests.ConnectionError as e:
        print("failed to send %s" % e)

def ip_went_online(name):
    send_sms("%s%%20went%%20online" % name)

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

class BroadcastListener(object):
    def __init__(self, interval=1):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.client.bind(("", 37020))

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self):
        sleep(4)
        while True:
            data, addr = self.client.recvfrom(1024)
            data = data.decode('ascii')
            sms_portal = "sms_portal: "
            if data.startswith(sms_portal):
                d = json.loads(data[len(sms_portal):])
                global sms_portal_ip
                global sms_portal_port
                sms_portal_ip = d["ip"]
                sms_portal_port = d["port"]
                dictToSend = {'commands':my_commands, 'port':my_port, 'ip':my_ip}
                try:
                    res = requests.get("http://%s:%d/register_service" % (sms_portal_ip, sms_portal_port), json=dictToSend, timeout=2)
                except requests.ConnectionError as e:
                    print("failed to send %s" % e)

def scan_collection():
    mypath = "/home/rolf/Downloads"
    urls = [os.path.join(mypath, f) for f in listdir(mypath) if isfile(join(mypath, f)) and f.endswith(".mp3")]
    for url in urls:
        audiofile = eyed3.load(url)
        music_collection.append({"title":audiofile.tag.title, "artist":audiofile.tag.artist, "url":"file://"+url})


scan_collection()


#http://127.0.0.1:5002/play?query=hello
@app.route("/play")
def hello():
    query = request.args.get('query')
    best_match = {}
    best_score = -1.0
    for music in music_collection:
        title = music["title"]
        score = fuzzy_substring(query.lower(), title.lower())
        if score < best_score or best_score == -1.0:
            best_score = score
            best_match = music
    subprocess.call("qdbus org.mpris.MediaPlayer2.vlc /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.OpenUri %s" % best_match["url"], shell=True, stdout=devnull)
    print("playing: '" + best_match["artist"] + " - " + best_match["title"] + "' (" + best_match["url"] + ")")
    return "playing: '" + best_match["artist"] + " - " + best_match["title"] + "'"


if __name__ == '__main__':
    vlc_thread = VlcThread()
    broadcastListener = BroadcastListener();
    app.run(host="0.0.0.0", port=my_port, threaded=True)
