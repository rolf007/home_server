import os
import time
import sys
from keypress_runner import KeyPressRunner
from enum import Enum

import RPi.GPIO as gpio

home_server_root = os.path.split(sys.path[0])[0]
sys.path.append(os.path.join(home_server_root, "utils"))
from timer import Timer

DIO = 23 # blue
LATCH = 17 # white
CLK = 27 # brown
LOAD = 22 # purple

class RaspberryInputter():
    def __init__(self):
        self.runner = KeyPressRunner()
        self.depressed = ""
        gpio.setmode(gpio.BCM)

        gpio.setup(DIO,gpio.OUT)
        gpio.setup(LATCH,gpio.OUT)
        gpio.setup(CLK,gpio.OUT)
        gpio.setup(LOAD,gpio.OUT)

        gpio.output(LOAD,1)
        gpio.output(LATCH,0)
        gpio.output(CLK,0)
        self.old_butts = (0,0,0,0,0,0,0,0)
        self.timer = Timer(0.02, self.main_loop)

    def send_bit(self, b):
        time.sleep(0.01)
        gpio.output(DIO,b)
        time.sleep(0.01)
        gpio.output(CLK,1)
        time.sleep(0.01)
        gpio.output(CLK,0)
        time.sleep(0.01)

    class NadButton(Enum):
        DISC = 0
        TUNER = 1
        CD = 2
        MP = 3
        TAPE_MONITOR = 4
        VIDEO = 5
        AUX = 6
        TONE_DEFEAT = 7

    def push_NAD_button(self, n):
        gpio.setup(DIO,gpio.OUT)
        for butt in self.NadButton:
            if butt.value == n:
                self.send_bit(1)
            else:
                self.send_bit(0)

        time.sleep(0.01)
        gpio.output(LATCH,0)
        time.sleep(0.01)
        gpio.output(LATCH,1)
        time.sleep(0.01)

        for butt in self.NadButton:
            self.send_bit(0)

        time.sleep(0.01)
        gpio.output(LATCH,0)
        time.sleep(0.01)
        gpio.output(LATCH,1)
        time.sleep(0.01)

    def receive_bit(self):
        b = gpio.input(DIO)
        gpio.output(CLK,0)
        gpio.output(CLK,1)
        return b

    def pop_NAD_button(self):
        gpio.setup(DIO,gpio.IN)
        gpio.output(CLK,1)
        gpio.output(LOAD,0)
        time.sleep(0.01)
        gpio.output(LOAD,1)

        b0 = self.receive_bit() # TONE DEFEAT
        b1 = self.receive_bit() # TAPE MONITOR
        b2 = self.receive_bit() # VIDEO
        b3 = self.receive_bit() # AUX
        b4 = self.receive_bit() # DISC
        b5 = self.receive_bit() # TUNER
        b6 = self.receive_bit() # CD
        b7 = self.receive_bit() # MP

        #print("TD %d, TM %d, VI %d, AU %d, DI %d, TU %d, CD %d, MP %d" %(b0,b1,b2,b3,b4,b5,b6,b7))
        return (b7, b6, b5, b4, b3, b2, b1, b0)

    def set_key_press(self, key_press):
        self.runner.set_key_press(key_press)

    def read_NAD_buttons(self):
        return self.depressed
    
    def click_NAD_button(self, n):
        print("clicking '%s'" % n)
        self.push_NAD_button(n)


    async def main_loop(self):
        butts = self.pop_NAD_button()
        if butts != self.old_butts:
            if butts[0] and not self.old_butts[0]: self.runner.key_input('A', True)
            if not butts[0] and self.old_butts[0]: self.runner.key_input('a', False)
            if butts[1] and not self.old_butts[1]: self.runner.key_input('B', True)
            if not butts[1] and self.old_butts[1]: self.runner.key_input('b', False)
            if butts[2] and not self.old_butts[2]: self.runner.key_input('C', True)
            if not butts[2] and self.old_butts[2]: self.runner.key_input('c', False)
            if butts[3] and not self.old_butts[3]: self.runner.key_input('D', True)
            if not butts[3] and self.old_butts[3]: self.runner.key_input('d', False)
            if butts[4] and not self.old_butts[4]: self.runner.key_input('E', True)
            if not butts[4] and self.old_butts[4]: self.runner.key_input('e', False)
            if butts[5] and not self.old_butts[5]: self.runner.key_input('F', True)
            if not butts[5] and self.old_butts[5]: self.runner.key_input('f', False)
            if butts[6] and not self.old_butts[6]: self.runner.key_input('G', True)
            if not butts[6] and self.old_butts[6]: self.runner.key_input('g', False)
            if butts[7] and not self.old_butts[7]: self.runner.key_input('H', True)
            if not butts[7] and self.old_butts[7]: self.runner.key_input('h', False)
            #print(butts)
        self.old_butts = butts

    def shut_down(self):
        self.runner.shut_down()

