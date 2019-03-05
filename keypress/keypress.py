#!/usr/bin/env python3

import copy
import itertools

#epsilon state
class EState:
    def __init__(self):
        self.estates = []

    def input(self, x):
        if x is None:
            if self.estates == []:
                return [self]
            return self.estates
        return []

#callback state
class CState:
    def __init__(self, next_state, l):
        self.next_state = next_state
        self.l = l

    def input(self, x):
        if x is None:
            self.l()
            return [self.next_state]
        return []

#char state
class State:
    def __init__(self, char, next_state):
        self.char = char
        self.next_state = next_state

    def input(self, char):
        if char is None:
            return [self]
        if type(char) is not str:
            return []
        if char == self.char:
            return [self.next_state]
        else:
            return []

#time state
class TState:
    def __init__(self, min_time, max_time, next_state):
        self.min_time = min_time
        self.max_time = max_time
        self.next_state = next_state

    def input(self, time):
        if time is None:
            return [self]
        if type(time) is str:
            return []
        if time < self.min_time:
            return [self]
        if self.min_time <= time and time < self.max_time:
            return [self.next_state]
        else:
            return []

#any time state
class AState:
    def __init__(self, next_state):
        self.next_state = next_state

    def input(self, time):
        if time is None:
            return [self, self.next_state]
        if type(time) is str:
            return []
        return [self, self.next_state]

class Expr:
    def __init__(self, q, f):
        self.q = q
        self.f = f


