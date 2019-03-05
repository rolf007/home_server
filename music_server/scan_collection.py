#!/usr/bin/env python3

import argparse
import eyed3
import json
import os
import subprocess
import sys

home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])

sys.path.append(os.path.join(home_server_root, "utils"))

from mkdirp import mkdirp

def scan_collection(scan_path):
    music_collection = {}
    directory = os.fsencode(scan_path)
    total_num_files = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            total_num_files = total_num_files + 1
    file_num = 0
    pct = ""
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_num = file_num + 1
            new_pct = "%d%%" % (file_num*100/total_num_files)
            if new_pct != pct:
                pct = new_pct
                print(pct)
            if file.endswith(b'.mp3'):
                url = os.path.join(root, file).decode('ascii')

                audiofile = eyed3.load(url)
                if audiofile and audiofile.tag:
                    #print("found : %s - %s (%s)" % ( ascii(audiofile.tag.artist), ascii(audiofile.tag.title), url))
                    music_collection[url] = {
                        "album":audiofile.tag.album,
                        "artist":audiofile.tag.artist,
                        "bpm":audiofile.tag.bpm,
                        "genre":str(audiofile.tag.genre),
                        "release":str(audiofile.tag.release_date),
                        "title":audiofile.tag.title,
                        "track_num":audiofile.tag.track_num
                        }
    return music_collection
#'getBestDate',

#!music_server/scan_collection.py /mnt/usb/Albums\ -\ Alfabetisk/M/Metallica/Metallica-And_Justice_For_All-1988-INT-DDZ/
#!music_server/scan_collection.py /mnt/usb/Albums\ -\ Alfabetisk/


parser = argparse.ArgumentParser()
parser.add_argument('path', type=str)
args = parser.parse_args()
scan_path = args.path
if not os.path.isabs(scan_path):
    print("path must be absolute!")
    exit(1)
if not os.path.exists(scan_path):
    print("path does not exist!")
    exit(1)

collection = scan_collection(scan_path)

filename = scan_path[1:].replace('/', '_') + ".json"
print("filename", filename)
collection_path = os.path.join(home_server_config, "collections")
mkdirp(collection_path)
abs_filename = os.path.join(collection_path, filename)
with open(abs_filename, 'w') as f:
    json.dump(collection, f)
#make the collection file more human readable:
subprocess.check_output("sed -i -e 's/},/},\\n/g' \"%s\"" % abs_filename, shell=True)
