#!/usr/bin/env python3

#https://wiki.videolan.org/Documentation:Streaming_HowTo/Advanced_Streaming_Using_the_Command_Line/#Examples
#/etc/portage/package.use/vlc:
#media-video/vlc lua
#pip install --user youtube_dl
#pip install --user -U youtube-dl

import subprocess
import os
import sys
import fcntl
import json
from os.path import isfile, join
import pty
import random
import re
import uuid
import youtube_dl_wrapper
import time

home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])
sys.path.append(os.path.join(home_server_root, "comm"))
sys.path.append(os.path.join(home_server_root, "utils"))
from comm import Comm
from mkdirp import mkdirp
from fuzzy_substring import Levenshtein
from micro_service import MicroServiceHandler
from timer import Loop

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
        self.logger.log("remote_control: '%s'" % ascii(cmd))
        # this fails if cmd contains non-ascii
        self.p.stdin.write(bytes(cmd+"\n", "ascii"))
        self.p.stdin.flush()
        return self.get_stdout()

    def enqueue(self, filenames, enqueue_mode):
        if filenames == []:
            return
        status = self.get_status()
        if enqueue_mode == 'q': # enqueue at end of playlist
            if status == "stopped":
                out = self.remote_control('add file://%s' % filenames[0])
                filenames = filenames[1:]
            for filename in filenames:
                out = self.remote_control('enqueue file://%s' % filename)
        elif enqueue_mode == 'c': # clear playlist. Then play this
            out = self.remote_control('clear')
            out = self.remote_control('add file://%s' % filenames[0])
            filenames = filenames[1:]
            for filename in filenames:
                out = self.remote_control('enqueue file://%s' % filename)
        elif enqueue_mode == 'n': # play NOW
            cur_id = self.get_cur_playlist_id()
            if cur_id == None:
                self.enqueue(filenames, 'q')
            else:
                out = self.remote_control('add file://%s' % filenames[0])
                last_id = self.get_last_playlist_id()
                out = self.remote_control('move %d %d' % (last_id, cur_id))

                for filename in filenames:
                    id = last_id
                    out = self.remote_control('enqueue file://%s' % filename)
                    last_id = self.get_last_playlist_id()
                    out = self.remote_control('move %d %d' % (last_id, id))
        elif enqueue_mode == 'x': # play next
            if status == "stopped":
                self.enqueue(filenames, 'n')
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

    def get_filename(self, id):
        out = self.remote_control('info %d' % id)
        r = re.compile('^\| filename: (.*)')
        for o in out:
            m = r.match(o)
            if m:
                return m.group(1)
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

    def get_playlist(self):
        id_list = []
        out = self.remote_control('playlist')
        r = re.compile('^\|  (\*| )([0-9]+).*')
        for o in out:
            m = r.match(o)
            if m:
                id_list.append(int(m.group(2)))
        return id_list

    def debug_playlist(self):
        status_out = self.remote_control('status')
        playlist_out = self.remote_control('playlist')
        out = "status:\n"
        for line in status_out:
            if line != '\n':
                out += line
        out += "\nplaylist:\n"
        for line in playlist_out:
            if line != '\n':
                out += line
        return out

    def get_status(self):
        r = re.compile('^\( state (.*) \)$')
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
        self.logger.log("stopping serving music...")
        self.p.stdin.write(bytes("shutdown\n", "ascii"))
        self.p.stdin.flush()
        print(self.p.communicate())
        self.p = None
        self.stdout.close()


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

def load_playlists(logger):
    playlist_path = os.path.join(home_server_config, "playlists")
    playlists = {}

    directory = os.fsencode(playlist_path)
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(b'.json'):
                full_path = os.path.join(root, file)
                logger.log("found playlist file %s" % file)
                with open(full_path) as f:
                    playlists = {**playlists, **json.load(f)}
    return playlists


class Podcaster():
    def __init__(self):
        self.episodes = None
        self.cur_episode = None
        self.program_name = None
        self.programs = {}

    def add_podcast(self, nick, name, url, regex):
        if nick is None:
            nick = name
        self.programs[nick] = { "name": name, "url": url, "regex": regex }

    def add_24syv_podcast(self, name, id, nick=None):
