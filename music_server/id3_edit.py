#!/usr/bin/env python3

import argparse
import curses
import eyed3
import os
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('mp3s', nargs='+')#, action=MyAction)
args = parser.parse_args()
print(args.mp3s)

screen = curses.initscr()

def just(s, col_num):
    if type(s) is tuple:
        s = s[1]
    if type(s) is str:
        pass
    elif type(s) is eyed3.id3.Genre:
        s = str(s)
    if s is None:
        s = "<None>"
    adj = [20,8,8,8,8,8,8][col_num]
    return s.ljust(adj)[:adj]

y = 4
screen.addstr(y, 2, "%s %s %s %s %s %s %s" % (
        just("url",0),
        just("album",1),
        just("track_num",2),
        just("artist",3),
        just("title",4),
        just("genre",5),
        just("release_date",6)
        ))
y = y + 1
for url in args.mp3s:
#    if not os.path.isabs(scan_path):
#        print("path must be absolute!")
#        exit(1)
    if not os.path.exists(url):
        print("path '%s' does not exist!" % url)
        exit(1)

    audiofile = eyed3.load(url)
    if audiofile and audiofile.tag:
        album = audiofile.tag.album
        track_num = audiofile.tag.track_num
        artist = audiofile.tag.artist
        title = audiofile.tag.title
        genre = audiofile.tag.genre
        release_date = audiofile.tag.release_date
        screen.addstr(y, 2, "%s %s %s %s %s %s %s" % (
                just(url,0),
                just(album,1),
                just(track_num,2),
                just(artist,3),
                just(title,4),
                just(genre,5),
                just(release_date,6)
                ))
    else:
        screen.addstr(y, 2, "%s ???" % url.ljust(12)[:12])
    y = y + 1


    if audiofile and audiofile.tag:
        print("artist = '%s'" % audiofile.tag.artist)
        print("title = '%s'" % audiofile.tag.title)

y = y + 1
screen.addstr(y, 2, "Please select an option...", curses.A_BOLD)
print("wait for it...")
c = screen.getch()
print ('you entered', chr(c))
curses.endwin()

#while True:
#    x = input('> ')
#    if x == 'q':
#        exit(0)


exit(0)

audiofile = eyed3.load(url)
if audiofile and audiofile.tag:
    #print("found : %s - %s (%s)" % ( ascii(audiofile.tag.artist), ascii(audiofile.tag.title), url))
    music_collection[url] = {
        "album":audiofile.tag.album,
        "artist":audiofile.tag.artist,
        "bpm":audiofile.tag.bpm,
        "genre":str(audiofile.tag.genre),
        "release_date":str(audiofile.tag.release_date),
        "title":audiofile.tag.title,
        "track_num":audiofile.tag.track_num
        }


