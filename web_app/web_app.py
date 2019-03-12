#!/usr/bin/env python3

import asyncio
import os
import sys
import uuid
from aiohttp import web
home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])
sys.path.append(os.path.join(home_server_root, "comm"))
sys.path.append(os.path.join(home_server_root, "utils"))
from comm import Comm
from multi_dict_to_dict_of_lists import multi_dict_to_dict_of_lists
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
                        web.get('/get_search_result', self.get_search_result),
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
        if peername[0] == '192.168.0.11':
            content += "<h2>Welcome rolf</h2><br>"
            content += button("play_list", "'metal'", "Rolf")
        elif peername[0] == '192.168.0.13':
            content += "<h2>Velkommen Karen</h2><br>"
        content += button("play_list", "'svensk'", "Ulf Lundell & Bo Kasper")
        content += button("stop", "", "Stop")
        content += "<input name=\"title\" id=\"filter\" />\n"
        content += button("play", "", "Play")
        content += "<ol id=\"fruits\"></ol>\n"
        scripts = "session_id ={session_id};".format(session_id = '"' + str(uuid.uuid4()) +'"')
        scripts += """
function play_list(playlist_name) {
  $.get("/play", {source:"list", query:playlist_name});
}
function stop() {
  $.get("/stop");
}
function play() {
  var title = document.getElementById('filter').value
  $.get("/play", {source:"collection", title:title});
}

polling = 0
$('#filter').keyup(function() {
  var query = document.getElementById('filter').value;
  $.get("/search", {title:query, session_id:session_id}, function(data0, status){
    //var n_res = JSON.parse(data0);
    if (!polling) {
      polling = 1;
      setTimeout(poll, 50);
    }
  });
});

function poll()
{
  $.get("/get_search_result", {session_id:session_id}, function(data, status){
    polling = 0;
    document.getElementById("fruits").innerHTML = "";
    try {
      var songs = JSON.parse(data);
    } catch(e) {
      console.log("bad json");
      console.log(data)
      return;
    }
    if (songs.status == "available") {
      for (var key in songs.result) {
        var linode = document.createElement("LI");
        var divnode = document.createElement("DIV");
        var textnode = document.createTextNode(songs.result[key]["artist"] + " - " + songs.result[key]["title"]);
        linode.appendChild(divnode);
        divnode.appendChild(textnode);
        divnode.setAttribute("title", key);
        document.getElementById("fruits").appendChild(linode);
      }
    } else if (songs.status == "in_progress") {
      polling = 1;
      setTimeout(poll, 50);
    }
  }).fail(function(jq){
      console.log("failure");
      console.log(jq.responseText);
      console.log(jq.status);
  });
};
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
        headers = {'content-type': 'text/html'}
        return web.Response(headers=headers, status=res[0], text=res[1])

    async def radio(self, request):
        print("calling radio!")
        args = multi_dict_to_dict_of_lists(request.rel_url.query)
        res = self.comm.call("music_server", "stop", {})
        res = self.comm.call("stream_receiver", "radio", args)
        res = self.comm.call("led", "set", {"anim": ["tu"]})
        headers = {'content-type': 'text/html'}
        return web.Response(headers=headers, status=res[0], text=res[1])

    async def play(self, request):
        args = multi_dict_to_dict_of_lists(request.rel_url.query)
        res = self.comm.call("music_server", "play", args)
        res = self.comm.call("stream_receiver", "multicast", {})
        res = self.comm.call("led", "set", {"anim": ["mp"]})
        headers = {'content-type': 'text/html'}
        return web.Response(headers=headers, status=res[0], text=res[1])

    async def search(self, request):
        args = multi_dict_to_dict_of_lists(request.rel_url.query)
        res = self.comm.call("music_server", "search", args)
        headers = {'content-type': 'text/html'}
        return web.Response(headers=headers, status=res[0], text=res[1])

    async def get_search_result(self, request):
        args = multi_dict_to_dict_of_lists(request.rel_url.query)
        res = self.comm.call("music_server", "get_search_result", args)
        headers = {'content-type': 'text/html'}
        return web.Response(headers=headers, status=res[0], text=res[1])

    def shut_down(self):
        print("begin stopping")
        self.comm.shut_down()
        print("done stopping")

if __name__ == '__main__':
    MicroServiceHandler("web_app", WebApp)
