#!/usr/bin/env python3

import os
import sys
import youtube_dl_wrapper
import eyed3
import locale

home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])

album = "Amerika"
genre = "pop"
artist = "Bo Kaspers Orkester"
titles = [
        "Vi Kommer Aldrig Att Do",
        "En NY Skon Varld",
        "Ett & Noll",
        "Amerika",
        "Lika Radd Som Du",
        "Kvarter",
        "Ar Det Dar VI Ar Nu",
        "En Varldsomsegling Under Havet",
        "Du Kan",
        "Gott Nytt Ar",
        ]

#https://www.allmusic.com/album/k%C3%A4r-och-galen-mw0000540852
#album = "Kar och Galan"
#genre = "pop"
#artist = "Ulf Lundell"
#titles = [
#        "Kar Och Galen",
#        "Oppna Landskap",
#        "Herrarna",
#        "Aldrig NaNsin Din Clown",
#        "I Kvinnors Ogon",
#        "Laglos",
#        "I Dina Slutna Rum",
#        "Lycklig, Lycklig",
#        "Nar Jag Kysser Haver",
#        "Vid Din Grind Igen",
#        "Hart Regnnna",
#        "Oppna Landskapnna",
#        ]

track = 1
for title in titles:
    query = "%s %s" % (artist, title)
    name, filename = youtube_dl_wrapper.youtube_dl_wrapper(query, track, artist, album)
    print("'%s' -> '%s'" % (ascii(query), ascii(filename)))

    audiofile = eyed3.load(filename)
    audiofile.tag.album = album
    audiofile.tag.title = title
    audiofile.tag.genre = genre
    audiofile.tag.artist = artist
    audiofile.tag.track_num = (track, len(titles))
    audiofile.tag.release_date = "1996"
    audiofile.tag.save()
    track += 1
