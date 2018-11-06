import json
import random
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, timeout, inet_aton, SOCK_DGRAM, IPPROTO_UDP, INADDR_ANY, IPPROTO_IP, IP_ADD_MEMBERSHIP, IP_MULTICAST_TTL
import struct
import threading
import time
import uuid
import urllib

def get_ip():
    s = socket(AF_INET, SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

class UnicastListener():
    def __init__(self, cb, port):
        self.cb = cb
        self.serverSocket = socket(AF_INET, SOCK_STREAM)
        self.serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        #Prepare a sever socket
        self.serverSocket.bind(('', port))
        self.serverSocket.listen(1)
        self.serverSocket.settimeout(2.0)
        self.i = 7
        self.running = True

        self.thread = threading.Thread(target=self.run, args=())
#        self.thread.daemon = True                            # Daemonize thread
        self.thread.start()                                  # Start the execution

    def run(self):
        while self.running:
            try:
                #Establish the connection
                connectionSocket, addr = self.serverSocket.accept()
                message = connectionSocket.recv(1024)
                ret = ""
                a = message.find(b'/')
                if a != -1:
                    b = message.find(b' ', a)
                    if b != -1:
                        ret = self.cb(message[a+1:b])
                #Send one HTTP header line into socket
                connectionSocket.send(bytes('HTTP/1.0 200 OK\r\n\r\n%s'%ret, 'ascii'))
                #connectionSocket.send('404 Not Found')
                #Send the content of the requested file to the client
                self.i = self.i + 1
                connectionSocket.close()
            except timeout:
                pass
                #Close client socket
                #connectionSocket.close()
        print("closing serverSocket")
        self.serverSocket.close()

    def stop(self):
        self.running = False
        self.thread.join()

class UnicastSender():
    def __init__(self):
        pass

    def send(self, ip, port, function, args):
        s = socket(AF_INET, SOCK_STREAM)

        try:
            s.connect((ip, port))
            s.sendall(bytes("GET /%s?%s HTTP/1.1\r\nHost: %s\r\n\r\n" % (function, urllib.parse.urlencode(args, doseq=True), ip), 'ascii'))
            ret = "undefined"
            r = s.recv(4096)
            a = r.find(b' ')
            if a != -1:
                b = r.find(b' ', a+1)
                if b != -1:
                    if r[a+1:b] == b"200":
                        c = r.find(b'\r\n\r\n', b)
                        if c != -1:
                            ret = r[c+4:]
            s.close()
            return ret
        except ConnectionRefusedError:
            print("Can't send. Connection refused!")

class MulticastListener():
    def __init__(self, cb):
        self.cb = cb
        self.running = True
        MCAST_GRP = '224.1.1.1'
        MCAST_PORT = 5007
        IS_ALL_GROUPS = True

        self.sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.settimeout(2.0)
        if IS_ALL_GROUPS:
            # on this port, receives ALL multicast groups
            self.sock.bind(('', MCAST_PORT))
        else:
            # on this port, listen ONLY to MCAST_GRP
            self.sock.bind((MCAST_GRP, MCAST_PORT))
        mreq = struct.pack("4sl", inet_aton(MCAST_GRP), INADDR_ANY)

        self.sock.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)
        self.thread = threading.Thread(target=self.runme, args=())
        #self.thread.daemon = True                            # Daemonize thread
        self.thread.start()                                  # Start the execution

    def runme(self):
        while self.running:
            try:
                r = self.sock.recv(10240)
                self.cb(json.loads(r))
                time.sleep(1)
            except timeout:
                pass
        print("closing multicast socket")
        self.sock.close()

    def stop(self):
        self.running = False
        self.thread.join()

class MulticastSender():
    def __init__(self, my_uuid, service_name, functions):
        self.uuid = my_uuid
        self.service_name = service_name
        self.functions = functions
        start_sleep = random.randint(500,1000)/1000.0
        self.timer = threading.Timer(start_sleep, self.send_whos_there)
        self.timer.start()
        self.ip = get_ip()

    def send_whos_there(self):
        whos_there = json.dumps({"cmd": "whos_there", "uuid": str(self.uuid)})
        self.multicast(whos_there)

    def send_im_here(self, port):
        whos_there = json.dumps({"cmd": "im_here", "uuid": str(self.uuid), "port": port, "service": self.service_name, "functions": self.functions, "ip": self.ip})
        self.multicast(whos_there)

    def multicast(self, msg):
        print("multicasting %s" % msg)
        MCAST_GRP = '224.1.1.1'
        MCAST_PORT = 5007
        # regarding socket.IP_MULTICAST_TTL
        # ---------------------------------
        # for all packets sent, after two hops on the network the packet will not
        # be re-sent/broadcast (see https://www.tldp.org/HOWTO/Multicast-HOWTO-6.html)
        MULTICAST_TTL = 2

        sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        sock.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, MULTICAST_TTL)
        bb = bytes(str(msg), 'ascii')
        sock.sendto(bb, (MCAST_GRP, MCAST_PORT))


class Comm():
    def __init__(self, service_name, functions):
        self.functions = functions
        self.port = None
        self.others = {}
        self.uuid = uuid.uuid4()
        self.multicast_listener = MulticastListener(lambda data: self.mc_received(data))
        self.multicast_sender = MulticastSender(self.uuid, service_name, list(functions.keys()))
        self.unicast_listener = None
        self.unicast_sender = UnicastSender()
        start_sleep = random.randint(3000,3500)/1000.0
        self.timer = threading.Timer(start_sleep, self.configure_unicast)
        self.timer.start()

    def uc_received(self, data):
        print("uc_received '%s'" % data)
        query = urllib.parse.urlsplit(data).query
        func  = urllib.parse.urlsplit(data).path.decode('ascii')
        params = urllib.parse.parse_qs(query)
        if func in self.functions:
            return self.functions[func](params)
        return None

    def mc_received(self, data):
        recv_uuid = uuid.UUID(data["uuid"])
        if recv_uuid == self.uuid:
            return
        print("%s received %s" % (self.uuid, data))
        if data["cmd"] == "whos_there":
            if self.port:
                self.multicast_sender.send_im_here(self.port)
        if data["cmd"] == "im_here":
            self.others[recv_uuid] = {"port": data["port"], "service": data["service"], "functions": data["functions"], "ip": data["ip"]}


    def configure_unicast(self):
        self.port = random.randint(5000,5999)
        self.unicast_listener = UnicastListener(lambda data: self.uc_received(data), self.port)
        self.multicast_sender.send_im_here(self.port)

    def call(self, service, function, args):
        for other in self.others:
            if self.others[other]["service"] == service:
                return self.unicast_sender.send(self.others[other]["ip"], self.others[other]["port"], function, args)
        return "not ready"

    def shut_down(self):
        if self.port:
            self.unicast_listener.stop()
        self.multicast_listener.stop()

