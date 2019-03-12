import asyncio
import json
import random
import requests
import socket
import struct
import sys
import threading
import time
from multi_dict_to_dict_of_lists import multi_dict_to_dict_of_lists
from aiohttp import web

class UnicastListener():
    def __init__(self, cb, port, logger, exc_cb):
        self.cb = cb
        self.exc_cb = exc_cb

        self.loop = asyncio.get_event_loop()
        self.app1 = web.Application()
        self.app1.router.add_route('GET', '/{tail:.*}', self.handle)
        self.handler1 = self.app1.make_handler()
        coroutine1 = self.loop.create_server(self.handler1, '0.0.0.0', port)
        self.server1 = self.loop.run_until_complete(coroutine1)

    def stop(self):
        self.loop.run_until_complete(self.app1.shutdown())
        self.loop.run_until_complete(self.handler1.shutdown(60.0))
        #self.loop.run_until_complete(self.handler1.finish_connections(1.0))
        self.loop.run_until_complete(self.app1.cleanup())

    async def handle(self, request):
        try:
            peername = request.transport.get_extra_info('peername')
            if peername is None:
                ip, port = '0.0.0.0', 0
            else:
                ip, port = peername
            headers = {'content-type': 'text/json'}
            d = request.rel_url.query
            # Convert MultiDict 'd' to dict of lists 'e':
            e = multi_dict_to_dict_of_lists(d)
            ret = self.cb(request.path[1:], e, ip, port)
            return web.Response(headers=headers, text=ret[1], status=ret[0])
        except Exception as e:
            await self.exc_cb(sys.exc_info())
            return web.Response(headers=headers, text="caugt exception", status=500)

class UnicastSender():
    def __init__(self, logger):
        self.logger = logger

    def args_to_html(self, args):
        if len(args) == 0:
            return ""
        ret = ""
        for k, v in args.items():
            for a in v:
                if len(ret):
                    ret += "&"
                ret += k + "=" + a
        return "?" + ret

    def send(self, ip, port, function, args):
        req = "http://%s:%s/%s%s" % (ip, port, function, self.args_to_html(args))
        try:
            resp0 = requests.get(req)
            if resp0.ok:
                return (200, resp0.text)
            else:
                return (405, resp0.text)
        except:
            return (406, "exception occured")

class MulticastListener():
    def __init__(self, cb, logger, exc_cb):
        self.cb = cb
        self.logger = logger
        self.exc_cb = exc_cb
        self.running = True
        mcast_grp = '224.1.1.1'
        mcast_port = 5007
        is_all_groups = True

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(2.0)
        if is_all_groups:
            # on this port, receives ALL multicast groups
            self.sock.bind(('', mcast_port))
        else:
            # on this port, listen ONLY to mcast_grp
            self.sock.bind((mcast_grp, mcast_port))
        mreq = struct.pack("4sl", socket.inet_aton(mcast_grp), socket.INADDR_ANY)

        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.thread = threading.Thread(target=self.run, args=())
        #self.thread.daemon = True
        self.thread.start()

    def run(self):
        while self.running:
            try:
                r = self.sock.recv(10240)
                self.cb(r)
                time.sleep(1)
            except socket.timeout:
                pass
            except:
                self.exc_cb(sys.exc_info())
        self.logger.log("closing multicast socket")
        self.sock.close()

    def stop(self):
        self.running = False
        self.thread.join()

class MulticastSender():
    def __init__(self, logger):
        self.logger = logger

    def multicast(self, msg):
        self.logger.log("multicasting %s" % msg)
        mcast_grp = '224.1.1.1'
        mcast_port = 5007
        # regarding socket.IP_MULTICAST_TTL
        # ---------------------------------
        # for all packets sent, after two hops on the network the packet will not
        # be re-sent/broadcast (see https://www.tldp.org/HOWTO/Multicast-HOWTO-6.html)
        multicast_ttl = 2

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, multicast_ttl)
        bb = bytes(str(msg), 'ascii')
        sock.sendto(bb, (mcast_grp, mcast_port))

class Comm():
    def __init__(self, port, service_name, functions, logger, exc_cb):
        self.logger = logger
        self.port = port
        self.service = service_name
        self.functions = functions
        self.others = {}
        self.logger.log("logger just started")
        ok = False
        while not ok:
            try:
                self.ip = self.get_ip()
                self.multicast_listener = MulticastListener(self.mc_received, self.logger, exc_cb)
                self.multicast_sender = MulticastSender(self.logger)
                self.unicast_listener = UnicastListener(self.uc_received, self.port, self.logger, exc_cb)
                self.unicast_sender = UnicastSender(self.logger)
                ok = True
            except OSError:
                self.logger.log("waiting for network connection")
                time.sleep(1)
        start_sleep = random.randint(500, 1000)/1000.0
        self.startup_timer = threading.Timer(start_sleep, self.startup)
        self.startup_timer.start()
        self.im_here_timer = None

    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def uc_received(self, path, params, ip, port):
        #self.logger.log("uc_received: '%s(%s)' from '%s:%d'" % (path, str(params), ip, port))
        if path in self.functions:
            return self.functions[path](params)
        return (404, "Unknown function '%s'" % path)

    def mc_received(self, r):
        data = json.loads(r.decode("ascii"))
        if ("port" in data) and data["port"] == self.port and ("ip" in data) and data["ip"] == self.ip:
            #mc message from my self
            return
        self.logger.log("%s:%s received %s" % (self.ip, self.port, data))
        if data["cmd"] == "whos_there":
            self.send_im_here_timed()
        if data["cmd"] == "im_here":
            if data["port"] == str(self.port):
                self.logger.log("Error, identical ports: %s:%s (%s) and %s:%s (%s)" % (self.ip, self.port, self.service, data["ip"], data["port"], data["service"]))
            self.others[(data["ip"], data["port"])] = {"port": data["port"], "service": data["service"], "functions": data["functions"], "ip": data["ip"]}

    def startup(self):
        self.logger.log("sending who's there")
        msg = json.dumps({"cmd": "whos_there"})
        self.multicast_sender.multicast(msg)
        self.send_im_here_timed()

    def send_im_here_timed(self):
        if self.im_here_timer != None:
            self.im_here_timer.cancel()
        im_here_sleep = random.randint(3000, 3500)/1000.0
        self.im_here_timer = threading.Timer(im_here_sleep, self.send_im_here)
        self.im_here_timer.start()

    def send_im_here(self):
        msg = json.dumps({"cmd": "im_here", "port": self.port, "service": self.service, "functions": list(self.functions.keys()), "ip": self.ip})
        self.multicast_sender.multicast(msg)

    def call(self, service, function, args):
        for other in self.others:
            if self.others[other]["service"] == service:
                return self.unicast_sender.send(self.others[other]["ip"], self.others[other]["port"], function, args)
        return (503, "Service '%s' not available." % service)

    def shut_down(self):
        self.startup_timer.cancel()
        self.im_here_timer.cancel()
        self.unicast_listener.stop()
        self.multicast_listener.stop()

