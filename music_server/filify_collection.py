#!/usr/bin/env python3

import argparse
from os.path import join
import os

def filify_collection(scan_path):
    music_collection = {}
    directory = os.fsencode(scan_path)
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(b'.mp3'):
                print(os.path.join(root, file))
                url = os.path.join(root, file).decode('ascii')
                print(url)
                print()



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

filify_collection(scan_path)