class KeyPress:
    def __init__(self, expr):
        self.start_state = expr.q
        self.end_state = expr.f
        self.reset()

    def reset(self):
        self.states = [self.start_state]

    def status(self):
        if self.end_state in self.states:
            return "match"
        if self.states == []:
            return "failed"
        return "in progress"

    def process_inputs(self, chars):
        for char in chars:
            self.process_input(char)

    def process_input(self, char):
        self.resolve_estates()
        new_states = []
        for state in self.states:
            new_states += state.input(char)
        self.states = new_states
        self.resolve_estates()
        times = set()
        chars = set()
        for state in self.states:
            if isinstance(state, TState):
                times.update([state.min_time, state.max_time])
            if isinstance(state, State):
                chars.update([state.char])
        print("chars = %s" % chars)
        return times

    def resolve_estates(self):
        self.states = list(set(self.states)) # remove duplicates
        new_states = []
        while True:
            new_states = []
            for state in self.states:
                x = state.input(None)
                new_states += x
            if list(set(new_states)) == list(set(self.states)):
                self.states = new_states
                break
            self.states = new_states

    def mkEmpty():
        f = EState()
        q = EState()
        q.estates = [f]
        return Expr(q, f)

    def mkSymbol(char):
        f = EState()
        q = State(char, f)
        return Expr(q, f)

    def mkCall(l):
        f = EState()
        q = CState(f, l)
        return Expr(q, f)

    def mkTime(min_time, max_time):
        f = EState()
        q = TState(min_time, max_time, f)
        return Expr(q, f)

    def mkAnyTime():
        f = EState()
        q = AState(f)
        return Expr(q, f)

    def mkCat(exprs):
        f = EState()
        q = exprs[0].q
        for i in range(0, len(exprs)-1):
            exprs[i].f.estates.append(exprs[i+1].q)
        exprs[len(exprs)-1].f.estates.append(f)
        return Expr(q, f)

    def mkUnion(exprs):
        f = EState()
        q = EState()
        for expr in exprs:
            q.estates.append(expr.q)
            expr.f.estates = [f]
        return Expr(q, f)

    def mkStar(expr):
        f = EState()
        q = EState()
        expr.f.estates = [expr.q, f]
        q.estates = [expr.q, f]
        return Expr(q, f)

    def mkAnyOrder(exprs):
        f = EState()
        q = EState()
        e = {}

        for i in range(0, len(exprs)):
            for x in itertools.combinations(range(0,len(exprs)), len(exprs)-i-1):
                for n in set(range(0, len(exprs))) - set(x):
                    e[x+(n,)] = copy.deepcopy(exprs[n])
                    for k in set(range(0, len(exprs)))-set(x+(n,)):
                        e[x+(n,)].f.estates.append(e[(tuple(set(x+(n,))) + (k,))].q)
        for x in itertools.combinations(range(0,len(exprs)), len(exprs)-1):
            e[x+tuple(set(range(0, len(exprs))) - set(x),)].f.estates = [f]
        for i in range(0, len(exprs)):
            q.estates.append(e[(i,)].q)
        return Expr(q, f)

    def _mkList(lst, maker):
        if len(lst) > 1:
            e = maker(lst)
        else:
            e = lst[0]
        del lst[:]
        return e

    def compileGroup(s, i, l, d, **kwargs):
        catList = []
        unionList = []
        anyOrderList = []
        while i < l:
            c = s[i]
            if (c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'Z'):
                e = KeyPress.mkSymbol(c)
                catList.append(e)
                i = i + 1
            elif s[i] >= '0' and s[i] <= '9':
                i, min, max = KeyPress.compileTime(s, i, l)
                catList.append(KeyPress.mkTime(min, max))
            elif s[i] == '<':
                i, e = KeyPress.compileCall(s, i+1, l, **kwargs)
                catList.append(e)
            elif s[i] == '.':
                catList.append(KeyPress.mkAnyTime())
                i = i + 1
            elif c == '(':
                i, e = KeyPress.compileGroup(s, i+1, l, d+1, **kwargs)
                catList.append(e)
            elif c == '{' or c == '*' or c == '+' or c == '?':
                if c == '{':
                    i, min,max = KeyPress.compileCount(s, i+1, l)
                elif c == '*':
                    min,max=0,0
                    i = i + 1
                elif c == '+':
                    min,max=1,0
                    i = i + 1
                elif c == '?':
                    min,max=0,1
                    i = i + 1
                last = catList[-1]
                catList = catList[:-1]
                for j in range(min):
                    catList.append(copy.deepcopy(last))
                if max == 0:
                    e = KeyPress.mkStar(last)
                    catList.append(e)
                else:
                    for j in range(max-min):
                        empty = KeyPress.mkEmpty()
                        catList.append(KeyPress.mkUnion([copy.deepcopy(last), empty]))
            elif c == '|':
                e = KeyPress._mkList(catList, KeyPress.mkCat)
                unionList.append(e)
                i = i + 1
            elif c == '&':
                e = KeyPress._mkList(catList, KeyPress.mkCat)
                unionList.append(e)
                e = KeyPress._mkList(unionList, KeyPress.mkUnion)
                anyOrderList.append(e)
                i = i + 1
            elif c == ')':
                if d == 0:
                    print("Unexpected ')' at position %d" % i)
                    return
                else:
                    i = i + 1
                    break
            else:
                print("Unrecognized token '%s' at position '%d'" % (c, i))
                i = i + 1
        e = KeyPress._mkList(catList, KeyPress.mkCat)
        unionList.append(e)
        e = KeyPress._mkList(unionList, KeyPress.mkUnion)
        anyOrderList.append(e)
        e = KeyPress._mkList(anyOrderList, KeyPress.mkAnyOrder)
        return i, e

    def compileCount(s, i, l):
        mode = True
        min = 0
        max = 0
        while i < l:
            c = s[i]
            if (c >= '0' and c <= '9'):
                if mode:
                    min = min*10 + int(c) - int('0')
                else:
                    max = max*10 + int(c) - int('0')
                i = i + 1
            elif c == ',':
                mode = False
                i = i + 1
            elif c == '}':
                if mode:
                    max = min
                return i+1, min, max
            else:
                print("Unrecognized token in {} '%s' at position '%d'" % (c, i))
                i = i + 1

    def compileTime(s, i, l):
        mode = True
        min = 0
        max = 0
        while i < l:
            c = s[i]
            if (c >= '0' and c <= '9'):
                if mode:
                    min = min*10 + int(c) - int('0')
                else:
                    max = max*10 + int(c) - int('0')
                i = i + 1
            elif c == '-':
                mode = False
                i = i + 1
            else:
                break
        if mode:
            print("missing '-' in time")
        return i, min, max


    def compileCall(s, i, l, **kwargs):
        label = ""
        while i < l:
            c = s[i]
            if (c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'Z') or (c >= '0' and c <= '9') or c == '_':
                label += c
                i = i + 1
            elif c == '>':
                if label in kwargs:
                    return i+1, KeyPress.mkCall(kwargs[label])
                else:
                    print("Unknown label '%s' at position '%d'" % (label, i))
                    return
            else:
                print("Illegal symbol in label '%s' at position '%d'" % (c, i))
                return


        return i+1, None

    def compile(s, **kwargs):
        # X?     -> (X|)
        # X+     -> XX*
        # X{3}   -> XXX                   The preceding item is matched exactly n times. min = 3, max = 3
        # X{3,}  -> XXXX*                 The preceding item is matched n or more times. min = 3, max = 0
        # X{,5}  -> (X|)(X|)(X|)(X|)(X|)  The preceding item is matched at most m times.  This is a GNU extension. min = 0, max = 5
        # X{3,5} -> XXX(X|)(X|)           The preceding item is matched at least n times, but not more than m times. min = 3, max = 5
        i, e = KeyPress.compileGroup(s, 0, len(s), 0, **kwargs)
        return e

#precedence:
#     Kleene Star/Plus (also finite versions),
#     concatenation,
#     alternative.
# 
# That is: 
# 10?1 is read as 1(0)?1
# and
# 10|01|11 as (10)|(01)|(11).

