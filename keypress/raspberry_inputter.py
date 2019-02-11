from keypress_runner import KeyPressRunner
import time
import pygame
import sys

import RPi.GPIO as gpio

DIO = 23 # blue
LATCH = 17 # white
CLK = 27 # brown
LOAD = 22 # purple

class RaspberryInputter():
    def __init__(self):
        self.running = True
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

    def send_bit(b):
        time.sleep(0.01)
        gpio.output(DIO,b)
        time.sleep(0.01)
        gpio.output(CLK,1)
        time.sleep(0.01)
        gpio.output(CLK,0)
        time.sleep(0.01)

    def push_NAD_button(n):
        gpio.setup(DIO,gpio.OUT)
        send_bit(0)#DISC
        send_bit(0)#TUNER
        send_bit(0)#CD
        send_bit(0)#MP
        send_bit(1)#TAPE MONITOR
        send_bit(0)#VIDEO
        send_bit(0)#AUX
        send_bit(0)#TONE DEFEAT

        time.sleep(0.01)
        gpio.output(LATCH,0)
        time.sleep(0.01)
        gpio.output(LATCH,1)
        time.sleep(0.01)

        send_bit(0)
        send_bit(0)
        send_bit(0)
        send_bit(0)
        send_bit(0)
        send_bit(0)
        send_bit(0)
        send_bit(0)

        time.sleep(0.01)
        gpio.output(LATCH,0)
        time.sleep(0.01)
        gpio.output(LATCH,1)
        time.sleep(0.01)

    def receive_bit(self):
        b = gpio.input(DIO)
        time.sleep(0.01)
        gpio.output(CLK,0)
        time.sleep(0.01)
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


    def main_loop(self):
        old_butts = (0,0,0,0,0,0,0,0)
        while self.running:
            time.sleep(0.1)
            print("raspberry inputter mainloop")
            butts = self.pop_NAD_button()
            if butts != old_butts:
                if butts[0] and not old_butts[0]: self.runner.key_input('A', True)
                if not butts[0] and old_butts[0]: self.runner.key_input('a', False)
                if butts[1] and not old_butts[1]: self.runner.key_input('B', True)
                if not butts[1] and old_butts[1]: self.runner.key_input('b', False)
                if butts[2] and not old_butts[2]: self.runner.key_input('C', True)
                if not butts[2] and old_butts[2]: self.runner.key_input('c', False)
                if butts[3] and not old_butts[3]: self.runner.key_input('D', True)
                if not butts[3] and old_butts[3]: self.runner.key_input('d', False)
                if butts[4] and not old_butts[4]: self.runner.key_input('E', True)
                if not butts[4] and old_butts[4]: self.runner.key_input('e', False)
                if butts[5] and not old_butts[5]: self.runner.key_input('F', True)
                if not butts[5] and old_butts[5]: self.runner.key_input('f', False)
                print(butts)
            old_butts = butts

    def shut_down(self):
        self.runner.shut_down()

