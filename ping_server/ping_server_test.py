#!/usr/bin/env python3

from ping_server import PingThread
import unittest
import time

class TestPingThread(unittest.TestCase):

    def setUp(self):
        self.online = set()

    def foo(self, ip):
        print("fooing '%s' in %s" % (ip, self.online))
        if ip in self.online:
            return 0
        return 1

    def test_onoffline(self):
        ping_thread = PingThread(0, self.foo)
        ping_thread.add_ip("S", "10.0.0.1")
        ping_thread.add_ip("C", "10.0.0.2")
        ping_thread.add_alarm_onoffline("S", "-+", "2")
        #ping_thread.add_alarm_timeofday("S", "01234", "1:00", "7:00")
        test_time = time.struct_time((2012, 1, 1, 0, 0, 0, 1, 0, 0)) # 1 = Tuesday
        ping_thread.do_something(test_time)
        self.online = {"10.0.0.1"}
        ping_thread.do_something(test_time)

if __name__ == '__main__':
    unittest.main()
