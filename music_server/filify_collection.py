#!/usr/bin/env python3

import argparse
from filify import filify
import os

def filify_collection(scan_path):
    music_collection = {}
    directory = os.fsencode(scan_path)
    for root, dirs, files in os.walk(directory):
        for dir in dirs:
            f = bytes(filify(dir), 'ascii')
            if f != dir:
                print("rename dir  %s / %s ->\n            %s / %s" % (root, ascii(dir), root, f))
                os.rename(os.path.join(root, dir), os.path.join(root, f))
        for file in files:
            f = bytes(filify(file), 'ascii')
            if f != file:
                print("rename file %s / %s ->\n            %s / %s" % (root, ascii(file), root, f))
                os.rename(os.path.join(root, file), os.path.join(root, f))



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

