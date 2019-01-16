#!/usr/bin/env python3

#https://wiki.videolan.org/Documentation:Streaming_HowTo/Advanced_Streaming_Using_the_Command_Line/#Examples
#/etc/portage/package.use/vlc:
#media-video/vlc lua
#pip install --user eyed3
#pip install --user youtube_dl


import subprocess
import os
import sys
import eyed3
import fcntl
import json
import time
from os import listdir
from os.path import isfile, join
import pty
import re
import youtube_dl


home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])
sys.path.append(os.path.join(home_server_root, "comm"))
sys.path.append(os.path.join(home_server_root, "logger"))
sys.path.append(os.path.join(home_server_root, "utils"))
from comm import Comm
from logger import Logger
from mkdirp import mkdirp
from filify import filify
from fuzzy_substring import fuzzy_substring

class VlcThread():
    def __init__(self, logger):
        self.logger = logger
        self.logger.log("VLC: started serving music")
        master, slave = pty.openpty()
        self.p = subprocess.Popen("vlc --intf rc --sout '#transcode{acodec=mpga,ab=128}:rtp{mux=ts,dst=239.255.12.42,sdp=sap,name=\"TestStream\"}'", shell=True, stdout=slave, stdin=subprocess.PIPE, preexec_fn=os.setsid, close_fds=True, bufsize=0)
        self.stdout = os.fdopen(master)
        fcntl.fcntl(self.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

        out = self.get_stdout()

    def get_stdout(self):
        out = []
        while True:
            out_line = self.stdout.readline()
            #output_result = self.p.poll()
            # this never breaks, if vlc/rc fails (i.e. vlc not build with lua)
            if out_line == '> ':
                break
            if out_line != '':
                out.append(out_line)
        return out

    def remote_control(self, cmd):
        print("foo: '%s'" % cmd)
        print("fooascii: '%s'" % ascii(cmd))
        # this fails if cmd contains non-ascii
        self.p.stdin.write(bytes(cmd+"\n", "ascii"))
        self.p.stdin.flush()
        return self.get_stdout()

    def play(self, filename):
        out = self.remote_control('add file://%s' % filename)

    def get_cur_playlist_id(self):
        r = re.compile('^\|\s*\*([0-9]+).*')
        out = self.remote_control('playlist')

        for o in out:
            m = r.match(o)
            if m:
                return int(m.group(1))

    def get_current_file(self):
        out = self.remote_control('status')
        r = re.compile('^\( new input: file://(.*) \)\n$')

        for o in out:
            m = r.match(o)
            if m:
                return m.group(1)

    def stop(self):
        if self.p == None:
            return
        print("stopping serving music...")
        self.p.terminate()
        print(self.p.communicate())
        self.p = None


def load_collection(logger):
    collection_path = os.path.join(home_server_config, "collections")
    music_collection = {}

    directory = os.fsencode(collection_path)
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(b'.json'):
                full_path = os.path.join(root, file)
                logger.log("found collection %s" % file)
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
        podcast_path = os.path.join(home_server_config, "podcast")
        mkdirp(podcast_path)
        filename = os.path.join(podcast_path, "%s_-_episode_%d" % (self.program_name, self.cur_episode))
        if os.path.isfile(filename):
            print("File '%s' already exists" % filename)
        else:
            print("downloading '%s' -> '%s'" % (self.episodes[self.cur_episode], filename))
            p = subprocess.Popen("wget \"%s\" -O %s" % (self.episodes[self.cur_episode], filename), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            print("downloading done!")
            if p.returncode != 0:
                return (404, "Failed to get sound file"), None
        return (200, "Found '%d' episodes. Starting program '%s'" % (len(self.episodes), self.program_name)), filename

class MusicCollection():
    def __init__(self, logger, collection):
        self.logger = logger
        self.music_collection = collection
        self.logger.log("music collection loaded %d tracks" % len(self.music_collection))

    def play(self, params):
        total_score = {}
        for keyword in ["title", "artist"]:
            if keyword in params:
                for kw in params[keyword]:
                    for url, music in self.music_collection.items():
                        collection_kw = music[keyword]
                        if not collection_kw:
                            score = 1000
                        else:
                            score = fuzzy_substring(kw.lower(), collection_kw.lower())
                        if url not in total_score:
                            total_score[url] = 0
                        total_score[url] += score

        print("total_score:", total_score)
        a_min = min(total_score, key=total_score.get)
        best_score = total_score[a_min]
        return [url for url, score in total_score.items() if score == best_score]

class MusicServer():
    def __init__(self):
        self.logger = Logger("music_server")
        self.logger.log("loading music collection...")
        self.music_collection = MusicCollection(self.logger, load_collection(self.logger))
        self.vlc_thread = VlcThread(self.logger)
        self.podcaster = Podcaster()
        self.comm = Comm(5001, "music_server", {"play": self.play, "podcast": self.podcast, "tag": self.tag}, self.logger)

    def enqueue_file(self, filename, params):
        print("now enqueueing! '%s'" % filename)
        self.vlc_thread.play(filename)
        id = self.vlc_thread.get_cur_playlist_id()
        print("id = '%s'" % id)

#http://127.0.0.1:5001/podcast?program=d6m&episode=4
#http://127.0.0.1:5001/podcast?program=d6m
#http://127.0.0.1:5001/podcast?next=1
    def podcast(self, params):
        ret, filename = self.podcaster.podcast(params)
        if filename:
            self.enqueue_file(filename, params)
        return ret

#http://127.0.0.1:5001/tag?star=5
#http://127.0.0.1:5001/tag?instrumetal=1
#http://127.0.0.1:5001/tag?xmas=1
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

#Play song from collection, where title matches the best:
#http://127.0.0.1:5001/play?title=sanitarium
#Play all songs in collection with this artist, fuzzy match:
#http://127.0.0.1:5001/play?artist=metalliac
#Play song from youtube now:
#http://127.0.0.1:5001/play?source=youtube&query=sanitarium&enqueue=now
#Play predefined playlist:
#http://127.0.0.1:5001/play?source=list&query=lanparty
#Play all 5-star rock songs:
#http://127.0.0.1:5001/play?genre=,rock&stars=5
#Play all instrumental iron maiden songs now:
#http://127.0.0.1:5001/play?artist=iron maiden&instrumental=1&enqueue=now
#Play all songs where title contains 'thor', 'thunder' OR 'hammer'
#http://127.0.0.1:5001/play?title=/thor|thunder|hammer&num=0
#Play all songs where title contains 'thor', 'thunder' AND 'hammer'
#http://127.0.0.1:5001/play?title=/thor&title=/thunder&title=/hammer&num=0
#Play next song in playlist
#http://127.0.0.1:5001/play?next=1

#source=[youtube|collection|list] search on youtube, search in local collection or search in predefined playlists. Default 'collection'
#enqueue=[now|next|end|replace] where to put new song(s) on playlist. If 'source' is 'list', default to 'replace'. Else default to 'end'
#query=<string> fuzzy search. Only valid if 'source' is 'list' or 'youtube'

# the remaining values are only valid, if 'source' is 'collection'
#num=N number of matches. If there's one or more fuzzy matchers, '0' means 'all equally best matches'. Else '0' means 'all matches'.
#                         If search criteria include for 'title' or 'url', then default to '1'. Else default to '0'

#artist=<string>
#album=<string>
#title=<string>
#genre=<string>
#url=<string>
#year=<string>
# prefixes in the above search strings mean:
#    , exact match. Use '|' for 'or': 'genre=,metal'. Matches 'metal', but not 'thrash metal'. Same as 'genre=/^metal$'
#    / regex match: 'title=/^[0-9]+\saca[sc]ia\s+avenue'
#    - match numeric range: 'year=-1980-1985' matches songs from 1980 to 1985, both years included. 'stars=-4-5'
#    ! combined with one of the above: no match: 'artist=!,vanilla ice'. Matches if artist isn't 'vanilla ice'
#    : case sensitive: 'album=:,Killers'
#    no prefix means fuzzy match (modified Levenshtein distance). Use '|' for 'or'

# sort: first by artist, then by release_date, then by album, then by track_number, finally by title.
    def play(self, params):
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
        best_url = self.music_collection.play(params)[0]
        if best_url == None:
            return (404, "Music collection seems to be empty")
        self.enqueue_file(best_url, params)
        return (200, "playing: '" + artist + " - " + title + "'")

    def play_youtube(self, params):
        # https://github.com/rg3/youtube-dl
        # python -m youtube_dl -x --audio-format mp3 gsoNl0MzDFA -o '%(artist)s - %(title)s.%(ext)s'
        # python -m youtube_dl ytsearch:"metallica jump in the fire" -o 'foo2'
        #https://github.com/rg3/youtube-dl/commit/6d7359775ae4eef1d1213aae81e092467a2c675c
        if "query" not in params:
            return (404, "if 'source' is 'youtube', 'query' is a required argument to 'play'")
        query = params["query"][0]
        print("play: '%s'" % query)

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '/tmp/yt.%(ext)s',
            'logger': MyLogger(),
            'progress_hooks': [my_hook],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info('ytsearch:%s' % query, ie_key='YoutubeSearch')
            e0 = info["entries"][0]
            artist = None if "artist" not in e0 or e0["artist"] == None else e0["artist"]
            alt_title = None if "alt_title" not in e0 or e0["alt_title"] == None else e0["alt_title"]
            if alt_title:
                title = alt_title
            else:
                title = "unknown" if "title" not in e0 else e0["title"]
        youtube_path = os.path.join(home_server_config, "youtube")
        mkdirp(youtube_path)
        if artist:
            name = "%s_-_%s.mp3" % (filify(artist), filify(title))
        else:
            name = "%s.mp3" % filify(title)
        filename = os.path.join(youtube_path, name)
        os.rename("/tmp/yt.mp3", filename)
        self.enqueue_file(filename, params)
        print("playing %s" % name)

        return (200, "playing name %s" % name)


    def shut_down(self):
        print("music_server shutting down!")
        self.vlc_thread.stop()
        self.comm.shut_down()
        print("music_server shutted down!")

if __name__ == '__main__':
    music_server = MusicServer()
    try:
        while True:
            time.sleep(2.0)
    except KeyboardInterrupt:
        pass
    music_server.shut_down()
