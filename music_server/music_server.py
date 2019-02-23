#!/usr/bin/env python3

#https://wiki.videolan.org/Documentation:Streaming_HowTo/Advanced_Streaming_Using_the_Command_Line/#Examples
#/etc/portage/package.use/vlc:
#media-video/vlc lua
#pip install --user eyed3
#pip install --user youtube_dl
#pip install --user -U youtube-dl


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
import random
import re
import youtube_dl_wrapper


home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])
sys.path.append(os.path.join(home_server_root, "comm"))
sys.path.append(os.path.join(home_server_root, "logger"))
sys.path.append(os.path.join(home_server_root, "utils"))
from comm import Comm
from logger import Logger
from mkdirp import mkdirp
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
        print("fooascii: '%s'" % ascii(cmd))
        # this fails if cmd contains non-ascii
        self.p.stdin.write(bytes(cmd+"\n", "ascii"))
        self.p.stdin.flush()
        return self.get_stdout()

    def play(self, filenames, enqueue):
        if filenames == []:
            return
        status = self.get_status()
        if enqueue == 'q': # enqueue at end of playlist
            if status == "stopped":
                out = self.remote_control('add file://%s' % filenames[0])
                filenames = filenames[1:]
            for filename in filenames:
                out = self.remote_control('enqueue file://%s' % filename)
        elif enqueue == 'c': # clear playlist. Then play this
            out = self.remote_control('clear')
            out = self.remote_control('add file://%s' % filenames[0])
            filenames = filenames[1:]
            for filename in filenames:
                out = self.remote_control('enqueue file://%s' % filename)
        elif enqueue == 'n': # play NOW
            cur_id = self.get_cur_playlist_id()
            if cur_id == None:
                self.play(filenames, 'q')
            else:
                out = self.remote_control('add file://%s' % filenames[0])
                last_id = self.get_last_playlist_id()
                out = self.remote_control('move %d %d' % (last_id, cur_id))

                for filename in filenames:
                    id = last_id
                    out = self.remote_control('enqueue file://%s' % filename)
                    last_id = self.get_last_playlist_id()
                    out = self.remote_control('move %d %d' % (last_id, id))

        elif enqueue == 'x': # play next
            if status == "stopped":
                self.play(filenames, 'n')
            else:
                last_id = self.get_cur_playlist_id()
                for filename in filenames:
                    id = last_id
                    out = self.remote_control('enqueue file://%s' % filename)
                    last_id = self.get_last_playlist_id()
                    out = self.remote_control('move %d %d' % (last_id, id))

    def stop(self):
        out = self.remote_control('stop')

    def get_cur_playlist_id(self):
        r = re.compile('^\|  \*([0-9]+).*')
        out = self.remote_control('playlist')

        for o in out:
            m = r.match(o)
            if m:
                return int(m.group(1))
        return None

    def get_last_playlist_id(self):
        r = re.compile('^\|  .([0-9]+).*')
        out = self.remote_control('playlist')

        id = None
        for o in out:
            m = r.match(o)
            if m:
                id = int(m.group(1))
        return id

    def get_status(self):
        r = re.compile('^\( (.*) \)$')
        out = self.remote_control('status')

        for o in out:
            m = r.match(o)
            if m:
                return m.group(1)

    def get_current_file(self):
        out = self.remote_control('status')
        r = re.compile('^\( new input: file://(.*) \)\n$')

        for o in out:
            m = r.match(o)
            if m:
                return m.group(1)

    def shut_down(self):
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

        if "program" not in params:
            return (404, "for 'podcast', 'program' is a required argument"), None
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
                filename = self.download_podcast()
                if filename:
                    return (200, "Found '%d' episodes. Starting program '%s', episode %d" % (len(self.episodes), self.program_name, self.cur_episode)), filename
                return (404, "Failed to get sound file"), None
            else:
                return (404, "No episodes found"), None
        else:
            return (404, "Unknown podcast program '%s'" % program), None

    def skip_to(self, to):
        if self.episodes == None:
            return (404, "no current podcast program"), None
        self.cur_episode = to
        self.cur_episode = min(self.cur_episode, len(self.episodes)-1)
        self.cur_episode = max(self.cur_episode, 0)
        filename = self.download_podcast()
        if filename:
            return (200, "Skipping to program '%s', episode %d" % (self.program_name, self.cur_episode)), filename
        return (404, "Failed to get sound file"), None

    def download_podcast(self):
        podcast_path = os.path.join(home_server_config, "podcast")
        mkdirp(podcast_path)
        filename = os.path.join(podcast_path, "%s_-_episode_%d" % (self.program_name, self.cur_episode))
        if os.path.isfile(filename):
            print("File already exists: '%s'" % filename)
        else:
            print("downloading '%s' -> '%s'" % (self.episodes[self.cur_episode], filename))
            p = subprocess.Popen("wget \"%s\" -O %s" % (self.episodes[self.cur_episode], filename), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            print("downloading done!")
            if p.returncode != 0:
                return None
        return filename

class MusicCollection():
    def __init__(self, logger, collection):
        self.logger = logger
        self.music_collection = collection
        self.logger.log("music collection loaded %d tracks" % len(self.music_collection))

    def parse_flags(self, query):
        flags = {"case_sensitive": False, "negate": False, "match_type": "fuzzy"}
        if query[0] == ':':
            flags["case_sensitive"] = True
            query = query[1:]
        if query[0] == '!':
            flags["negate"] = True
            query = query[1:]
        if query[0] == ',':
            flags["match_type"] = "exact"
            query = query[1:]
        elif query[0] == '/':
            flags["match_type"] = "regex"
            query = query[1:]
        elif query[0] == '-':
            flags["match_type"] = "range"
            query = query[1:]
        return query, flags


    def play(self, params):
        total_score = {}
        for url, music in self.music_collection.items():
            valid = True
            score = 0
            for keyword in ["title", "artist"]:
                if keyword in params:
                    collection_kw = music[keyword]
                    for query_kw in params[keyword]:
                        if not collection_kw:
                            valid = False
                            break
                        query, flags = self.parse_flags(query_kw)
                        if flags["match_type"] == "exact":
                            print(query.lower() , collection_kw.lower())
                            if query.lower() != collection_kw.lower():
                                valid = False
                        else:
                            score += fuzzy_substring(query_kw.lower(), collection_kw.lower())
                if not valid:
                    break
            if valid:
                total_score[url] = score

        if len(total_score) == 0:
            return []
        a_min = min(total_score, key=total_score.get)
        best_score = total_score[a_min]
        play = [url for url, score in total_score.items() if score == best_score]
        for val in play:
            print("%s " % val)
        return play

    def getPrettyName(self, url):
        if url in self.music_collection:
            track = self.music_collection[url]
            artist = track["artist"] if "artist" in track else None
            title = track["title"] if "title" in track else None
            if title == None and artist == None:
                return "unknown"
            elif title == None:
                return artist
            elif artist == None:
                return title
            else:
                return "%s - %s" % (artist, title)
        else:
            return "unknown2"

class MusicServer():
    def __init__(self):
        self.logger = Logger("music_server")
        self.logger.log("loading music collection...")
        self.music_collection = MusicCollection(self.logger, load_collection(self.logger))
        self.vlc_thread = VlcThread(self.logger)
        self.podcaster = Podcaster()
        self.comm = Comm(5001, "music_server", {"play": self.play, "podcast": self.podcast, "skip": self.skip, "stop": self.stop, "tag": self.tag}, self.logger)
        self.mode = "stopped"

#http://127.0.0.1:5001/skip?next=3
#http://127.0.0.1:5001/skip?prev=1
#http://127.0.0.1:5001/skip?to=random
#http://127.0.0.1:5001/skip?to=0
#http://127.0.0.1:5001/skip?to=last
    def skip(self, params):
        if "next" not in params and "prev" not in params and "to" not in params:
            return (404, "'skip' requires either 'next' or 'prev'.")
        to = None
        if "next" in params:
            delta = int(params["next"][0])
        elif "prev" in params:
            delta = -int(params["prev"][0])
        elif "to" in params:
            to = params["to"][0]
        if self.mode == "podcast":
            if to is not None:
                if to == "random":
                    to = random.randint(0, len(self.podcaster.episodes)-1)
                elif to == "last":
                    to = len(self.podcaster.episodes)-1
                else:
                    to = int(to)
                ret, filename = self.podcaster.skip_to(to)
            else:
                cur = self.podcaster.cur_episode
                if cur is None:
                    return (404, "can't 'skip'. No current podcast playing.")
                ret, filename = self.podcaster.skip_to(cur + delta)
            if filename:
                self.vlc_thread.play([filename], 'c')
            return ret
        elif self.mode == "music":
            return (200, "skipped music")
        else:
            return (404, "Can't skip. Nothing is playing.")

    def stop(self, params):
        self.mode = "stopped"
        self.vlc_thread.stop()
        return (200, "stopped")

#http://127.0.0.1:5001/podcast?program=d6m&episode=4
#http://127.0.0.1:5001/podcast?program=d6m
    def podcast(self, params):
        ret, filename = self.podcaster.podcast(params)
        if filename:
            self.vlc_thread.play([filename], 'c')
            self.mode = "podcast"
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
        filenames = self.music_collection.play(params)
        self.vlc_thread.play(filenames, 'c')
        self.mode = "music"
        if len(filenames) == 1:
            return (200, "playing: '%s'" % self.music_collection.getPrettyName(filenames[0]))
        return (200, "playing: '%s' songs" % len(filenames))


    def play_youtube(self, params):
        if "query" not in params:
            return (404, "if 'source' is 'youtube', 'query' is a required argument to 'play'")
        query = params["query"][0]
        print("youtube query: '%s'" % query)
        name, filename = youtube_dl_wrapper.youtube_dl_wrapper(query)
        self.vlc_thread.play([filename], 'c')
        self.mode = "music"
        print("youtube playing: '%s'" % name)

        return (200, "playing name '%s'" % name)


    def shut_down(self):
        print("music_server shutting down!")
        self.vlc_thread.shut_down()
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
