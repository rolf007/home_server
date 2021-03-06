#!/usr/bin/env python3

import os
import json
import sys
import requests

home_server_root = os.path.split(sys.path[0])[0]
sys.path.append(os.path.join(home_server_root, "comm"))
sys.path.append(os.path.join(home_server_root, "utils"))
from comm import Comm
from micro_service import MicroServiceHandler

class Wiki():
    def __init__(self, logger, exc_cb):
        self.logger = logger
        self.comm = Comm(5006, "wiki", {"wiki": self.wiki}, self.logger, exc_cb)

    def wiki(self, params):
        query = params["query"][0]
        resp0 = requests.get("https://en.wikipedia.org/w/api.php?action=opensearch&limit=1&namespace=0&format=json&search=%s" % query)
        json0 = json.loads(resp0.text)
        if len(json0) < 2:
            return (404, "no search")
        if len(json0[1]) < 1:
            return (404, "no result")
        title = json0[1][0]
        resp1 = requests.get("https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&exintro&explaintext&redirects=1&titles=%s" % title)
        json1 = json.loads(resp1.text)
        try:
            extract = next(iter(json1['query']['pages'].values()))['extract']
        except KeyError:
            return (404, "wiki Error")
        return (200, extract)

    def shut_down(self):
        print("wiki shutting down!")
        self.comm.shut_down()
        print("wiki shutted down!")


if __name__ == '__main__':
    MicroServiceHandler("wiki", Wiki)
