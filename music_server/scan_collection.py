#!/usr/bin/env python3

import argparse
import errno
import eyed3
import json
from os import listdir
from os.path import isfile, join
import os
import subprocess
import sys

home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])

def scan_collection(scan_path):
    music_collection = {}
    directory = os.fsencode(scan_path)
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(b'.mp3'):
                url = os.path.join(root, file).decode('ascii')

                audiofile = eyed3.load(url)
                if audiofile.tag:
                    print("found : %s - %s (%s)" % ( audiofile.tag.artist, audiofile.tag.title, url))
                    music_collection[url] = {"title":audiofile.tag.title, "artist":audiofile.tag.artist}
    return music_collection


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
try:
    os.makedirs(collection_path)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise
abs_filename = os.path.join(collection_path, filename)
with open(abs_filename, 'w') as f:
    json.dump(collection, f)
#make the collection file more human readable:
subprocess.check_output("sed -i -e 's/},/},\\n/g' %s" % abs_filename, shell=True)