#https://www.24syv.dk/programmer
        regex_24syv = "<enclosure url=\"(https://arkiv.radio24syv.dk/.*/.*/.*/audio/podcast/.*-audio.(?:mp3|m4a))\""
        self.add_podcast(nick, name, "https://arkiv.radio24syv.dk/audiopodcast/channel/" + str(id), regex_24syv)

    def add_dr_podcast(self, name, nick=None):
#https://www.dr.dk/allepodcast/?letter=
        regex_dr = "<enclosure url=\"(https://www.dr.dk/mu/MediaRedirector/WithFileExtension/.*.mp3\\?highestBitrate=True&amp;podcastDownload=True)\""
        self.add_podcast(nick, name, "https://www.dr.dk/mu/feed/"+name+".xml?format=podcast", regex_dr)

    def podcast(self, params):
        self.add_podcast("lir", "Forhjulslir", "https://forhjulslir.libsyn.com/rss", "<enclosure length=\"[0-9]+\" type=\"audio/mpeg\" url=\"(https://traffic.libsyn.com/secure/forhjulslir/.*.mp3\\?dest-id=[0-9]+)\" />")

        self.add_dr_podcast("orientering")
        self.add_dr_podcast("mads-monopolet-podcast", "mads")
        self.add_dr_podcast("bagklog-pa-p1")
        self.add_dr_podcast("4-division")
        self.add_dr_podcast("sidste-mand-slukker-lyset")
        self.add_dr_podcast("audiens")
        self.add_dr_podcast("foelg-pengene")
        self.add_dr_podcast("klimatestamentet")
        self.add_dr_podcast("ugens-gaest-p1")
        self.add_dr_podcast("bagklog-pa-p1")
        self.add_dr_podcast("klog-pa-sprog")
        self.add_dr_podcast("slotsholmen")
        self.add_dr_podcast("gudstjeneste-radio")
        self.add_dr_podcast("mands-minde-foredrag")
        self.add_dr_podcast("4-division")
        self.add_dr_podcast("de-hoejere-magter")
        self.add_dr_podcast("verdenspressen")
        self.add_dr_podcast("shitstorm")
        self.add_dr_podcast("public-service")
        self.add_dr_podcast("digitalt")
        self.add_dr_podcast("supertanker")
        self.add_dr_podcast("kulturen-pa-p1")
        self.add_dr_podcast("radiofortaellinger")
        self.add_dr_podcast("p1-debat")
        self.add_dr_podcast("tidsaand")
        self.add_dr_podcast("p1-dokumentar")
        self.add_dr_podcast("hjernekassen-pa-p1")
        self.add_dr_podcast("mennesker-og-medier")
        self.add_dr_podcast("verden-ifoelge-gram")
        self.add_dr_podcast("filmland")
        self.add_dr_podcast("p1-morgen")
        self.add_dr_podcast("skoenlitteratur-pa-p1")
        self.add_dr_podcast("orientering")
        self.add_dr_podcast("baglandet")
        self.add_24syv_podcast("Den_Sjete_Masseuddoen", 27580524, "d6m")
        self.add_24syv_podcast("Baeltestedet", 8741566, "baelte")
        self.add_24syv_podcast("genialos", 4184863)
        self.add_24syv_podcast("abernes-planet", 27984455)
        self.add_24syv_podcast("den-sjette-masseuddoeen", 27580524)
        self.add_24syv_podcast("genialos", 4184863)
        self.add_24syv_podcast("tibet-papirerne", 27748091)
        self.add_24syv_podcast("hitlers-aeseloerer", 11777576)
        self.add_24syv_podcast("spoerge-joergen", 12592536)
        self.add_24syv_podcast("24-spoergsmaal-til-professoren", 13973671)
        self.add_24syv_podcast("24syv-dokumentar", 3887302)
        self.add_24syv_podcast("24syv-morgen", 3843763)
        self.add_24syv_podcast("24syv-nyheder", 3561248)
        self.add_24syv_podcast("55-minutter", 16512232)
        self.add_24syv_podcast("aflyttet", 4466232)
        self.add_24syv_podcast("ak-24syv", 3843145)
        self.add_24syv_podcast("baeltestedet", 8741566)
        self.add_24syv_podcast("croque-monsieur", 11929746)
        self.add_24syv_podcast("datolinjen", 4945795)
        self.add_24syv_podcast("den-korte-radioavis", 10839671)
        self.add_24syv_podcast("det-naeste-kapitel", 12132345)
        self.add_24syv_podcast("det-roede-felt", 8373634)
        self.add_24syv_podcast("det-vi-taler-om", 10327258)
        self.add_24syv_podcast("efter-otte", 8633895)
        self.add_24syv_podcast("elektronista", 3843152)
        self.add_24syv_podcast("er-du-sunshine", 13967997)
        self.add_24syv_podcast("europa-i-flammer", 4643454)
        self.add_24syv_podcast("fedeabes-fyraften", 16512250)
        self.add_24syv_podcast("finnsk-terapi", 10685650)
        self.add_24syv_podcast("fitness-mk", 11777621)
        self.add_24syv_podcast("flaskens-aand", 3843405)
        self.add_24syv_podcast("fodbold-fm", 3843776)
        self.add_24syv_podcast("foraeldreintra", 13973585)
        self.add_24syv_podcast("ghetto-fitness", 26967854)
        self.add_24syv_podcast("globus", 3778761)
        self.add_24syv_podcast("huxi-og-det-gode-gamle-folketing", 6555368)
        self.add_24syv_podcast("jeppesens-bibelskole", 12391837)
        self.add_24syv_podcast("kampagnesporet", 13965705)
        self.add_24syv_podcast("kina-snak", 7560743)
        self.add_24syv_podcast("mikrofonholder", 3843770)
        self.add_24syv_podcast("millionaerklubben", 3784851)
        self.add_24syv_podcast("nattevagten", 3843151)
        self.add_24syv_podcast("pharaos-cigarer", 9760337)
        self.add_24syv_podcast("politiradio", 12144388)
        self.add_24syv_podcast("qa", 13976201)
        self.add_24syv_podcast("raabaand", 3843225)
        self.add_24syv_podcast("rene-linjer", 14632714)
        self.add_24syv_podcast("romerriget", 3973425)
        self.add_24syv_podcast("rushys-roulette", 6563547)
        self.add_24syv_podcast("soendagspolitikken", 8629629)
        self.add_24syv_podcast("winthertid", 17937754)

        if "program" not in params:
            return (404, "for 'podcast', 'program' is a required argument"), None
        program = params["program"][0]
        if program in self.programs:
            program_info = self.programs[program]
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
        self.searches = {}

    def start_search(self, resolve_cb, params, session_id, asynch=True):
        if session_id in self.searches:
            self.searches[session_id].cancel()
        self.searches[session_id] = Search(self.music_collection.items(), resolve_cb, params, session_id)
        self.searches[session_id].start(asynch)

    def get_search_status(self, session_id):
        if session_id not in self.searches:
            return "not_available"
        if self.searches[session_id].status == "done":
            return "available"
        if self.searches[session_id].status == "in_progress":
            return "in_progress"
        return "not_available"

    def get_search_result(self, session_id):
        if session_id not in self.searches:
            return None
        ret = self.searches[session_id].search_results
        del self.searches[session_id]
        return ret

    def get_all_info(self, urls):
        return {url:self.music_collection[url] for url in urls}

