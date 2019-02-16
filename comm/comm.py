import json
import random
import socket
import struct
import threading
import time
import urllib.parse

class UnicastListener():
    def __init__(self, cb, port, logger):
        self.cb = cb
        self.logger = logger
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #Prepare a sever socket
        self.serverSocket.bind(('', port))
        self.serverSocket.listen(1)
        self.serverSocket.settimeout(2.0)
        self.running = True

        self.thread = threading.Thread(target=self.run, args=())
        #self.thread.daemon = True
        self.thread.start()

    def run(self):
        while self.running:
            try:
                #Establish the connection
                connectionSocket, addr = self.serverSocket.accept()
                message = connectionSocket.recv(1024)
                message = message.decode('utf-8', 'ignore')
                ret = (404, "Not found")
                a = message.find('/')
                if a != -1:
                    b = message.find(' ', a)
                    if b != -1:
                        data = message[a+1:b]
                        self.logger.log("comm listener received %s" % data)
                        path  = urllib.parse.urlsplit(data).path
                        query = urllib.parse.urlsplit(data).query
                        params = urllib.parse.parse_qs(query)
                        ret = self.cb(path, params, addr[0], addr[1])
                #Send one HTTP header line into socket
                if ret[0] == 200:
                    errorMsg = "OK"
                elif ret[0] == 404:
                    errorMsg = "Not Found"
                else:
                    errorMsg = "Other error"
                self.logger.log("comm listener replying %s" % ret[1])
                connectionSocket.send(bytes('HTTP/1.0 %d %s\r\n\r\n' % (ret[0], errorMsg), 'ascii') + ret[1].encode('utf-8', 'ignore'))
                #connectionSocket.send('404 Not Found')
                connectionSocket.close()
            except socket.timeout:
                pass
        self.logger.log("closing serverSocket")
        self.serverSocket.close()

    def stop(self):
        self.running = False
        self.thread.join()

class UnicastSender():
    def __init__(self, logger):
        self.logger = logger

    def send(self, ip, port, function, args):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            s.connect((ip, port))
            req = "%s?%s" % (function, urllib.parse.urlencode(args, doseq=True))
            self.logger.log("sender sending %s" % req)
            s.sendall(bytes("GET /%s HTTP/1.1\r\nHost: %s\r\n\r\n" % (req, ip), 'ascii'))
            ret_code = 500
            ret = "undefined"
            r = s.recv(4096).decode('utf-8', 'ignore')
            self.logger.log("sender received = %s" % r)
            a = r.find(' ')
            if a != -1:
                b = r.find(' ', a+1)
                if b != -1:
                    ret_code = int(r[a+1:b])
                    c = r.find('\r\n\r\n', b)
                    if c != -1:
                        ret = r[c+4:]
            s.close()
            self.logger.log("sender received %s" % ret)
            return (ret_code, ret)
        except ConnectionRefusedError:
            self.logger.log("Error: Can't send. Connection refused!")
            return (521, "Connection refused!")

class MulticastListener():
    def __init__(self, cb, logger):
        self.cb = cb
        self.logger = logger
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
        self.thread = threading.Thread(target=self.runme, args=())
        #self.thread.daemon = True
        self.thread.start()

    def runme(self):
        while self.running:
            try:
                r = self.sock.recv(10240)
                self.cb(r)
                time.sleep(1)
            except socket.timeout:
                pass
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

    def shut_down(self):
        pass


class Comm():
    def __init__(self, port, service_name, functions, logger, try_for_a_while = 10):
        self.logger = logger
        self.logger.log("logger just started")
        ok = False
        while not ok:
            try:
                self.ip = self.get_ip()
                self.port = port
                self.service = service_name
                self.functions = functions
                self.others = {}
                self.multicast_listener = MulticastListener(lambda data: self.mc_received(data), self.logger)
                self.multicast_sender = MulticastSender(self.logger)
                self.unicast_listener = UnicastListener(self.uc_received, self.port, self.logger)
                self.unicast_sender = UnicastSender(self.logger)
                start_sleep = random.randint(500, 1000)/1000.0
                self.startup_timer = threading.Timer(start_sleep, self.startup)
                self.startup_timer.start()
                self.im_here_timer = None
                ok = True
            except Exception as e:
                self.logger.log("error: %s" % e)
                time.sleep(1)
                try_for_a_while -= 1
                if try_for_a_while == 0:
                    raise e

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
        self.logger.log("uc_received: '%s(%s)' from '%s:%d'" % (path, str(params), ip, port))
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
        if self.port:
            self.unicast_listener.stop()
        self.multicast_listener.stop()
        self.multicast_sender.shut_down()
        self.startup_timer.cancel()
        self.im_here_timer.cancel()

