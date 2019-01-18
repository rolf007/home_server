#!/usr/bin/env python3

from enum import Enum

#argument parser optimized for sms usage:
#cmd .a.b equilvalent to cmd -a -b
#cmd .a36.b45 xxx equilvalent to 'cmd -a36 -b45 xxx' 'b' does not accept spaces
#cmd .a36.b45. xxx same as above. 'b' may or may not accept spaces
#cmd .a36.b new file. xxx equilvalent to 'cmd -a36 -b"new file" xxx [('a', 36), (b, 'new file'), 'xxx']
#cmd .a36.bnew file. xxx same as above
#cmd .a .b1.c2. stuff equilvalent to cmd hello -a what is -b1 -c2 stuff ['hello', ('a',None), 'what', ('b', 1), ('c', 2), 'stuff']
#cmd ..pay give money
#cmd ..pay. give money

#type bool:
#es .b hello    set b to True
#es .b. hello   set b to True
#es hello       set b to default_missing
#es .b0 hello   set b to False
#es .b0. hello  set b to False
#es .b1 hello   set b to True
#es .b1. hello  set b to True

#type int:
#es .m hello    set m to 1
#es .m. hello   set m to 1
#es hello       set m to default_missing
#es .m3hello    set m to 3
#es .m3 hello   set m to 3
#es .m3. hello  set m to 3

#type: str
#es .s hello world set s to 'hello'
#es .s. hello      set s to ''
#es hello          set s to default_missing
#es .sfoo hello    set s to 'foo'
#es .s foo hello   set s to 'foo'
#es .sfoo. hello   set s to 'foo'
#es .s foo. hello  set s to 'foo'

#type: space_str
#es .s hello       set s to 'hello'
#es .s. hello      set s to ''
#es hello          set s to default_missing
#es .sfoo hello    set s to 'foo hello'
#es .s foo hello   set s to 'foo hello'
#es .sfoo hello.   set s to 'foo hello'
#es .s foo hello.  set s to 'foo hello'
#es .sfoo. hello   set s to 'foo'
#es .s foo. hello  set s to 'foo'
#es .s  foo. hello set s to ' foo'

class space_str:
    pass

class Args(dict):
    __getattr__= dict.__getitem__

class State(Enum):
    init = 0
    found_dot = 1
    found_dotdot = 2
    parse_bool = 3
    parse_int = 4
    parse_str = 5
    parse_space_str = 6

class ArgpKarse:
    def __init__(self):
        self.arg_name_list = {}

    def add_argument(self, name, type=bool, default=None, required=False):
        # where type is [str|int|bool|space_str]
        if len(name) < 2:
            raise Exception("arg name too short")
        if name[0] != '.':
            raise Exception("arg name must start with '.'")
        if name[1] == '.':
            if len(name) < 3:
                raise Exception("missing arg name after '..'")
            else:
                self.arg_name_list[name[2:]] = {'type': type, "default": default, "required": required}
        else:
            if len(name) != 2:
                raise Exception("arg name after '.' must be one letter")
            self.arg_name_list[name[1]] = {'type': type, "default": default, "required": required}

    def parse_args(self, s):
        args = Args()
        arg = None
        for a, meta in self.arg_name_list.items():
            args[a] = meta["default"]
        args["remain"] = ""
        state = State.init
        for i in range(len(s)+1):
            c = s[i] if i < len(s) else None
            print(c)
            if state == State.init:
                if c == None:
                    break
                elif c == '.':
                    state = State.found_dot
                else:
                    args.remain = s[i:]
                    break
            elif state == State.found_dot:
                if c == None:
                    break
                elif c == '.':
                    state = State.found_dotdot
                elif c == ' ':
                    args.remain = s[i+1:]
                    break
                else:
                    arg_name = s[i]
                    if arg_name not in self.arg_name_list:
                        raise Exception("unknwon arg name: '%s'" % arg_name)
                    arg = self.arg_name_list[arg_name]
                    if arg["type"] == bool:
                        state = State.parse_bool
                        value = ""
                        extra_space = False
                    elif arg["type"] == int:
                        state = State.parse_int
                        value = ""
                        extra_space = False
                    elif arg["type"] == str:
                        state = State.parse_str
                        value = ""
                        extra_space = False
                    elif arg["type"] == space_str:
                        state = State.parse_space_str
                        value = ""
                        extra_space = False
                    else:
                        raise Exception("found unknown type")
            elif state == State.found_dotdot:
                pass
            elif state == State.parse_bool:
                pass
            elif state == State.parse_int:
                pass
            elif state == State.parse_str:
                if c == None:
                    args[arg_name] = value
                    break
                elif c == ' ':
                    if extra_space == False and len(value) == 0:
                        extra_space = True
                    else:
                        args[arg_name] = value
                        if extra_space and len(value) == 0:
                            args.remain = s[i:]
                        else:
                            args.remain = s[i+1:]
                        break
                elif c == '.':
                    args[arg_name] = value
                    state = State.found_dot
                else:
                    value = value + c
            elif state == State.parse_space_str:
                if c == None:
                    args[arg_name] = value
                    break
                elif c == ' ':
                    if extra_space == False and len(value) == 0:
                        extra_space = True
                    else:
                        value = value + c
                elif c == '.':
                    args[arg_name] = value
                    state = State.found_dot
                else:
                    value = value + c



        return args