class Search(Loop):
    def __init__(self, ittr, resolve_cb, params, session_id):
        super(Search, self).__init__(ittr)
        self.resolve_cb = resolve_cb
        self.params = params
        self.session_id = session_id
        self.levenshtein = Levenshtein(1, 10, 10)
        self.total_score = {}
        self.status = "in_progress"
        self.search_results = []
        self.count = 0
        self.count2 = 0
        self.start_time = time.time()
        self.best_score = 1000000000

    def cancel(self):
        self.status = "cancelled"
        self.stop()

    def parse_flags(self, query):
        flags = {"case_sensitive": False, "negate": False, "match_type": "fuzzy"}
        if len(query) == 0:
            return query, flags
        if query[0] == '!':
            flags["negate"] = True
            query = query[1:]
            if len(query) == 0:
                return query, flags
        if query[0] == ':':
            flags["case_sensitive"] = True
            query = query[1:]
            if len(query) == 0:
                return query, flags
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

    def negate(self, expr, flags):
        if flags["negate"]:
            return not expr
        return expr

    def case(self, s, flags):
        if flags["case_sensitive"]:
            return s
        return s.lower()

    def safe_to_int(self, s):
        try:
            return int(s)
        except:
            return None

    def body(self, i):
        self.count += 1
        old = self.count2
        self.count2 = int(self.count/1730)
        if old != self.count2:
            print("count: %d %s" % (self.count2, self.params))
        valid = True
        score = 0
        url, music = i
        params = self.params
        for keyword in ["title", "artist", "album", "genre", "release"]:
            if keyword in params and keyword in music:
                collection_kw = music[keyword]
                for query_kw in params[keyword]:
                    if not collection_kw:
                        valid = False
                        break
                    query, flags = self.parse_flags(query_kw)
                    if flags["match_type"] == "exact":
                        if self.negate(self.case(query, flags) != self.case(collection_kw, flags), flags):
                            valid = False
                    elif flags["match_type"] == "range":
                        splt = query.split('-')
                        if len(splt) != 2:
                            continue
                        range_min = self.safe_to_int(splt[0])
                        range_max = self.safe_to_int(splt[1])
                        value = self.safe_to_int(collection_kw)
                        if value is None:
                            continue
                        if self.negate(range_max is not None and value > range_max or range_min is not None and value < range_min, flags):
                            valid = False
                    elif flags["match_type"] == "regex":
                        try:
                            m = re.search(self.case(query, flags), self.case(collection_kw, flags))
                            if self.negate(not m, flags):
                                valid = False
                        except re.error:
                            valid = False
                    else:
                        leven = self.levenshtein.distance(self.case(query, flags), self.case(collection_kw, flags),self.best_score-score)
                        if leven is not None:
                            score += leven
                        else:
                            valid = False
            if not valid:
                break
        if valid:
            if score <= self.best_score:
                self.best_score = score
                print(url)
            self.total_score[url] = score

    def done(self):
        self.end_time = time.time()
        print("duration: %s" % (self.end_time - self.start_time))
        if len(self.total_score) == 0:
            return []
        a_min = min(self.total_score, key=self.total_score.get)
        best_score = self.total_score[a_min]
        #for e, s in self.total_score.items():
        #    print(e, s)
        urls = [url for url, score in self.total_score.items() if score == best_score]
        limit = 20
        if len(urls) > limit:
            urls = urls[:limit]
        self.search_results = urls
        self.resolve_cb(self.session_id)
        self.status = "done"


