#!/usr/bin/env python3

from ping_server import PingThread
import unittest
import time

class TestPingThread(unittest.TestCase):

    def setUp(self):
        self.online = set()

    def mock_ping(self, ip):
        if ip in self.online:
            return True
        return False

    def test_onoffline(self):
        ping_thread = PingThread(60, self.mock_ping)
        ping_thread.add_ip("S", "10.0.0.1")
        ping_thread.add_ip("C", "10.0.0.2")
        ping_thread.add_alarm_onoffline("S", "-+", "1")
        test_time = time.struct_time((2012, 1, 1, 0, 0, 0, 1, 0, 0)) # 1 = Tuesday
        self.assertEqual([], ping_thread.do_something(test_time))
        self.online = {"10.0.0.1"}
        self.assertEqual(["S went online"], ping_thread.do_something(test_time))

    def test_timeofday(self):
        ping_thread = PingThread(60, self.mock_ping)
        ping_thread.add_ip("S", "10.0.0.1")
        ping_thread.add_ip("C", "10.0.0.2")
        ping_thread.add_alarm_timeofday("S", "1:00", "7:00", "01234")
        test_time = time.struct_time((2012, 1, 1, 0, 30, 0, 1, 0, 0)) # 1 = Tuesday time = 0:30:00
        self.assertEqual([], ping_thread.do_something(test_time))
        self.online = {"10.0.0.1"}
        test_time = time.struct_time((2012, 1, 1, 1, 30, 0, 1, 0, 0)) # 1 = Tuesday time = 1:30:00
        self.assertEqual(["S went online at 1:30"], ping_thread.do_something(test_time))
        test_time = time.struct_time((2012, 1, 1, 2, 30, 0, 1, 0, 0)) # 1 = Tuesday time = 2:30:00
        self.assertEqual([], ping_thread.do_something(test_time))

    def test_dayamount(self):
        ping_thread = PingThread(60, self.mock_ping) # 60 seconds interval
        ping_thread.add_ip("S", "10.0.0.1")
        #ping_thread.add_ip("C", "10.0.0.2")
        ping_thread.add_alarm_dayamount("S", 3, "01234") # 3 minutes max amount
        test_time = time.struct_time((2012, 1, 1, 0, 0, 0, 1, 0, 0))
        self.assertEqual([], ping_thread.do_something(test_time))
        self.assertEqual([], ping_thread.do_something(test_time))
        self.online = {"10.0.0.1"}
        self.assertEqual([], ping_thread.do_something(test_time))
        self.assertEqual([], ping_thread.do_something(test_time))
        self.assertEqual(["S exceeded amount 3"], ping_thread.do_something(test_time))
        self.assertEqual([], ping_thread.do_something(test_time))

    def test_m_get_log(self):
        ping_thread = PingThread(60, self.mock_ping)
        ping_thread.add_ip("S", "10.0.0.1")
        ping_thread.do_something(time.struct_time((2012, 1, 1, 0, 0, 0, 1, 0, 0)))
        self.online = {"10.0.0.1"}
        ping_thread.do_something(time.struct_time((2012, 1, 1, 0, 5, 0, 1, 0, 0)))
        ping_thread.do_something(time.struct_time((2012, 1, 1, 0, 15, 0, 1, 0, 0)))
        self.online = {}
        ping_thread.do_something(time.struct_time((2012, 1, 1, 3, 55, 0, 1, 0, 0)))
        self.assertEqual("+0:05\n-3:55\n", ping_thread.m_get_log("S"))

        self.online = {"10.0.0.1"}
        ping_thread.do_something(time.struct_time((2012, 1, 2, 4, 0, 0, 1, 0, 0)))
        self.online = {}
        ping_thread.do_something(time.struct_time((2012, 1, 2, 5, 0, 0, 1, 0, 0)))
        self.assertEqual("+4:00\n-5:00\n", ping_thread.m_get_log("S"))
        self.assertEqual("+0:05\n-3:55\n", ping_thread.m_get_log("S", (2012,1,1)))

if __name__ == '__main__':
    unittest.main()
