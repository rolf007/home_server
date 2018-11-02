#!/usr/bin/env python3
import json
import random
import socket
import struct
import threading
import time
import uuid


class Receiver():
    def __init__(self):
        self.uuid = uuid.uuid4()
        MCAST_GRP = '224.1.1.1'
        MCAST_PORT = 5007
        IS_ALL_GROUPS = True
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if IS_ALL_GROUPS:
            # on this port, receives ALL multicast groups
            self.sock.bind(('', MCAST_PORT))
        else:
            # on this port, listen ONLY to MCAST_GRP
            self.sock.bind((MCAST_GRP, MCAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        thread = threading.Thread(target=self.runme, args=())
        #thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution
        start_sleep = random.randint(500,1000)/1000.0
        self.timer = threading.Timer(start_sleep, self.start_send)
        self.timer.start()

    def runme(self):
        print("runme")
        while True:
          print("%s received %s" % (self.uuid, self.sock.recv(10240)))
          time.sleep(1)

    def start_send(self):
        whos_there = json.dumps({"cmd": "whos_there", "uuid": str(self.uuid)})
        self.broadcast(whos_there)

    def broadcast(self, msg):
        print("broadcasting %s" % msg)
        MCAST_GRP = '224.1.1.1'
        MCAST_PORT = 5007
        # regarding socket.IP_MULTICAST_TTL
        # ---------------------------------
        # for all packets sent, after two hops on the network the packet will not 
        # be re-sent/broadcast (see https://www.tldp.org/HOWTO/Multicast-HOWTO-6.html)
        MULTICAST_TTL = 2
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)
        bb = bytes(str(msg), 'ascii')
        sock.sendto(bb, (MCAST_GRP, MCAST_PORT))

receiver = Receiver()

