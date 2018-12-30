#!/usr/bin/env python3

#https://wiki.videolan.org/Documentation:Streaming_HowTo/Advanced_Streaming_Using_the_Command_Line/#Examples
#import unicodedata
#print(unicodedata.name(chr(128514)))
#FACE WITH TEARS OF JOY
#pip install --user eyed3
#pip install --user youtube_dl


import subprocess
import os
import sys
import eyed3
import json
import time
from os import listdir
from os.path import isfile, join
import re
import youtube_dl

home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])
sys.path.append(os.path.join(home_server_root, "comm"))
from comm import Comm

devnull = open(os.devnull, 'w')

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


class VlcThread():
    def __init__(self):
        print("starting serving music...")
        self.filename = None
        self.p = subprocess.Popen("vlc --intf rc --sout '#transcode{acodec=mpga,ab=128}:rtp{mux=ts,dst=239.255.12.42,sdp=sap,name=\"TestStream\"}'", shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, preexec_fn=os.setsid, close_fds=True)


    def play(self, filename):
        self.filename = filename
        self.p.stdin.write(bytes('add file://%s\n' % filename, "ascii"))
        self.p.stdin.flush()

    def get_current_file(self):
        return self.filename

    def stop(self):
        self.filename = None
        if self.p == None:
            return
        print("stopping serving music...")
        self.p.terminate()
        print(self.p.communicate())
        self.p = None


def load_collection():
    collection_path = os.path.join(home_server_config, "collections")
    music_collection = {}

    directory = os.fsencode(collection_path)
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(b'.json'):
                full_path = os.path.join(root, file)
                with open(full_path) as f:
                    music_collection = {**music_collection, **json.load(f)}
    return music_collection


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')

