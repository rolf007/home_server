#!/usr/bin/env python3

from argpkarse import ArgpKarse
from argpkarse import space_str
import unittest
import time

class TestArgpKarse(unittest.TestCase):

    def setUp(self):
        pass

    def t(self, parser, arglist, kvs, remain):
        args = parser.parse_args(arglist)
        for k, v in kvs.items():
            self.assertEqual(v, args[k])
        self.assertEqual(remain, args.remain)

    def test_str(self):
        parser = ArgpKarse()
        parser.add_argument('.s', type=str, default="greetings")
        self.t(parser, ".shello foo bar", {'s': 'hello'}, "foo bar")
        self.t(parser, ".s hello foo bar", {'s': 'hello'}, "foo bar")
        self.t(parser, ".s. foo bar", {'s': ''}, "foo bar")
        self.t(parser, "foo bar", {'s': 'greetings'}, "foo bar")
        self.t(parser, " foo bar", {'s': 'greetings'}, " foo bar")
        self.t(parser, "foo .sbar", {'s': 'greetings'}, "foo .sbar")
        self.t(parser, ".s hello foo bar", {'s': 'hello'}, "foo bar")
        self.t(parser, ".s  foo bar", {'s': ''}, " foo bar")
        self.t(parser, ".shello. foo bar", {'s': 'hello'}, "foo bar")
        self.t(parser, ".s hello. foo bar", {'s': 'hello'}, "foo bar")
        self.t(parser, ".s . foo bar", {'s': ''}, "foo bar")
        self.t(parser, ".s  . foo bar", {'s': ''}, " . foo bar")
        self.t(parser, ".s hello", {'s': 'hello'}, "")
        self.t(parser, ".shello", {'s': 'hello'}, "")
        self.t(parser, ".s hello.", {'s': 'hello'}, "")
        self.t(parser, ".shello.", {'s': 'hello'}, "")

    def test_space_str(self):
        parser = ArgpKarse()
        parser.add_argument('.s', type=space_str, default="greetings")
        self.t(parser, ".shello world", {'s': 'hello world'}, "")
        self.t(parser, ".s hello world", {'s': 'hello world'}, "")
        self.t(parser, ".s. foo bar", {'s': ''}, "foo bar")
        self.t(parser, "foo bar", {'s': 'greetings'}, "foo bar")
        self.t(parser, " foo bar", {'s': 'greetings'}, " foo bar")
        self.t(parser, "foo .sbar", {'s': 'greetings'}, "foo .sbar")
        self.t(parser, ".s  hello", {'s': ' hello'}, "")
        self.t(parser, ".shello. foo bar", {'s': 'hello'}, "foo bar")
        self.t(parser, ".s hello. foo bar", {'s': 'hello'}, "foo bar")
        self.t(parser, ".s . foo bar", {'s': ''}, "foo bar")
        self.t(parser, ".s  . foo bar", {'s': ' '}, "foo bar")
        self.t(parser, ".s hello", {'s': 'hello'}, "")
        self.t(parser, ".shello", {'s': 'hello'}, "")
        self.t(parser, ".s hello.", {'s': 'hello'}, "")
        self.t(parser, ".shello.", {'s': 'hello'}, "")

if __name__ == '__main__':
    unittest.main()
