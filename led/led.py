#!/usr/bin/env python3

import os
import sys
import threading
import time

home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])
sys.path.append(os.path.join(home_server_root, "comm"))
sys.path.append(os.path.join(home_server_root, "logger"))
from comm import Comm
from logger import Logger

class LedController():
    class Led():
        def __init__(self):
            self.anim = [(0,(0,0,0,0,0))]
            self.i = 0
            self.repeat_point = 0
            self.repeat_count = 0
            self.now = (0,0,0,0,0)
            self.duration = 0
            self.total_duration = 0
            self.time = 0
            self.src = (0,0,0,0,0)
            self.dst = (0,0,0,0,0)
            self.running = False

        def set_anim(self, anim):
            self.anim = anim
            self.i = 0
            self.cmd(0)

        def next_step(self, overtime):
            self.i += 1
            if len(self.anim) > self.i:
                self.cmd(overtime)
            else:
                self.running = False

        def mix(self):
            frac = self.time / self.duration
            frac = max(0.0, min(frac, 1.0))
            power = int(self.src[0]*(1-frac) + self.dst[0]*(frac))
            red = int(self.src[1]*(1-frac) + self.dst[1]*(frac))
            green = int(self.src[2]*(1-frac) + self.dst[2]*(frac))
            blue = int(self.src[3]*(1-frac) + self.dst[3]*(frac))
            alpha = int(self.src[4]*(1-frac) + self.dst[4]*(frac))
            self.now = (power,red,green,blue,alpha)

        def cmd(self, overtime):
            cmd = self.anim[self.i][0]
            if cmd == "set":
                self.duration = 0
                self.time = overtime
                self.now = self.anim[self.i][1]
                self.next_step(overtime)
                self.running = True
            elif cmd == "fade":
                self.time = overtime
                self.duration = self.anim[self.i][1]
                self.total_duration = self.anim[self.i][3]
                self.src = self.now
                self.dst = self.anim[self.i][2]
                self.running = True
                self.mix()
            elif cmd == "wait":
                self.time = overtime
                self.duration = self.anim[self.i][1]
                self.total_duration = self.anim[self.i][1]
                self.running = True
            elif cmd == "repeat":
                self.repeat_point = self.i
                self.repeat_count = self.anim[self.i][1]
                self.next_step(overtime)
            elif cmd == "loop":
                if self.repeat_count == 0:
                    self.i = self.repeat_point
                elif self.repeat_count > 1:
                    self.repeat_count -= 1
                    self.i = self.repeat_point
                self.next_step(overtime)
            elif cmd == "setanim":
                led = self.anim[self.i][1]
                anim = self.anim[self.i][2]
                led.set_anim(anim)
                self.next_step(overtime)
            else:
                self.running = False

        def update(self, dt):
            if not self.running:
                return
            self.time += dt
            if self.duration != 0:
                self.mix()
            else:
                self.running = False
            if self.time >= self.total_duration:
                self.next_step(self.time - self.total_duration)



    def __init__(self, dt, host_mode):
        self.logger = Logger("led")
        self.logger.log("Started leds")
        self.comm = Comm(5008, "led", {"set": self.set_leds, }, self.logger)
        self.startup_timer = None
        self.num_leds = 8
        self.num_layers = 3
        #self.leds = [self.Led() for i in range(self.num_leds)]
        self.leds = [[self.Led() for i in range(self.num_layers)] for i in range(self.num_leds)]
        print(self.leds[7][2])
        self.meta_led = self.Led()
        self.dt = dt

        self.set_leds({"anim": ["mp"]})
        self.set_leds({"anim": ["knightrider"]})

    def timer_func(self):
        self.startup_timer = None
        running = False
        self.meta_led.update(self.dt)
        running = self.meta_led.running
        for layer in range(self.num_layers):
            sys.stdout.write(" "* layer)
            for led in range(self.num_leds):
                self.leds[led][layer].update(self.dt)
#                sys.stdout.write("(%03d %03d %03d) " % (self.leds[led][layer].now[1], self.leds[led][layer].now[2], self.leds[led][layer].now[3]))
                running = running or self.leds[led][layer].running