class Podcaster():
    def __init__(self):
        self.episodes = None
        self.cur_episode = None
        self.program_name = None

    def podcast(self, params):
        programs = {
            "d6m": {
                "name": "Den_Sjete_Masseuddoen",
                "url": "https://arkiv.radio24syv.dk/audiopodcast/channel/27580524",
                "regex": "<enclosure url=\"(https://arkiv.radio24syv.dk/.*/.*/.*/audio/podcast/.*-audio.(?:mp3|m4a))\"",
            }, "baelte": {
                "name": "Baeltestedet",
                "url": "https://arkiv.radio24syv.dk/audiopodcast/channel/8741566",
                "regex": "<enclosure url=\"(https://arkiv.radio24syv.dk/.*/.*/.*/audio/podcast/.*-audio.(?:mp3|m4a))\"",
            }, "orientering": {
                "name": "Orientering",
                "url": "https://www.dr.dk/mu/feed/orientering.xml?format=podcast&limit=500",
                "regex": "<enclosure url=\"(https://www.dr.dk/mu/MediaRedirector/WithFileExtension/.*.mp3\\?highestBitrate=True&amp;podcastDownload=True)\"",
            }, "mads": {
                "name": "Mads_og_Monopolet",
                "url": "https://www.dr.dk/mu/Feed/mads-monopolet-podcast?format=podcast&limit=500",
                "regex": "<enclosure url=\"(https://www.dr.dk/mu/MediaRedirector/WithFileExtension/.*.mp3\\?highestBitrate=True&amp;podcastDownload=True)\"",
            }
        }

        if "program" in params:
            program = params["program"][0]
            if program in programs:
                program_info = programs[program]
                p = subprocess.Popen("wget \"%s\" -O -" % program_info["url"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = p.communicate()
                if p.returncode != 0:
                    return (404, "Failed to get info page"), None
                self.episodes = re.findall(program_info["regex"], stdout.decode('ascii', 'ignore'))
                self.episodes.reverse()
                self.program_name = program_info["name"]
                if "episode" in params:
                    self.cur_episode = int(params["episode"][0])
                else:
                    self.cur_episode = len(self.episodes) - 1
                if self.cur_episode >= 0 and self.cur_episode < len(self.episodes):
                    return self.download_podcast()
                else:
                    return (404, "No episodes found"), None
            else:
                return (404, "Unknown podcast program '%s'" % program), None
        elif "next"  in params:
            if self.episodes == None:
                return (404, "no current podcast program"), None
            if self.cur_episode >= len(self.episodes)-1:
                return (404, "no newer programs"), None
            self.cur_episode += 1
            return self.download_podcast()
        elif "prev"  in params:
            if self.episodes == None:
                return (404, "no current podcast program"), None
            if self.cur_episode <= 0:
                return (404, "no older programs"), None
            self.cur_episode -= 1
            return self.download_podcast()
        else:
            return (404, "Unknown podcast query: '%s'" % params), None

    def download_podcast(self):
        filename = os.path.join(home_server_root, "%s_-_episode_%d" % (self.program_name, self.cur_episode))
        if os.path.isfile(filename):
            print("File '%s' already exists" % filename)
            return (200, "Found '%d' episodes. Starting program '%s'" % (len(self.episodes), self.program_name)), filename
        print("downloading '%s' -> '%s'" % (self.episodes[self.cur_episode], filename))
        p = subprocess.Popen("wget \"%s\" -O %s" % (self.episodes[self.cur_episode], filename), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        print("downloading done!")
        if p.returncode != 0:
            return (404, "Failed to get sound file"), None
        return (200, "Found '%d' episodes. Starting program '%s'" % (len(self.episodes), self.program_name)), filename


class MusicServer():
    def __init__(self):
        self.music_collection = load_collection()
        print("music_collection = '%s'" % self.music_collection)
        self.vlc_thread = VlcThread()
        self.podcaster = Podcaster()
        self.comm = Comm(5001, "music_server", {"play": self.play, "podcast": self.podcast, "tag": self.tag})

    def enqueue_file(self, filename, params):
        print("now enqueueing! '%s'" % filename)
        self.vlc_thread.play(filename)

    def podcast(self, params):
        ret, filename = self.podcaster.podcast(params)
        if filename:
            self.enqueue_file(filename, params)
        return ret

#http://127.0.0.1:5001/tag?star=5
#http://127.0.0.1:5001/tag?instrumetal=1
#http://127.0.0.1:5001/tag?christmas=1
    def tag(self, params):
        print("tagging '%s'" % params)
        filename = self.vlc_thread.get_current_file()
        if filename == None:
            return (404, "nothing to tag")
        print("tagging '%s' with '%s'" % (filename, params))
        if not os.path.exists(home_server_config):
            os.mkdir(home_server_config)
        with open(os.path.join(home_server_config, "custom_tags.txt"), 'a+') as f:
            for key, value in params.items():
                f.write('"%s": {"%s": "%s"},\n' % (filename, key, value[0]))
        return (200, "tagging ok")

#http://127.0.0.1:5001/play?query=sanitarium
    def play(self, params):
        if "query" not in params:
            return (404, "'query' is a required argument to 'play'")
        if ("source" in params):
            source = params["source"][0]
        else:
            source = "collection"
        if source == "collection":
            return self.play_collection(params)
        if source == "youtube":
            return self.play_youtube(params)
        return (404, "Source must be 'collection' or 'youtube'")

    def play_collection(self, params):
        query = params["query"][0]
        print("play: '%s'" % query)
        best_match = {}
        best_score = -1
        for music in self.music_collection:
            title = music["title"]
            if not title:
                continue
            score = fuzzy_substring(query.lower(), title.lower())
            print("score = %s (%s)" % (score, title))
            if score < best_score or best_score == -1.0 and ("url" in music):
                best_score = score
                best_match = music
        if best_score == -1:
            return (404, "Music collection seems to be empty")
        artist = "unknown" if "artist" not in best_match else best_match["artist"]
        title = "unknown" if "title" not in best_match else best_match["title"]
        url = best_match["url"]
        print("artist: '%s'" % artist)
        print("title: '%s'" % title)
        print("url: '%s'" % url)
        self.enqueue_file(best_match["url"], params)
        return (200, "playing: '" + artist + " - " + title + "'")

    def filify(self, s):
        return s.replace(' ','_').replace('/','_')

    def play_youtube(self, params):
        # https://github.com/rg3/youtube-dl
        # python -m youtube_dl -x --audio-format mp3 gsoNl0MzDFA -o '%(artist)s - %(title)s.%(ext)s'
        # python -m youtube_dl ytsearch:"metallica jump in the fire" -o 'foo2'
        #https://github.com/rg3/youtube-dl/commit/6d7359775ae4eef1d1213aae81e092467a2c675c
        query = params["query"][0]
        print("play: '%s'" % query)

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'yt.%(ext)s',
            'logger': MyLogger(),
            'progress_hooks': [my_hook],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info('ytsearch:%s' % query, ie_key='YoutubeSearch')
            e0 = info["entries"][0]
            artist = "unknown" if "artist" not in e0 or e0["artist"] == None else e0["artist"].encode('ascii', 'ignore')
            alt_title = None if "alt_title" not in e0 or e0["alt_title"] == None else e0["alt_title"].encode('ascii', 'ignore')
            if alt_title:
                title = alt_title
            else:
                title = "unknown" if "title" not in e0 else e0["title"]
            if type(artist) == bytes: artist = artist.decode('ascii', 'ignore')
            if type(title) == bytes: title = title.decode('ascii', 'ignore')
            print("playing %s - %s" % (artist, title))
        filename = os.path.join(home_server_root, "%s_-_%s.mp3" % (self.filify(artist), self.filify(title)))
        os.rename("yt.mp3", filename)
        self.enqueue_file(filename, params)

        return (200, "playing %s - %s" % (artist, title))


    def shut_down(self):
        print("music_server shutting down!")
        self.vlc_thread.stop()
        self.comm.shut_down()
        print("music_server shutted down!")

music_server = MusicServer()
try:
    while True:
        time.sleep(2.0)
except KeyboardInterrupt:
    pass
music_server.shut_down()
