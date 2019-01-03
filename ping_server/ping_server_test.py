#!/usr/bin/env python3

from ping_server import PingThread
import unittest
import time

class TestPingThread(unittest.TestCase):

    def setUp(self):
        self.online = set()
        self.ping_thread = PingThread(60, self.mock_ping)
        self.alarms = []

    def mock_ping(self, ip):
        if ip in self.online:
            return True
        return False

    def mock_alarm(self, alarm):
        self.alarms.append(alarm)

    def do_something(self, year, mon, day, hour, min, weekday):
        self.alarms = []
        test_time = time.struct_time((year, mon, day, hour, min, 0, weekday, 0, 0)) # 1 = Tuesday
        self.ping_thread.do_something(test_time)
        return self.alarms

    def test_onoffline(self):
        self.ping_thread.add_ip("S", "10.0.0.1")
        self.ping_thread.add_ip("C", "10.0.0.2")
        self.ping_thread.add_alarm_onoffline("S", self.mock_alarm, "-+", "1")
        self.assertEqual([], self.do_something(2012, 1, 1, 0, 0, 1))
        self.online = {"10.0.0.1"}
        self.assertEqual(["S went online"], self.do_something(2012, 1, 1, 0, 5, 1))
        self.online = {}
        self.assertEqual([], self.do_something(2012, 1, 1, 0, 10, 1))
        self.online = {"10.0.0.1"}
        self.assertEqual([], self.do_something(2012, 1, 1, 0, 15, 1))
        self.ping_thread.reset_alarms()
        self.online = {}
        self.assertEqual(["S went offline"], self.do_something(2012, 1, 1, 0, 20, 1))

    def test_onoffline_online_at_start(self):
        self.ping_thread.add_ip("S", "10.0.0.1")
        self.ping_thread.add_alarm_onoffline("S", self.mock_alarm, "-+", "1")
        self.online = {"10.0.0.1"}
        self.assertEqual([], self.do_something(2012, 1, 1, 0, 0, 1))

    def test_timeofday(self):
        self.ping_thread.add_ip("S", "10.0.0.1")
        self.ping_thread.add_ip("C", "10.0.0.2")
        self.ping_thread.add_alarm_timeofday("S", self.mock_alarm, "1:00", "7:00", "01234")
        self.assertEqual([], self.do_something(2012, 1, 1, 0, 30, 1))
        self.online = {"10.0.0.1"}
        self.assertEqual(["S is online at 1:30"], self.do_something(2012, 1, 1, 1, 30, 1))
        self.assertEqual([], self.do_something(2012, 1, 1, 2, 30, 1))
        self.online = {}
        self.assertEqual([], self.do_something(2012, 1, 1, 2, 40, 1))
        self.online = {"10.0.0.1"}
        self.assertEqual([], self.do_something(2012, 1, 1, 2, 50, 1))
        self.online = {}
        self.assertEqual([], self.do_something(2012, 1, 2, 1, 10, 1))
        self.online = {"10.0.0.1"}
        self.assertEqual(["S is online at 1:15"], self.do_something(2012, 1, 2, 1, 15, 1))

    def test_timeofday_online_at_start(self):
        self.ping_thread.add_ip("S", "10.0.0.1")
        self.ping_thread.add_alarm_timeofday("S", self.mock_alarm, "1:00", "7:00", "01234")
        self.online = {"10.0.0.1"}
        self.assertEqual([], self.do_something(2012, 1, 1, 1, 30, 1))

    def test_dayamount(self):
        self.ping_thread.add_ip("S", "10.0.0.1")
        self.ping_thread.add_ip("C", "10.0.0.2")
        self.ping_thread.add_alarm_dayamount("S", self.mock_alarm, 3, "01234") # 3 minutes max amount
        self.assertEqual([], self.do_something(2012, 1, 1, 0, 0, 1))
        self.assertEqual([], self.do_something(2012, 1, 1, 0, 1, 1))
        self.online = {"10.0.0.1"}
        self.assertEqual([], self.do_something(2012, 1, 1, 0, 2, 1))
        self.assertEqual([], self.do_something(2012, 1, 1, 0, 3, 1))
        self.assertEqual(["S exceeded amount 3"], self.do_something(2012, 1, 1, 0, 5, 1))
        self.assertEqual([], self.do_something(2012, 1, 1, 0, 5, 1))

    def test_m_get_log(self):
        self.assertEqual("unknown user 'S'", self.ping_thread.m_get_log("S"))
        self.ping_thread.add_ip("S", "10.0.0.1")
        self.ping_thread.add_ip("C", "10.0.0.2")
        self.assertEqual("=0", self.ping_thread.m_get_log("S"))
        self.do_something(2012, 1, 1, 0, 2, 1)
        self.online = {"10.0.0.1", "10.0.0.2"}
        self.do_something(2012, 1, 1, 0, 5, 1)
        self.do_something(2012, 1, 1, 0, 15, 1)
        self.online = {"10.0.0.2"}
        self.do_something(2012, 1, 1, 3, 45, 1)
        self.do_something(2012, 1, 1, 3, 50, 1)
        self.assertEqual("+0:05-3:45\n=220", self.ping_thread.m_get_log("S"))
        self.assertEqual("+0:05\n=225", self.ping_thread.m_get_log("C"))

        self.online = {"10.0.0.1", "10.0.0.2"}
        self.do_something(2012, 1, 2, 4, 0, 1)
        self.online = {}
        self.do_something(2012, 1, 2, 5, 0, 1)
        self.assertEqual("+0:05-3:45\n=220", self.ping_thread.m_get_log("S", (2012,1,1)))
        self.assertEqual("+0:05-24:00\n=1435", self.ping_thread.m_get_log("C", (2012,1,1)))
        self.assertEqual("+4:00-5:00\n=60", self.ping_thread.m_get_log("S"))
        self.assertEqual("+0:00-5:00\n=300", self.ping_thread.m_get_log("C"))
        self.online = {"10.0.0.1", "10.0.0.2"}
        self.do_something(2012, 1, 2, 6, 0, 1)
        self.online = {"10.0.0.1"}
        self.do_something(2012, 1, 2, 6, 30, 1)
        self.do_something(2012, 1, 2, 6, 45, 1)
        self.assertEqual("+4:00-5:00\n+6:00\n=105", self.ping_thread.m_get_log("S"))
        self.assertEqual("+0:00-5:00\n+6:00-6:30\n=330", self.ping_thread.m_get_log("C"))

    def test_get_status(self):
        self.assertEqual("", self.ping_thread.get_status())
        self.ping_thread.add_ip("S", "10.0.0.1")
        self.ping_thread.add_ip("C", "10.0.0.2")
        self.ping_thread.add_ip("A", "10.0.0.3")
        self.assertEqual("", self.ping_thread.get_status())
        self.do_something(2012, 1, 1, 0, 0, 1)
        self.online = {"10.0.0.1"}
        self.do_something(2012, 1, 1, 0, 1, 1)
        self.do_something(2012, 1, 1, 0, 2, 1)
        self.online = {"10.0.0.1", "10.0.0.2"}
        self.do_something(2012, 1, 1, 0, 3, 1)
        self.do_something(2012, 1, 1, 0, 4, 1)
        self.assertEqual("S 3\nC 1", self.ping_thread.get_status())
        self.online = {"10.0.0.2"}
        self.do_something(2012, 1, 1, 0, 5, 1)
        self.do_something(2012, 1, 1, 0, 6, 1)
        self.assertEqual("(S 1) 4\nC 3", self.ping_thread.get_status())
        self.do_something(2012, 1, 1, 0, 7, 1)
        self.assertEqual("(S 2) 4\nC 4", self.ping_thread.get_status())
        self.do_something(2012, 1, 2, 0, 7, 1)
        self.assertEqual("C 7", self.ping_thread.get_status())

if __name__ == '__main__':
    unittest.main()
