#!/usr/bin/env python3

from argpkarse import ArgpKarse
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

    def test_bool(self):
        parser = ArgpKarse()
        parser.add_argument('.t', type=bool, default=True)
        parser.add_argument('.f', type=bool, default=False)
        self.t(parser, "world", {'t': True, 'f':False}, "world")
        self.t(parser, ".f world", {'t': True, 'f':True}, "world")
        self.t(parser, ".f1.t0 world", {'t': False, 'f':True}, "world")
        self.t(parser, ".f1.t0world", {'t': False, 'f':True}, "world")
        self.t(parser, ".f1.t0. world", {'t': False, 'f':True}, "world")
        self.t(parser, ".f0.t1 world", {'t': True, 'f':False}, "world")
        self.t(parser, ".t1.f0 world", {'t': True, 'f':False}, "world")
        self.t(parser, ".f1", {'f': True}, "")
        self.t(parser, ".t0", {'t': False}, "")
        self.t(parser, ".f.", {'f': True}, "")

    def test_int(self):
        parser = ArgpKarse()
        parser.add_argument('.i', type=int, default=42)
        self.t(parser, ".i12 world", {'i': 12}, "world")
        self.t(parser, ".i-12 world", {'i': -12}, "world")
        self.t(parser, ".i12  world", {'i': 12}, " world")
        self.t(parser, ".i 12 world", {'i': 1}, "12 world")
        self.t(parser, ".i  12 world", {'i': 1}, " 12 world")
        self.t(parser, "world", {'i': 42}, "world")
        self.t(parser, " world .i16.", {'i': 42}, " world .i16.")
        self.t(parser, ".i world", {'i': 1}, "world")
        self.t(parser, ".i. world", {'i': 1}, "world")
        self.t(parser, ".i25world", {'i': 25}, "world")
        self.t(parser, ".i25 world", {'i': 25}, "world")
        self.t(parser, ".i25. world", {'i': 25}, "world")
        self.t(parser, ".i", {'i': 1}, "")
        self.t(parser, ".i.", {'i': 1}, "")

    def test_str(self):
        parser = ArgpKarse()
        parser.add_argument('.s', type=str, default="greetings")
        self.t(parser, ".shello foo bar", {'s': 'hello'}, "foo bar")
        self.t(parser, ".s hello foo bar", {'s': 'hello foo bar'}, "")
        self.t(parser, ".s. foo bar", {'s': ''}, "foo bar")
        self.t(parser, "foo bar", {'s': 'greetings'}, "foo bar")
        self.t(parser, " foo bar", {'s': 'greetings'}, " foo bar")
        self.t(parser, "foo .sbar", {'s': 'greetings'}, "foo .sbar")
        self.t(parser, ".s  foo bar", {'s': ' foo bar'}, "")
        self.t(parser, ".shello. foo bar", {'s': 'hello'}, "foo bar")
        self.t(parser, ".s hello. foo bar", {'s': 'hello'}, "foo bar")
        self.t(parser, ".s . foo bar", {'s': ''}, "foo bar")
        self.t(parser, ".s  . foo bar", {'s': ' '}, "foo bar")
        self.t(parser, ".s hello", {'s': 'hello'}, "")
        self.t(parser, ".shello", {'s': 'hello'}, "")
        self.t(parser, ".s hello.", {'s': 'hello'}, "")
        self.t(parser, ".shello.", {'s': 'hello'}, "")

    def test_space_str(self):
        parser = ArgpKarse()
        parser.add_argument('.s', type=str, default="greetings")
        self.t(parser, ".shello world", {'s': 'hello'}, "world")
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

    def test_space_str1(self):
        parser = ArgpKarse()
        parser.add_argument('..longname', type=str, default="greetings", empty="blank")
        self.t(parser, "..longname hello world", {'longname': 'hello world'}, "")
        self.t(parser, "..longname hello world. foo", {'longname': 'hello world'}, "foo")
        self.t(parser, "..longname  hello world . foo", {'longname': ' hello world '}, "foo")
        self.t(parser, "..longname. foo", {'longname': 'blank'}, "foo")

    def test_long_name_int(self):
        parser = ArgpKarse()
        parser.add_argument('..long_name_int', type=int, default=10, empty=9)
        self.t(parser, "..long_name_int 12 hello world", {'long_name_int': 12}, "hello world")

    def test_mixed0(self):
        parser = ArgpKarse()
        parser.add_argument('.i', type=int, default=15)
        parser.add_argument('.j', type=int, default=16, empty=7)
        self.t(parser, ".i1000.j2000 hello world", {'i': 1000, 'j':2000}, "hello world")

    def test_mixed(self):
        parser = ArgpKarse()
        parser.add_argument('.b', type=bool, default=False)
        parser.add_argument('.j', type=int, default=18, empty=7)
        parser.add_argument('..pay', type=bool, default=False, empty=True)
        self.t(parser, ".b.j-1000..pay hello world", {'b': True, 'j':-1000, 'pay': True}, "hello world")

    def test_remain(self):
        parser = ArgpKarse()
        parser.add_argument('.b', type=bool, default=False)
        parser.add_argument('.j', type=int, default=18, empty=7)
        self.t(parser, ".. .j hello world", {'b': False, 'j':18}, ".j hello world")
        self.t(parser, ".. hello world", {'b': False, 'j':18}, "hello world")
        self.t(parser, "...j hello world", {'b': False, 'j':18}, ".j hello world")
        self.t(parser, ".b...j hello world", {'b': True, 'j':18}, ".j hello world")

    def test_short_or_long_name(self):
        parser = ArgpKarse()
        parser.add_argument('.j..jar', type=int, default=18, empty=7)
        self.t(parser, ".j12 bing", {'jar':12}, "bing")
        self.t(parser, "..jar 12 bing", {'jar':12}, "bing")

    def test_real_world(self):
        parser = ArgpKarse()
        parser.add_argument('.r..artist', type=str, default=None, empty=None)
        parser.add_argument('.l..album', type=str, default=None, empty=None)
        self.t(parser, "..artist iron maiden..album seventh son. tailgunner", {'artist':'iron maiden', 'album':'seventh son'}, "tailgunner")
        self.t(parser, ".r iron maiden.l seventh son. tailgunner", {'artist':'iron maiden', 'album':'seventh son'}, "tailgunner")
        self.t(parser, ".rmaiden.l seventh son. tailgunner", {'artist':'maiden', 'album':'seventh son'}, "tailgunner")
        self.t(parser, ".rmaiden.lpowerslave tailgunner", {'artist':'maiden', 'album':'powerslave'}, "tailgunner")
        self.t(parser, ".rmaiden.lpowerslave. tailgunner", {'artist':'maiden', 'album':'powerslave'}, "tailgunner")
        self.t(parser, ".rmaiden tailgunner", {'artist':'maiden', 'album':None}, "tailgunner")
        self.t(parser, ".rmetallica ...and justice for all", {'artist':'metallica', 'album':None}, "...and justice for all")

if __name__ == '__main__':
    unittest.main()
