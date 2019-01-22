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


class space_str:
    pass

class Args(dict):
    __getattr__= dict.__getitem__

class State(Enum):
    init = 0
    found_dot = 1
    found_dotdot = 2
    parse_value = 3

class ArgpKarse:
    class Parse:
        def __init__(self, empty, extra_space):
            self.extra_space = extra_space
            self.value = None
            self.empty = empty
        def parseSpace(self):
            if self.extra_space == False and self.value == None:
                self.extra_space = True
                return None
            else:
                if self.extra_space and self.value == None:
                    return 0
                else:
                    return 1
        def finish(self):
            if self.value == None:
                return self.empty
            return self.value

    class ParseBool(Parse):
        def __init__(self, empty, extra_space):
            if empty == None:
                empty = True
            super(ArgpKarse.ParseBool, self).__init__(empty, extra_space)
        def isLegal(self, c):
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
        def __init__(self, empty, extra_space):
            if empty == None:
                empty = 1
            super(ArgpKarse.ParseInt, self).__init__(empty, extra_space)
            self.sign = 1
        def isLegal(self, c):
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
        def __init__(self, empty, extra_space):
            if empty == None:
                empty = ""
            super(ArgpKarse.ParseStr, self).__init__(empty, extra_space)
        def isLegal(self, c):
            if c != ' ':
                if self.value == None:
                    self.value = ""
                self.value = self.value + c
                return True
            return False


    class ParseSpaceStr(Parse):
        def __init__(self, empty, extra_space):
            if empty == None:
                empty = ""
            super(ArgpKarse.ParseSpaceStr, self).__init__(empty, extra_space)
        def isLegal(self, c):
            if c == ' ' and self.extra_space == False and self.value == None:
                return False
            if self.value == None:
                self.value = ""
            self.value = self.value + c
            return True

    def __init__(self):
        self.arg_name_list = {}

    def add_argument(self, name, type=bool, default=None, required=False, empty=None):
        # where type is [str|int|bool|space_str]
        if len(name) < 2:
            raise Exception("arg name too short")
        if name[0] != '.':
            raise Exception("arg name must start with '.'")
        if name[1] == '.':
            if len(name) < 3:
                raise Exception("missing arg name after '..'")
            else:
                self.arg_name_list[name[2:]] = {'type': type, "default": default, "required": required, "empty": empty}
        else:
            if len(name) != 2:
                raise Exception("arg name after '.' must be one letter")
            self.arg_name_list[name[1]] = {'type': type, "default": default, "required": required, "empty": empty}

    def foo(self, arg_name, extra_space):
        if arg_name not in self.arg_name_list:
            raise Exception("unknwon arg name: '%s'" % arg_name)
        arg = self.arg_name_list[arg_name]
        if arg["type"] == bool:
            state = State.parse_value
            istate = ArgpKarse.ParseBool(arg["empty"], extra_space)
        elif arg["type"] == int:
            state = State.parse_value
            istate = ArgpKarse.ParseInt(arg["empty"], extra_space)
        elif arg["type"] == str:
            state = State.parse_value
            istate = ArgpKarse.ParseStr(arg["empty"], extra_space)
        elif arg["type"] == space_str:
            state = State.parse_value
            istate = ArgpKarse.ParseSpaceStr(arg["empty"], extra_space)
        else:
            raise Exception("found unknown type")
        return state, istate

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
                    arg_name = s[i]
                    state, istate = self.foo(arg_name, False)
            elif state == State.found_dotdot:
                if c == None:
                    break
                elif c == '.':
                    arg_name = dotdot_name
                    state, istate = self.foo(dotdot_name, True)
                    args[arg_name] = istate.finish()
                    state = State.found_dot
                elif c == ' ':
                    arg_name = dotdot_name
                    state, istate = self.foo(dotdot_name, True)
                else:
                    dotdot_name += c
            elif state == State.parse_value:
                if c == None:
                    args[arg_name] = istate.finish()
                    break
                elif c == '.':
                    args[arg_name] = istate.finish()
                    state = State.found_dot
                elif istate.isLegal(c):
                    pass
                elif c == ' ':
                    e = istate.parseSpace()
                    if e != None:
                        i = i + e - 1
                        args[arg_name] = istate.finish()
                        state = State.init
                else:
                    args[arg_name] = istate.finish()
                    break
        args.remain = s[i:]

        return args