#            sys.stdout.write("\n")

        sys.stdout.write("=")
        for led in range(self.num_leds):
            rA = self.leds[led][0].now[1]
            gA = self.leds[led][0].now[2]
            bA = self.leds[led][0].now[3]
            aA = self.leds[led][0].now[4]
            for layer in range(self.num_layers-1):
                rB = self.leds[led][layer+1].now[1]
                gB = self.leds[led][layer+1].now[2]
                bB = self.leds[led][layer+1].now[3]
                aB = self.leds[led][layer+1].now[4]
                rA = (rB * aB / 255) + (rA * aA * (255 - aB) / (255*255))
                gA = (gB * aB / 255) + (gA * aA * (255 - aB) / (255*255))
                bA = (bB * aB / 255) + (bA * aA * (255 - aB) / (255*255))
                aA = aB + (aA * (255 - aB) / 255)
            sys.stdout.write("(%03d %03d %03d) " % (rA, gA, bA))
        sys.stdout.write("\n")
        #sys.stdout.write("\n")

        if running:
            self.startup_timer = threading.Timer(self.dt, self.timer_func)
            self.startup_timer.start()

    # http://127.0.0.1:5008/set?anim=mp
    def set_leds(self, params):
        if "anim" not in params:
            return (404, "function 'set' requires 'anim'")
        anim = params["anim"][0]
        if anim == "mp":
            self.leds[0][0].set_anim([("set",(10,0,0,255,255)) ])
            self.leds[1][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[2][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[3][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[4][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[5][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[6][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[7][0].set_anim([("set",(0,0,0,0,255))])
        if anim == "cd":
            self.leds[0][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[1][0].set_anim([("set",(10,0,0,255,255)) ])
            self.leds[2][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[3][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[4][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[5][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[6][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[7][0].set_anim([("set",(0,0,0,0,255))])

        if anim == "foo":
            white = (10,255,255,255,255)
            green = (10,0,255,0,255)
            off = (0,0,0,0,255)
            self.leds[1][0].set_anim([("fade", 1,white,1), ("repeat",2), ("fade", 1,green,1), ("fade", 1, off,1), ("loop",) ])

        if anim == "knightrider":
            period = 1.35
            t = 0.6
            d = period/((self.num_leds-1)*2)
            on = (10,255,0,0,255)
            off = (0,255,0,0,0)
            self.meta_led.set_anim([("repeat", 1),
                                    ("setanim", self.leds[0][1], [("set",on), ("fade", t, off, t)]), ("wait", 1*d),
                                    ("setanim", self.leds[1][1], [("set",on), ("fade", t, off, t)]), ("wait", 1*d),
                                    ("setanim", self.leds[2][1], [("set",on), ("fade", t, off, t)]), ("wait", 1*d),
                                    ("setanim", self.leds[3][1], [("set",on), ("fade", t, off, t)]), ("wait", 1*d),
                                    ("setanim", self.leds[4][1], [("set",on), ("fade", t, off, t)]), ("wait", 1*d),
                                    ("setanim", self.leds[5][1], [("set",on), ("fade", t, off, t)]), ("wait", 1*d),
                                    ("setanim", self.leds[6][1], [("set",on), ("fade", t, off, t)]), ("wait", 1*d),
                                    ("setanim", self.leds[7][1], [("set",on), ("fade", t, off, t)]), ("wait", 1*d),
                                    ("setanim", self.leds[6][1], [("set",on), ("fade", t, off, t)]), ("wait", 1*d),
                                    ("setanim", self.leds[5][1], [("set",on), ("fade", t, off, t)]), ("wait", 1*d),
                                    ("setanim", self.leds[4][1], [("set",on), ("fade", t, off, t)]), ("wait", 1*d),
                                    ("setanim", self.leds[3][1], [("set",on), ("fade", t, off, t)]), ("wait", 1*d),
                                    ("setanim", self.leds[2][1], [("set",on), ("fade", t, off, t)]), ("wait", 1*d),
                                    ("setanim", self.leds[1][1], [("set",on), ("fade", t, off, t)]), ("wait", 1*d),
                                    ("loop",),
                                    ("setanim", self.leds[0][1], [("set",on), ("fade", t, off, t)]), ("wait", 1*d),])

        running = self.meta_led.running
        for layer in range(self.num_layers):
            for led in range(self.num_leds):
                running = running or self.leds[led][layer].running
        if running and self.startup_timer == None:
            self.startup_timer = threading.Timer(self.dt, self.timer_func)
            self.startup_timer.start()

        return (200, "%s" % "Led ok!")

    def shut_down(self):
        if self.startup_timer != None:
            self.startup_timer.cancel()
        self.comm.shut_down()

if __name__ == '__main__':
    try:
        import RPi.GPIO as gpio
        host_mode = False
    except (ImportError, RuntimeError):
        host_mode = True
    led_controller = LedController(0.01, host_mode)
    try:
        while True:
            time.sleep(2.0)
    except KeyboardInterrupt:
        pass
    led_controller.shut_down()
