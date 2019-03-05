#!/usr/bin/env python3
import sys
from keypress import KeyPress
from pygame_inputter import PyGameInputter
from morse_maker import MorseMaker

#seq0 = KeyPress.compile("Aa1000-3000*Aa<foo>", foo=lambda: print("SUCCES foo"))
#seq1 = KeyPress.compile("Bb1000-3000*Bb<bar>", bar=lambda: print("SUCCES bar"))
#seq2 = KeyPress.compile("BAa<one>Aa<two>Aa<three>b<tripple>", tripple=lambda: print("SUCCES tripple"), one=lambda: print("ONE"), two=lambda: print("TWO"), three=lambda: print("THREE"))
#seq3 = KeyPress.compile("Cc1000-3000<baz>", baz=lambda: print("SUCCES baz"))
#seq4 = KeyPress.compile(".C(.A.a<one>|.B.b<two>|(.A&.B)(.a&.b)<three>)*.c", one=lambda: print("cA"), two=lambda: print("cB"), three=lambda: print("cAB"))
#seq4 = KeyPress.compile(".C(.A1000-3000+a<one>|.A2000-4000+a<two>)*.c", one=lambda: print("one"), two=lambda: print("two"))
#seq4 = KeyPress.compile(".C1000-3000<one>3000-5000<two>5000-7000<three>.c", one=lambda: print("one"), two=lambda: print("two"), three=lambda: print("three"))


class ItTest():
    def __init__(self, inputter):
        self.inputter = inputter
        morse_maker = MorseMaker('C', 'c', 200, 500)
        self.morseAlphbeth = KeyPress.mkUnion(morse_maker.mkAll(lambda c: print("=== %s" % c)) +
                [KeyPress.compile(".A.a<go_to_normal>", go_to_normal = lambda: self.go_normal())]
                )

        self.main_menu = KeyPress.mkUnion([
            KeyPress.compile(".A.C.c.a<go_to_morse>", go_to_morse=lambda: self.go_morse()),
            KeyPress.compile(".A.a<A>", A=lambda: print("A")),
            KeyPress.compile(".B.b<B>", B=lambda: print("B")),
        ])
        self.go_normal()

    def go_morse(self):
        print("going morse")
        self.inputter.set_key_press(KeyPress(self.morseAlphbeth))

    def go_normal(self):
        print("going normal")
        self.inputter.set_key_press(KeyPress(self.main_menu))

    def main_loop(self):
        self.inputter.main_loop()

    def shut_down(self):
        print("ItTest::shut_down")
        self.inputter.shut_down()
        pass


inputter = PyGameInputter()

it_test = ItTest(inputter)
try:
    it_test.main_loop()
except KeyboardInterrupt:
    pass
it_test.shut_down()
