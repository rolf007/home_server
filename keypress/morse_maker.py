from keypress import KeyPress

class MorseMaker:
    def __init__(self, down, up, t0, t1):
        self.down = down
        self.up = up
        self.t0 = t0
        self.t1 = t1

    def mkMorse(self, seq, l):
        s = ""
        i = "."
        for c in seq:
            if c == '.': s += i+self.down+"0-"+str(self.t0)   +"+"+self.up
            if c == '-': s += i+self.down+str(self.t0)+"-1000"+"+"+self.up
            i = "0-500"
        s += str(self.t1)+"-2000<match>"
        return KeyPress.compile(s, match=l)

    def mkAll(self, l):
        return [
            self.mkMorse(".-",   lambda: l("a")),
            self.mkMorse("-...", lambda: l("b")),
            self.mkMorse("-.-.", lambda: l("c")),
            self.mkMorse("-..",  lambda: l("d")),
            self.mkMorse(".",    lambda: l("e")),
            self.mkMorse("..-.", lambda: l("f")),
            self.mkMorse("--.",  lambda: l("g")),
            self.mkMorse("....", lambda: l("h")),
            self.mkMorse("..",   lambda: l("i")),
            self.mkMorse(".---", lambda: l("j")),
            self.mkMorse("-.-",  lambda: l("k")),
            self.mkMorse(".-..", lambda: l("l")),
            self.mkMorse("--",   lambda: l("m")),
            self.mkMorse("-.",   lambda: l("n")),
            self.mkMorse("---",  lambda: l("o")),
            self.mkMorse(".--.", lambda: l("p")),
            self.mkMorse("--.-", lambda: l("q")),
            self.mkMorse(".-.",  lambda: l("r")),
            self.mkMorse("...",  lambda: l("s")),
            self.mkMorse("-",    lambda: l("t")),
            self.mkMorse("..-",  lambda: l("u")),
            self.mkMorse("...-", lambda: l("v")),
            self.mkMorse(".--",  lambda: l("w")),
            self.mkMorse("-..-", lambda: l("x")),
            self.mkMorse("-.--", lambda: l("y")),
            self.mkMorse("--..", lambda: l("z")),
        ]

