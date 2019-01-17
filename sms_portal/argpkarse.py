#!/usr/bin/env python3

#argument parser optimized for sms usage:
#cmd .a.b equilvalent to cmd -a -b
#cmd .a36.b45 xxx equilvalent to 'cmd -a36 -b45 xxx' 'b' does not accept spaces
#cmd .a36.b45. xxx same as above. 'b' may or may not accept spaces
#cmd .a36.b new file. xxx equilvalent to 'cmd -a36 -b"new file" xxx ['cmd', ('a', 36), (b, 'new file'), 'xxx']
#cmd .a36.bnew file. xxx same as above
#cmd hello .a what is .b1.c2. stuff equilvalent to cmd hello -a what is -b1 -c2 stuff ['hello', ('a',None), 'what', ('b', 1), ('c', 2), 'stuff']

class ArgpKarse:
    def __init__(self):
        pass

    def add_argument(self, name, type):
        pass

    def parse_args(self):
        pass
