#!/usr/bin/env python3

import asyncio
import os
import sys
import threading
from aiohttp import web
home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])
sys.path.append(os.path.join(home_server_root, "comm"))
sys.path.append(os.path.join(home_server_root, "utils"))
from comm import Comm
from micro_service import MicroServiceHandler

minimal_head = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="apple-touch-icon" href='/assets/apple-touch-icon.png'/>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
"""

def tag(tg, inner):
    return "<"+tg+">\n"+inner+"</"+tg+">"
def button(func, args, text):
    return "<button onclick=\""+func+"("+args+")\">"+text+"</button><br>\n"
def link(lnk, text):
    return "<form action=\""+lnk+"\"><input type=\"submit\" value=\""+text+"\" /></form>\n"


class WebApp:
    def __init__(self, logger, exc_cb):
        self.logger = logger
        self.comm = Comm(5009, "web_app", {}, self.logger, exc_cb)

        self.loop = asyncio.get_event_loop()

        app = web.Application()
        app.add_routes([web.get('/', self.main_menu),
                        web.get('/stop', self.stop),
                        web.get('/search', self.search),
                        web.get('/play', self.play),
                        web.get('/radio', self.radio),
                        web.get('/music', self.music_menu),
                        web.get('/assets/apple-touch-icon.png', self.png)])

        handler = app.make_handler()
        self.server = self.loop.create_server(handler, port=8080)
        self.loop.run_until_complete(self.server)

    async def png(self, request):
        headers = {'content-type': 'image/png'}
        return web.FileResponse('./web_app/assets/apple-touch-icon.png')

    async def main_menu(self, request):
        content = ""
        content += link("/music", "Music")
        content += button("radio", "'p1'", "P1")
        content += button("radio", "'p2'", "P2")
        content += button("radio", "'p3'", "P3")
        content += button("radio", "'24syv'", "24Syv")
        content += button("stop", "", "Stop")

        scripts = """
function radio(channel_name) {
  $.get("/radio", {channel:channel_name});
}
function stop() {
  $.get("/stop");
}
"""
        head = tag("head", minimal_head)
        script = tag("script", scripts)
        body = tag("body", content + script)
        html = tag("html", head + body)
        text = "<!DOCTYPE html>" + html
        peername = request.transport.get_extra_info('peername')
        print("peername:", peername)
    
        headers = {'content-type': 'text/html'}
        return web.Response(headers=headers, text=text)

    async def music_menu(self, request):
        peername = request.transport.get_extra_info('peername')
        content = ""
        content += link("/", "Main Menu")
        content += button("play_list", "'svensk'", "Ulf Lundell & Bo Kasper")
        content += button("stop", "", "Stop")
        content += "<input name=\"title\" id=\"filter\" />\n"
        content += "<ol id=\"fruits\"></ol>\n"
        scripts = """
function play_list(playlist_name) {
  $.get("/play", {source:"list", query:playlist_name});
}
function stop() {
  $.get("/stop");
}
$('#filter').keyup(function() {
  var query = document.getElementById('filter').value
  $.get("/search", {title:query}, function(data, status){
    document.getElementById("fruits").innerHTML = "";
    var songs = JSON.parse(data);
    for (var key in songs) {
      var linode = document.createElement("LI");
      var divnode = document.createElement("DIV");
      var textnode = document.createTextNode(songs[key]["artist"] + " - " + songs[key]["title"]);
      linode.appendChild(divnode);
      divnode.appendChild(textnode);
      divnode.setAttribute("title", key);
      document.getElementById("fruits").appendChild(linode);
    }
  });
});
"""

        head = tag("head", minimal_head)
        script = tag("script", scripts)
        body = tag("body", content + script)
        html = tag("html", head + body)
        text = "<!DOCTYPE html>" + html

        headers = {'content-type': 'text/html'}
        return web.Response(headers=headers, text=text)

    async def stop(self, request):
        res = self.comm.call("music_server", "stop", {})
        res = self.comm.call("stream_receiver", "off", {})
        res = self.comm.call("led", "set", {"anim": ["off"]})
        text=res[1]
        headers = {'content-type': 'text/html'}
        return web.Response(headers=headers, text=text)

    async def radio(self, request):
        print("calling radio!")
        channel = request.rel_url.query['channel']
        res = self.comm.call("music_server", "stop", {})
        res = self.comm.call("stream_receiver", "radio", {"channel":[channel]})
        res = self.comm.call("led", "set", {"anim": ["tu"]})
        text=res[1]
        headers = {'content-type': 'text/html'}
        return web.Response(headers=headers, text=text)

    async def play(self, request):
        source = request.rel_url.query['source']
        if source == 'list':
            query = request.rel_url.query['query']
            res = self.comm.call("music_server", "play", {"source":[source], "query":[query]})
            res = self.comm.call("stream_receiver", "multicast", {})
            res = self.comm.call("led", "set", {"anim": ["mp"]})
            text=res[1]
        else:
            text = "source error"
        headers = {'content-type': 'text/html'}
        return web.Response(headers=headers, text=text)

    async def search(self, request):
        title = request.rel_url.query['title']
        res = self.comm.call("music_server", "search", {"title":[title]})
        text=res[1]
        headers = {'content-type': 'text/html'}
        return web.Response(headers=headers, text=text)

    def shut_down(self):
        print("begin stopping")
        self.comm.shut_down()
        print("done stopping")

if __name__ == '__main__':
    MicroServiceHandler("web_app", WebApp)
