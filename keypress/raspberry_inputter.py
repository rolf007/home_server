from keypress_runner import KeyPressRunner
import time
#from gpiozero import LED, Button
import pygame
import sys


class RaspberryInputter():
    def __init__(self):
        self.running = True
        self.runner = KeyPressRunner()
        self.depressed = ""

    def set_key_press(self, key_press):
        self.runner.set_key_press(key_press)

    def read_NAD_buttons(self):
        return self.depressed
    
    def click_NAD_button(self, n):
        print("clicking '%s'" % n)


    def main_loop(self):
        old_buttons = ""
        while self.running:
            ln = sys.stdin.readlines()
            if ln:
                #print("foo: '%s'" % ln)
                self.depressed = ln[0][:-1]
            buttons = self.read_NAD_buttons()
            if buttons != old_buttons:
                if '1' in buttons and '1' not in old_buttons:
                    self.runner.key_input('A', True)
                if '1' in old_buttons and '1' not in buttons:
                    self.runner.key_input('a', True)
                if '2' in buttons and '2' not in old_buttons:
                    self.runner.key_input('B', True)
                if '2' in old_buttons and '2' not in buttons:
                    self.runner.key_input('b', True)
                print("'%s'" % buttons)
                old_buttons = buttons
            time.sleep(0.1)

    def shut_down(self):
        self.runner.shut_down()

