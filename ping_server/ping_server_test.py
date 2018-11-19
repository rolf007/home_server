#!/usr/bin/env python3

from ping_server import PingThread
import unittest
import time

class TestPingThread(unittest.TestCase):

    def setUp(self):
        pass

    def foo(self, ip):
        print("fooing '%s'" % ip)
        return 0

    def test_simple(self):
        ping_thread = PingThread(0, self.foo)
        ping_thread.add_ip("1", "alpha")
        ping_thread.add_ip("2", "beta")
        ping_thread.add_timeofday_alarm("1:00", "7:00", "01234", "S")
        test_time = time.struct_time((2012, 1, 1, 0, 0, 0, 1, 0, 0)) # 1 = Tuesday
        ping_thread.do_something(test_time)

if __name__ == '__main__':
    unittest.main()
