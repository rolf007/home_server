#!/usr/bin/env python3

import argparse
import eyed3
import json
from os import listdir
from os.path import isfile, join
import os
import subprocess
import sys

home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])

def scan_collection(path):
    music_collection = {}
    urls = [os.path.join(path, f) for f in listdir(path) if isfile(join(path, f)) and f.endswith(".mp3")]
    for url in urls:
        audiofile = eyed3.load(url)
        if audiofile.tag:
            print("found : %s - %s (%s)" % ( audiofile.tag.artist, audiofile.tag.title, url))
            music_collection[url] = {"title":audiofile.tag.title, "artist":audiofile.tag.artist}
    return music_collection


parser = argparse.ArgumentParser()
parser.add_argument('path', type=str)
args = parser.parse_args()
path = args.path
if not os.path.isabs(path):
    print("path must be absolute!")
    exit(1)
if not os.path.exists(path):
    print("path does not exist!")
    exit(1)

collection = scan_collection(path)

filename = path[1:].replace('/', '_') + ".collection"
print("filename", filename)
abs_filename = os.path.join(home_server_config, filename)
with open(abs_filename, 'w') as f:
    json.dump(collection, f)
#make the collection file more human readable:
subprocess.check_output("sed -i -e 's/},/},\\n/g' %s" % abs_filename, shell=True)
