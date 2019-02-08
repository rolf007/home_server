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
            self.anim = [(0,(0,0,0,0))]
            self.i = 0
            self.now = (0,0,0,0)
            self.duration = 0
            self.time = 0
            self.src = (0,0,0,0)
            self.dst = (0,0,0,0)

        def set_anim(self, anim):
            self.anim = anim
            self.i = 0
            self.duration = anim[0][0]
            self.time = 0
            self.src = self.now
            self.dst = anim[0][1]


    def __init__(self):
        self.logger = Logger("led")
        self.logger.log("Started leds")
        self.comm = Comm(5008, "led", {"set": self.set_leds, }, self.logger)
        self.startup_timer = threading.Timer(1, self.startup)
        self.startup_timer.start()
        self.num_leds = 8
        self.leds = [self.Led(),self.Led(),self.Led(),self.Led(),self.Led(),self.Led(),self.Led(),self.Led()]

        self.led_anim = [(0,(0,0,0,0))]*self.num_leds
        self.led_i = [0]*self.num_leds
        self.led_now = [(0,0,0,0)]*self.num_leds
        self.led_duration = [0]*self.num_leds
        self.led_time = [0]*self.num_leds
        self.led_src = [(0,0,0,0)]*self.num_leds
        self.led_dst = [(0,0,0,0)]*self.num_leds

        self.set_leds({"anim": ["mp"]})
        self.set_leds({"anim": ["foo"]})

    def startup(self):
        dt = 0.1
        for led in range(self.num_leds):
            if self.leds[led].time == 0:
                power = self.leds[led].dst[0]
                blue = self.leds[led].dst[1]
                green = self.leds[led].dst[2]
                red = self.leds[led].dst[3]
            else:
                frac = self.leds[led].time / self.leds[led].duration
                frac = max(0.0, min(frac, 1.0))
                power = int(self.leds[led].src[0]*(1-frac) + self.leds[led].dst[0]*(frac))
                blue = int(self.leds[led].src[1]*(1-frac) + self.leds[led].dst[1]*(frac))
                green = int(self.leds[led].src[2]*(1-frac) + self.leds[led].dst[2]*(frac))
                red = int(self.leds[led].src[3]*(1-frac) + self.leds[led].dst[3]*(frac))
            self.leds[led].now = (power,blue,green,red)
            if self.leds[led].time < self.leds[led].duration:
                self.leds[led].time += dt
            else:
                self.leds[led].i += 1
                if len(self.leds[led].anim) > self.leds[led].i:
                    self.leds[led].time = 0
                    self.leds[led].duration = self.leds[led].anim[self.leds[led].i][0]
                    self.leds[led].src = self.leds[led].now
                    self.leds[led].dst = self.leds[led].anim[self.leds[led].i][1]

        print(self.leds[1].now)
        self.startup_timer = threading.Timer(dt, self.startup)
        self.startup_timer.start()

    def set_led_anim(self, led_num, anim):
        self.leds[led_num].set_anim(anim)

        #self.led_anim[led_num] = anim
        #self.led_i[led_num] = 0
        #self.led_duration[led_num] = anim[0][0]
        #self.led_time[led_num] = 0
        #self.led_src[led_num] = self.led_now[led_num]
        #self.led_dst[led_num] = anim[0][1]
        ##self.led_now[led_num] = anim[0][1]

    # http://127.0.0.1:5004/set?anim=mp
    def set_leds(self, params):
        if "anim" not in params:
            return (404, "function 'set' requires 'anim'")
        anim = params["anim"][0]
        if anim == "mp":
            self.set_led_anim(0, [(0,(10,255,0,0)) ])
            self.set_led_anim(1, [(0,(0,0,0,0))])
            self.set_led_anim(2, [(0,(0,0,0,0))])
            self.set_led_anim(3, [(0,(0,0,0,0))])
            self.set_led_anim(4, [(0,(0,0,0,0))])
            self.set_led_anim(5, [(0,(0,0,0,0))])
            self.set_led_anim(6, [(0,(0,0,0,0))])
            self.set_led_anim(7, [(0,(0,0,0,0))])

        if anim == "foo":
            self.set_led_anim(1, [(5,(10,255,0,0)), (5,(10,0,255,0)), (5, (0,0,0,0)) ])

        return (200, "%s" % "Led ok!")

    def shut_down(self):
        self.startup_timer.cancel()
        self.comm.shut_down()

if __name__ == '__main__':
    led_controller = LedController()
    try:
        while True:
            time.sleep(2.0)
    except KeyboardInterrupt:
        pass
    led_controller.shut_down()
