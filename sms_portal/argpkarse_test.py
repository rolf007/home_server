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

    def test_int(self):
        parser = ArgpKarse()
        parser.add_argument('.i', type=int, default=42)
        self.t(parser, ".i12 world", {'i': 12}, "world")
        self.t(parser, ".i-12 world", {'i': -12}, "world")
        self.t(parser, ".i 12 world", {'i': 12}, "world")
        self.t(parser, ".i 12  world", {'i': 12}, " world")
        self.t(parser, ".i  12 world", {'i': 1}, " 12 world")
        self.t(parser, "world", {'i': 42}, "world")
        self.t(parser, " world .i16.", {'i': 42}, " world .i16.")
        self.t(parser, ".i world", {'i': 1}, "world")
        self.t(parser, ".i. world", {'i': 1}, "world")
        self.t(parser, ".i25world", {'i': 25}, "world")
        self.t(parser, ".i25. world", {'i': 25}, "world")

    def test_bool(self):
        parser = ArgpKarse()
        parser.add_argument('.t', type=bool, default=True)
        parser.add_argument('.f', type=bool, default=False)
        self.t(parser, "world", {'t': True, 'f':False}, "world")
        self.t(parser, ".f world", {'t': True, 'f':True}, "world")
        self.t(parser, ".f1.t0 world", {'t': False, 'f':True}, "world")


if __name__ == '__main__':
    unittest.main()
