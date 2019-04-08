import os
import sys
import youtube_dl
home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])
sys.path.append(os.path.join(home_server_root, "utils"))
from filify import filify
from mkdirp import mkdirp

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

def youtube_dl_wrapper(query, track = None, default_artist = None, default_album = None):
    # https://github.com/rg3/youtube-dl
    # python -m youtube_dl -x --audio-format mp3 gsoNl0MzDFA -o '%(artist)s - %(title)s.%(ext)s'
    # python -m youtube_dl ytsearch:"metallica jump in the fire" -o 'foo2'
    #https://github.com/rg3/youtube-dl/commit/6d7359775ae4eef1d1213aae81e092467a2c675c

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
        artist = default_artist if "artist" not in e0 or e0["artist"] == None else e0["artist"]
        album = default_album if "album" not in e0 or e0["album"] == None else e0["album"]
        alt_title = None if "alt_title" not in e0 or e0["alt_title"] == None else e0["alt_title"]
        if alt_title:
            title = alt_title
        else:
            title = "unknown" if "title" not in e0 else e0["title"]
    youtube_path = os.path.join(home_server_config, "youtube")
    if artist:
        youtube_path = os.path.join(youtube_path, filify(artist))
    if album:
        youtube_path = os.path.join(youtube_path, filify(album))
    mkdirp(youtube_path)
    if artist:
        name = "%s - %s.mp3" % (filify(artist), filify(title))
    else:
        name = "%s.mp3" % filify(title)
    if track:
        name = "%02d %s" % (track, name)
    filename = os.path.join(youtube_path, name)
    os.rename("/tmp/yt.mp3", filename)
    return name, filename
