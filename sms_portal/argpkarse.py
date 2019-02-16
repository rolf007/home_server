#!/usr/bin/env python3

from enum import Enum

#argument parser optimized for sms usage:
#cmd .a.b equilvalent to cmd -a -b
#cmd .a36.b45 xxx equilvalent to 'cmd -a36 -b45 xxx' 'b' does not accept spaces
#cmd .a36.b45. xxx same as above. 'b' may or may not accept spaces
#cmd .a36.b new file. xxx equilvalent to 'cmd -a36 -b"new file" xxx [('a', 36), (b, 'new file'), 'xxx']
#cmd .a36.bnew file. xxx same as above
#cmd .a.b1.c2. stuff equilvalent to cmd hello -a what is -b1 -c2 stuff ['hello', ('a',None), 'what', ('b', 1), ('c', 2), 'stuff']
#cmd ..pay give money
#cmd ..pay. give money

class ArgpKarseError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class Args(dict):
    __getattr__= dict.__getitem__

class State(Enum):
    init = 0
    found_dot = 1
    found_dotdot = 2
    parse_value = 3

class ArgpKarse:
    class Parse:
        def __init__(self, empty):
            self.value = None
            self.empty = empty
        def finish(self):
            if self.value == None:
                return self.empty
            return self.value

    class ParseBool(Parse):
        def __init__(self, empty):
            if empty == None:
                empty = True
            super(ArgpKarse.ParseBool, self).__init__(empty)
        def parseChar(self, c):
            if self.value == None:
                if c == '0':
                    self.value = False
                elif c == '1':
                    self.value = True
                else:
                    return False
                return True
            return False

    class ParseInt(Parse):
        def __init__(self, empty):
            if empty == None:
                empty = 1
            super(ArgpKarse.ParseInt, self).__init__(empty)
            self.sign = 1
        def parseChar(self, c):
            if c == '-':
                if self.sign == 1 and self.value == None:
                    self.sign = -1
                    return True
            elif c in ['0','1','2','3','4','5','6','7','8','9']:
                if self.value == None:
                    self.value = 0
                self.value = self.value*10
                if self.value != 0 and self.sign == -1:
                    self.value *= self.sign
                    self.sign = 1
                if self.value < 0:
                    self.value -= ord(c) - ord('0')
                else:
                    self.value += ord(c) - ord('0')
                return True
            return False

    class ParseStr(Parse):
        def __init__(self, empty):
            if empty == None:
                empty = ""
            self.leading_space = False
            super(ArgpKarse.ParseStr, self).__init__(empty)
        def parseChar(self, c):
            if c == '.':
                return False
            if c == ' ' and not self.leading_space:
                if self.value == None:
                    self.leading_space = True
                    return True
                else:
                    return False
            if self.value == None:
                self.value = ""
            self.value = self.value + c
            return True


    def __init__(self):
        self.arg_name_list = {}
        self.long_short_name = {}

    def add_argument(self, name, type=bool, default=None, required=False, empty=None):
        # where type is [str|int|bool] and name is [.a|..arg|.a..arg]
        value_parser_info = {'type': type, "default": default, "required": required, "empty": empty}
        if len(name) < 2:
            raise ArgpKarseError("arg name too short")
        if name[0] != '.':
            raise ArgpKarseError("arg name must start with '.'")
        if name[1] == '.':
            if len(name) < 3:
                raise ArgpKarseError("missing arg name after '..'")
            else:
                self.arg_name_list[name[2:]] = value_parser_info
        else:
            if len(name) == 2:
                self.arg_name_list[name[1]] = value_parser_info
            elif len(name) > 2:
                if len(name) < 6 or name[2] != '.' or name[3] != '.': # ".a..ar"
                    raise ArgpKarseError("arg name after '.' must be one letter or like this: '.a..arg'")
                self.arg_name_list[name[4:]] = value_parser_info
                self.long_short_name[name[1]] = name[4:]

    def start_parsing_value(self, arg_name, space):
        if arg_name in self.long_short_name:
            arg_name = self.long_short_name[arg_name]
        if arg_name not in self.arg_name_list:
            raise ArgpKarseError("unknwon arg name: '%s'" % arg_name)
        arg = self.arg_name_list[arg_name]
        if arg["type"] == bool:
            istate = ArgpKarse.ParseBool(arg["empty"])
        elif arg["type"] == int:
            istate = ArgpKarse.ParseInt(arg["empty"])
        elif arg["type"] == str:
            istate = ArgpKarse.ParseStr(arg["empty"])
            if space:
                istate.parseChar(' ')
        else:
            raise ArgpKarseError("found unknown type")
        return arg_name, istate

    def parse_args(self, s):
        args = Args()
        arg = None
        for a, meta in self.arg_name_list.items():
            args[a] = meta["default"]
        args["remain"] = ""
        state = State.init
        l = len(s)+1
        i = -1
        while i < l:
            i = i + 1
            c = s[i] if i < len(s) else None
            if state == State.init:
                if c == None:
                    break
                elif c == '.':
                    state = State.found_dot
                else:
                    break
            elif state == State.found_dot:
                if c == None:
                    break
                elif c == '.':
                    dotdot_name = ""
                    state = State.found_dotdot
                elif c == ' ':
                    i = i + 1
                    break
                else:
                    arg_name, istate = self.start_parsing_value(s[i], False)
                    state = State.parse_value
            elif state == State.found_dotdot:
                if c == None:
                    break
                elif c == '.':
                    if dotdot_name == "":
                        break
                    arg_name, istate = self.start_parsing_value(dotdot_name, False)
                    args[arg_name] = istate.finish()
                    state = State.found_dot
                elif c == ' ':
                    if dotdot_name == "":
                        i = i + 1
                        break
                    arg_name, istate = self.start_parsing_value(dotdot_name, True)
                    state = State.parse_value
                else:
                    dotdot_name += c
            elif state == State.parse_value:
                if c == None:
                    args[arg_name] = istate.finish()
                    break
                elif istate.parseChar(c):
                    pass
                elif c == '.':
                    args[arg_name] = istate.finish()
                    state = State.found_dot
                elif c == ' ':
                    i = i + 1
                    args[arg_name] = istate.finish()
                    break
                else:
                    args[arg_name] = istate.finish()
                    break
        args.remain = s[i:]

        return args
