#!/usr/bin/env python3
import comm
import time

def cb_a(msg):
    print("A called: %s" % msg)
    return "I'm-A"

def cb_a2(msg):
    print("A2 called: %s" % msg)
    return "I'm-A2"

comm = comm.Comm("serviceA", {"funcA": cb_a, "funcA2": cb_a2})
try:
    while True:
        time.sleep(5)
#        ret = comm.call("serviceB", "funcB", "I'm-A,-who-are-you?")
#        print("I'm A, who are you? returns '%s'" % ret)
except KeyboardInterrupt:
    print("shutting down!")
    comm.shut_down()
    print("shutted down!")