class MusicServer():
    def __init__(self, logger, exc_cb):
        self.logger = logger
        self.logger.log("loading music collection...")
        self.music_collection = MusicCollection(self.logger, load_collection(self.logger))
        self.playlists = load_playlists(self.logger)
        self.vlc_thread = VlcThread(self.logger)
        self.podcaster = Podcaster()
        self.comm = Comm(5001, "music_server", {"play": self.play, "search": self.search, "get_search_result": self.get_search_result, "debug_playlist": self.debug_playlist, "podcast": self.podcast, "skip": self.skip, "stop": self.stop, "tag": self.tag}, self.logger, exc_cb)
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
                self.vlc_thread.enqueue([filename], 'c')
            return ret
        elif self.mode == "music":
            return (200, "skipping music not implemented yet")
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
            self.vlc_thread.enqueue([filename], 'c')
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

# sort: first by artist, then by release, then by album, then by track_number, finally by title.

    def search_resolve_cb(self, session_id):
        pass

    def search(self, params):
        #self.logger.log("search begin: %s " % params)
        if ("source" in params):
            source = params["source"][0]
        else:
            source = "collection"
        if ("session_id" not in params):
            return (404, "'session_id' is required for 'search'" % source)
        session_id = params["session_id"][0]
        if source == "collection":
            self.music_collection.start_search(self.search_resolve_cb, params, session_id)
            return (200, "%s" % "search started ok!")
        return (404, "Source must be 'collection', 'youtube' or 'list' (%s)" % source)

    def debug_playlist(self, params):
        ret = self.vlc_thread.debug_playlist()
        return (200, ret)

    def get_search_result(self, params):
        #self.logger.log("get_search_result: %s " % params)
        if ("session_id" not in params):
            return (404, "'session_id' is required for 'get_search_result'" % source)
        session_id = params["session_id"][0]
        status = self.music_collection.get_search_status(session_id)
        if status == "available":
            j = json.dumps({"status": status, "result": self.music_collection.get_all_info(self.music_collection.get_search_result(session_id))})
        else:
            j = json.dumps({"status": status})
        return (200, j)

    def play(self, params):
        if ("source" in params):
            source = params["source"][0]
        else:
            source = "collection"
        if source == "collection":
            return self.play_collection(params)
        elif source == "youtube":
            return self.play_youtube(params)
        elif source == "list":
            return self.play_list(params)
        return (404, "Source must be 'collection', 'youtube' or 'list' (%s)" % source)

    def play_collection_resolve_cb(self, session_id):
        self.logger.log("play_collection_resolve_cb: %s " % session_id)
        urls = self.music_collection.get_search_result(session_id)
        if len(urls) == 0:
            return
        self.vlc_thread.enqueue(urls, 'c')
        self.mode = "music"

    def play_collection(self, params):
        self.logger.log("play_collection: %s " % params)
        session_id = str(uuid.uuid4())
        self.music_collection.start_search(self.play_collection_resolve_cb, params, session_id)
        return (200, "succesfully requested music from collection")


    def play_youtube(self, params):
        if "query" not in params:
            return (404, "if 'source' is 'youtube', 'query' is a required argument to 'play'")
        query = params["query"][0]
        print("youtube query: '%s'" % query)
        name, filename = youtube_dl_wrapper.youtube_dl_wrapper(query)
        self.vlc_thread.enqueue([filename], 'c')
        self.mode = "music"
        print("youtube playing: '%s'" % name)
        return (200, "playing name '%s'" % name)

    def play_list_searches_all_done(self):
        if len(self.play_list_search_results) == 0:
            return
        if self.play_list_sort == "shuffle":
            random.shuffle(self.play_list_search_results)
        self.vlc_thread.enqueue(self.play_list_search_results, 'c')
        self.mode = "music"

    def play_list_resolve_cb(self, session_id):
        self.logger.log("play_list_resolve_cb: %s " % session_id)
        urls = self.music_collection.get_search_result(session_id)
        self.play_list_search_results += urls
        self.play_list_searches.remove(session_id)
        if len(self.play_list_searches) == 0:
            self.play_list_searches_all_done()

    def play_list(self, params):
        self.logger.log("play_list '%s'" % params)
        if "query" not in params:
            return (404, "if 'source' is 'list', 'query' is a required argument to 'play'")
        query = params["query"][0]
        if query not in self.playlists:
            return (404, "unknown playlist '%s'" % query)
        playlist = self.playlists[query]
        qs = playlist["queries"]
        sort = None if "sort" not in playlist else playlist["sort"]
        self.play_list_searches = set()
        self.play_list_search_results = []
        self.play_list_sort = sort
        for q in qs:
            session_id = str(uuid.uuid4())
            self.play_list_searches.add(session_id)
            self.music_collection.start_search(self.play_list_resolve_cb, q, session_id)
        return (200, "succesfully requsted to play a predefined playlist")


    def shut_down(self):
        print("music_server shutting down!")
        self.vlc_thread.shut_down()
        self.comm.shut_down()
        print("music_server shutted down!")

if __name__ == '__main__':
    MicroServiceHandler("music_server", MusicServer)
