import json
import random
import socket
import struct
import threading
import time
import urllib

class UnicastListener():
    def __init__(self, cb, port):
        self.cb = cb
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
                ret = (404, "Not found")
                a = message.find(b'/')
                if a != -1:
                    b = message.find(b' ', a)
                    if b != -1:
                        ret = self.cb(message[a+1:b])
                #Send one HTTP header line into socket
                if ret[0] == 200:
                    errorMsg = "OK"
                elif ret[0] == 404:
                    errorMsg = "Not Found"
                else:
                    errorMsg = "Other error"
                connectionSocket.send(bytes('HTTP/1.0 %d %s\r\n\r\n%s' % (ret[0], errorMsg, ret[1]), 'ascii'))
                #connectionSocket.send('404 Not Found')
                connectionSocket.close()
            except socket.timeout:
                pass
        print("closing serverSocket")
        self.serverSocket.close()

    def stop(self):
        self.running = False
        self.thread.join()

class UnicastSender():
    def __init__(self):
        pass

    def send(self, ip, port, function, args):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            s.connect((ip, port))
            s.sendall(bytes("GET /%s?%s HTTP/1.1\r\nHost: %s\r\n\r\n" % (function, urllib.parse.urlencode(args, doseq=True), ip), 'ascii'))
            ret_code = 500
            ret = "undefined"
            r = s.recv(4096).decode('ascii', 'ignore')
            print("r = '%s'" % r)
            a = r.find(' ')
            if a != -1:
                b = r.find(' ', a+1)
                if b != -1:
                    ret_code = int(r[a+1:b])
                    c = r.find('\r\n\r\n', b)
                    if c != -1:
                        ret = r[c+4:]
            s.close()
            return (ret_code, ret)
        except ConnectionRefusedError:
            print("Can't send. Connection refused!")
            return (521, "Connection refused!")

class MulticastListener():
    def __init__(self, cb):
        self.cb = cb
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
                self.cb(json.loads(r))
                time.sleep(1)
            except socket.timeout:
                pass
        print("closing multicast socket")
        self.sock.close()

    def stop(self):
        self.running = False
        self.thread.join()

class MulticastSender():
    def __init__(self, service_name, functions):
        self.service_name = service_name
        self.functions = functions
        start_sleep = random.randint(500,1000)/1000.0
        self.timer = threading.Timer(start_sleep, self.send_whos_there)
        self.timer.start()

    def send_whos_there(self):
        msg = json.dumps({"cmd": "whos_there"})
        self.multicast(msg)

    def send_im_here(self, ip, port):
        msg = json.dumps({"cmd": "im_here", "port": port, "service": self.service_name, "functions": self.functions, "ip": ip})
        self.multicast(msg)

    def multicast(self, msg):
        print("multicasting %s" % msg)
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
        self.timer.cancel()


class Comm():
    def __init__(self, port, service_name, functions):
        self.ip = self.get_ip()
        self.port = port
        self.service = service_name
        self.functions = functions
        self.others = {}
        self.multicast_listener = MulticastListener(lambda data: self.mc_received(data))
        self.multicast_sender = MulticastSender(service_name, list(functions.keys()))
        self.unicast_listener = UnicastListener(lambda data: self.uc_received(data), self.port)
        self.unicast_sender = UnicastSender()
        start_sleep = random.randint(3000,3500)/1000.0
        self.timer = threading.Timer(start_sleep, self.send_im_here)
        self.timer.start()

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

    def uc_received(self, data):
        print("uc_received '%s'" % data)
        query = urllib.parse.urlsplit(data).query.decode('ascii')
        func  = urllib.parse.urlsplit(data).path.decode('ascii')
        params = urllib.parse.parse_qs(query)
        if func in self.functions:
            return self.functions[func](params)
        return (404, "Unknown function '%s'" % func)

    def mc_received(self, data):
        if ("port" in data) and data["port"] == self.port and ("ip" in data) and data["ip"] == self.ip:
            #mc message from my self
            return
        print("%s:%s received %s" % (self.ip, self.port, data))
        if data["cmd"] == "whos_there":
            self.multicast_sender.send_im_here(self.ip, self.port)
        if data["cmd"] == "im_here":
            if data["port"] == str(self.port):
                print("WARNING, identical ports: %s:%s (%s) and %s:%s (%s)" % (self.ip, self.port, self.service, data["ip"], data["port"], data["service"]))
            self.others[(data["ip"], data["port"])] = {"port": data["port"], "service": data["service"], "functions": data["functions"], "ip": data["ip"]}

    def send_im_here(self):
        self.multicast_sender.send_im_here(self.ip, self.port)

    def call(self, service, function, args):
        for other in self.others:
            if self.others[other]["service"] == service:
                return self.unicast_sender.send(self.others[other]["ip"], self.others[other]["port"], function, args)
        return (503, "Serive '%s' not available." % service)

    def shut_down(self):
        if self.port:
            self.unicast_listener.stop()
        self.multicast_listener.stop()
        self.multicast_sender.shut_down()
        self.timer.cancel()

