#!/usr/bin/env python3
import comm
import time

def cb_x(msg):
    print("B called: %s" % msg)
    return "I'm-B"

comm = comm.Comm("serviceB", {"funcB": cb_x})
try:
    while True:
        time.sleep(5)
        ret = comm.call("serviceA", "funcA2", "I'm-B,-who-are-you?")
        print("I'm B, who are you? returns '%s'" % ret)
except KeyboardInterrupt:
    print("shutting down!")
    comm.shut_down()
    print("shutted down!")


