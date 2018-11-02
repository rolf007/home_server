#!/usr/bin/env python3

#import socket module
from socket import socket, AF_INET, SOCK_STREAM
import threading
import time

port = 12005

class HttpThread():
    def __init__(self, cb):
        self.cb = cb
        self.serverSocket = socket(AF_INET, SOCK_STREAM)
        #Prepare a sever socket
        self.serverSocket.bind(('', port))
        self.serverSocket.listen(1)
        self.i = 7
        self.running = True

        self.thread = threading.Thread(target=self.run, args=())
#        self.thread.daemon = True                            # Daemonize thread
        self.thread.start()                                  # Start the execution

    def run(self):
        while self.running:
            #Establish the connection
            connectionSocket, addr = self.serverSocket.accept()
            try:
                message = connectionSocket.recv(1024)
                ret = None
                a = message.find(b'/')
                if a != -1:
                    b = message.find(b' ', a)
                    if b != -1:
                        ret = cb(message[a+1:b])
                #Send one HTTP header line into socket
                connectionSocket.send(bytes('HTTP/1.0 200 OK\r\n\r\n', 'ascii'))
                #Send the content of the requested file to the client
                if ret:
                    connectionSocket.send(bytes(ret, 'ascii'))
                self.i = self.i + 1
                connectionSocket.close()
            except IOError:
                #Send response message for file not found
                connectionSocket.send('404 Not Found')
                #Close client socket
                connectionSocket.close()

    def stop(self):
        self.serverSocket.close() 
        self.running = False


class HttpComm():
    def __init__(self, cb):
        self.cb = cb
        self.http_thread = HttpThread(cb)

    def call(self, host, port, args):
        s = socket(AF_INET, SOCK_STREAM)                 
        
        s.connect((host, port))
        s.sendall(bytes("GET /%s HTTP/1.1\r\nHost: %s\r\n\r\n" % (args, host), 'ascii'))
        ret = None
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

    def shut_down(self):
        self.http_thread.stop()

def cb(msg):
    print("called: %s" % msg)
    return "HEJ"

http_comm = HttpComm("cb")
try:
    while True:
        print("!Q")
        time.sleep(5)
        ret = http_comm.call("127.0.0.1", port, "hello2")
        print("returns '%s'" % ret)
except KeyboardInterrupt:
    print("shutting down!")
    http_comm.shut_down()
    print("shutted down!")

