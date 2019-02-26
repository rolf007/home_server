#!/usr/bin/env python3

import os
import sys
import threading
import time

home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])
sys.path.append(os.path.join(home_server_root, "comm"))
sys.path.append(os.path.join(home_server_root, "utils"))
from comm import Comm
from micro_service import MicroServiceHandler

class LedController():
    class Led():
        def __init__(self):
            self.anim = [(0,(0,0,0,0,0))]
            self.i = 0
            self.repeat_point = 0
            self.repeat_count = 0
            self.now = (0,0,0,0,0)
            self.duration = 0
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

        def fade_mix(self):
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
                self.src = self.now
                self.dst = self.now
                self.next_step(overtime)
                self.running = True
            elif cmd == "fade":
                self.time = overtime
                self.duration = self.anim[self.i][1]
                self.src = self.now
                self.dst = self.anim[self.i][2]
                self.running = True
                self.fade_mix()
            elif cmd == "wait":
                self.time = overtime
                self.duration = self.anim[self.i][1]
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
                self.fade_mix()
            else:
                self.running = False
            if self.time >= self.duration:
                self.next_step(self.time - self.duration)



    def __init__(self, logger, exc_cb, dt, host_mode):
        self.dt = dt
        self.host_mode = host_mode
        self.logger = logger
        self.logger.log("host_mode = %s" % host_mode)
        self.comm = Comm(5008, "led", {"set": self.set_leds, }, self.logger, exc_cb)
        self.startup_timer = None
        self.num_leds = 8
        self.num_layers = 3
        self.leds = [[self.Led() for i in range(self.num_layers)] for i in range(self.num_leds)]
        self.meta_led = self.Led()


        if self.host_mode:
            pygame.display.init()
            self.rect = 30
            self.display = pygame.display.set_mode((self.rect*self.num_leds,100))
        else:
            # We only have SPI bus 0 available to us on the Pi
            bus = 0

            #Device is the chip select pin. Set to 0 or 1, depending on the connections
            device = 1

            # Enable SPI
            self.spi = spidev.SpiDev()

            # Open a connection to a specific bus and device (chip select pin)
            self.spi.open(bus, device)

            # Set SPI speed and mode
            self.spi.max_speed_hz = 500000
            self.spi.mode = 0

        self.set_leds({"anim": ["boot"]})

    def timer_func(self):
        self.startup_timer = None
        running = False
        self.meta_led.update(self.dt)
        running = self.meta_led.running
        for layer in range(self.num_layers):
            for led in range(self.num_leds):
                self.leds[led][layer].update(self.dt)
                running = running or self.leds[led][layer].running

        if not self.host_mode:
            msg = [0x00, 0x00, 0x00, 0x00]
            self.spi.xfer2(msg)

        for led in range(self.num_leds-1,-1,-1):
            rA = 0
            gA = 0
            bA = 0
            aA = 255
            for layer in range(self.num_layers):
                rB = self.leds[led][layer].now[1]
                gB = self.leds[led][layer].now[2]
                bB = self.leds[led][layer].now[3]
                aB = self.leds[led][layer].now[4]
                rA = (rB * aB / 255) + (rA * aA * (255 - aB) / (255*255))
                gA = (gB * aB / 255) + (gA * aA * (255 - aB) / (255*255))
                bA = (bB * aB / 255) + (bA * aA * (255 - aB) / (255*255))
                aA = aB + (aA * (255 - aB) / 255)
            if self.host_mode:
                pygame.draw.rect(self.display, (rA, gA, bA),(led*self.rect,0,self.rect,self.rect))
            else:
                msg0 = [128+64+32+10, int(bA), int(gA), int(rA)]
                self.spi.xfer2(msg0)

        if self.host_mode:
            pygame.display.update()
        else:
            msg = [0xff, 0xff, 0xff, 0xff]
            self.spi.xfer2(msg)

        if running:
            self.startup_timer = threading.Timer(self.dt, self.timer_func)
            self.startup_timer.start()

    # http://127.0.0.1:5008/set?anim=mp
    def set_leds(self, params):
        if "anim" not in params:
            return (404, "function 'set' requires 'anim'")
        anim = params["anim"][0]
        if anim == "mp":
            self.leds[0][0].set_anim([("set",(10,0,0,255,255))])
            self.leds[1][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[2][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[3][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[4][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[5][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[6][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[7][0].set_anim([("set",(0,0,0,0,255))])
        elif anim == "mp_wait":
            self.leds[0][0].set_anim([("set",(10,0,0,255,255)), ("repeat",0), ("fade",1,(0,0,0,0,255)), ("fade",1,(10,0,0,255,255)), ("loop",)])
            self.leds[1][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[2][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[3][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[4][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[5][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[6][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[7][0].set_anim([("set",(0,0,0,0,255))])
        elif anim == "tu":
            self.leds[0][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[1][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[2][0].set_anim([("set",(10,0,0,255,255))])
            self.leds[3][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[4][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[5][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[6][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[7][0].set_anim([("set",(0,0,0,0,255))])
        elif anim == "vi":
            self.leds[0][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[1][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[2][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[3][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[4][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[5][0].set_anim([("set",(10,0,0,255,255))])
            self.leds[6][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[7][0].set_anim([("set",(0,0,0,0,255))])
        elif anim == "vi_wait":
            self.leds[0][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[1][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[2][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[3][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[4][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[5][0].set_anim([("set",(10,0,0,255,255)), ("repeat",0), ("fade",1,(0,0,0,0,255)), ("fade",1,(10,0,0,255,255)), ("loop",)])
            self.leds[6][0].set_anim([("set",(0,0,0,0,255))])
            self.leds[7][0].set_anim([("set",(0,0,0,0,255))])
        elif anim == "radio_menu":
            self.leds[0][1].set_anim([("set",(0,0,255,0,255))])
            self.leds[1][1].set_anim([("set",(0,0,255,0,255))])
            self.leds[2][1].set_anim([("set",(0,0,255,0,255))])
            self.leds[3][1].set_anim([("set",(0,255,255,0,255))])
            self.leds[4][1].set_anim([("set",(0,0,0,0,255))])
            self.leds[5][1].set_anim([("set",(0,0,0,0,255))])
            self.leds[6][1].set_anim([("set",(0,0,0,0,255))])
            self.leds[7][1].set_anim([("set",(0,0,0,0,255))])
        elif anim == "playlist_menu":
            self.leds[0][1].set_anim([("set",(0,255,0,0,255))])
            self.leds[1][1].set_anim([("set",(0,100,255,0,255))])
            self.leds[2][1].set_anim([("set",(0,255,255,0,255))])
            self.leds[3][1].set_anim([("set",(0,100,0,100,255))])
            self.leds[4][1].set_anim([("set",(0,0,0,140,255))])
            self.leds[5][1].set_anim([("set",(0,20,160,255,255))])
            self.leds[6][1].set_anim([("set",(0,0,0,0,255))])
            self.leds[7][1].set_anim([("set",(0,0,0,0,255))])
        elif anim == "podcast_menu":
            self.leds[0][1].set_anim([("set",(0,255,0,0,255))])
            self.leds[1][1].set_anim([("set",(0,255,255,255,255))])
            self.leds[2][1].set_anim([("set",(0,255,0,0,255))])
            self.leds[3][1].set_anim([("set",(0,255,255,255,255))])
            self.leds[4][1].set_anim([("set",(0,255,0,0,255))])
            self.leds[5][1].set_anim([("set",(0,255,255,255,255))])
            self.leds[6][1].set_anim([("set",(0,255,0,0,255))])
            self.leds[7][1].set_anim([("set",(0,255,255,255,255))])
        elif anim == "flow_menu":
            d = 0.4
            self.leds[0][1].set_anim([("set",(0,255,0,0,255))])
            self.leds[1][1].set_anim([("set",(0,0,255,0,255))])
            self.leds[2][1].set_anim([("repeat", 0),
                                      ("set",(0,0,0,255,255)), ("wait", d),
                                      ("set",(0,255,255,0,255)), ("wait", d),
                                      ("set",(0,255,0,255,255)), ("wait", d),
                                      ("set",(0,255,0,0,255)), ("wait", d),
                                      ("set",(0,0,255,255,255)), ("wait", d),
                                      ("loop",)])
            self.leds[3][1].set_anim([("set",(0,0,255,0,255))])
            self.leds[4][1].set_anim([("set",(0,255,0,0,255))])
            self.leds[5][1].set_anim([("set",(0,0,0,0,255))])
            self.leds[6][1].set_anim([("set",(0,0,0,0,255))])
            self.leds[7][1].set_anim([("set",(0,0,0,0,255))])
        elif anim == "clear_submenu":
            self.leds[0][1].set_anim([("set",(0,0,0,0,0))])
            self.leds[1][1].set_anim([("set",(0,0,0,0,0))])
            self.leds[2][1].set_anim([("set",(0,0,0,0,0))])
            self.leds[3][1].set_anim([("set",(0,0,0,0,0))])
            self.leds[4][1].set_anim([("set",(0,0,0,0,0))])
            self.leds[5][1].set_anim([("set",(0,0,0,0,0))])
            self.leds[6][1].set_anim([("set",(0,0,0,0,0))])
            self.leds[7][1].set_anim([("set",(0,0,0,0,0))])

        elif anim == "knightrider":
            period = 1.35
            t = 0.6
            d = period/((self.num_leds-1)*2)
            on = (10,255,0,0,255)
            off = (0,255,0,0,0)
            self.meta_led.set_anim([("repeat", 10),
                                    ("setanim", self.leds[0][2], [("set",on), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[1][2], [("set",on), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[2][2], [("set",on), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[3][2], [("set",on), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[4][2], [("set",on), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[5][2], [("set",on), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[6][2], [("set",on), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[7][2], [("set",on), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[6][2], [("set",on), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[5][2], [("set",on), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[4][2], [("set",on), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[3][2], [("set",on), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[2][2], [("set",on), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[1][2], [("set",on), ("fade", t, off)]), ("wait", 1*d),
                                    ("loop",),
                                    ("setanim", self.leds[0][2], [("set",on), ("fade", t, off)]), ("wait", 1*d),])

        elif anim == "boot":
            period = 1.35
            t = 0.6
            d = 0.05
            red = (10,255,0,0,255)
            green = (10,0,255,0,255)
            blue = (10,0,0,255,255)
            white = (10,255,255,255,255)
            off = (0,0,0,0,255)
            off_white = (0,255,255,255,0)
            self.meta_led.set_anim([
                                    ("setanim", self.leds[0][2], [("set",red), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[1][2], [("set",red), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[2][2], [("set",red), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[3][2], [("set",red), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[4][2], [("set",red), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[5][2], [("set",red), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[6][2], [("set",red), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[7][2], [("set",red), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[0][2], [("set",green), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[1][2], [("set",green), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[2][2], [("set",green), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[3][2], [("set",green), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[4][2], [("set",green), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[5][2], [("set",green), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[6][2], [("set",green), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[7][2], [("set",green), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[0][2], [("set",blue), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[1][2], [("set",blue), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[2][2], [("set",blue), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[3][2], [("set",blue), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[4][2], [("set",blue), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[5][2], [("set",blue), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[6][2], [("set",blue), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[7][2], [("set",blue), ("fade", t, off)]), ("wait", 1*d),
                                    ("setanim", self.leds[0][2], [("set",white), ("fade", t, off_white)]), ("wait", 1*d),
                                    ("setanim", self.leds[1][2], [("set",white), ("fade", t, off_white)]), ("wait", 1*d),
                                    ("setanim", self.leds[2][2], [("set",white), ("fade", t, off_white)]), ("wait", 1*d),
                                    ("setanim", self.leds[3][2], [("set",white), ("fade", t, off_white)]), ("wait", 1*d),
                                    ("setanim", self.leds[4][2], [("set",white), ("fade", t, off_white)]), ("wait", 1*d),
                                    ("setanim", self.leds[5][2], [("set",white), ("fade", t, off_white)]), ("wait", 1*d),
                                    ("setanim", self.leds[6][2], [("set",white), ("fade", t, off_white)]), ("wait", 1*d),
                                    ("setanim", self.leds[7][2], [("set",white), ("fade", t, off_white)]), ("wait", 1*d),
                                    ])

        running = self.meta_led.running
        for layer in range(self.num_layers):
            for led in range(self.num_leds):
                running = running or self.leds[led][layer].running
        if running and self.startup_timer == None:
            self.startup_timer = threading.Timer(self.dt, self.timer_func)
            self.startup_timer.start()

        return (200, "%s" % "Led ok!")

    def shut_down(self):
        if host_mode:
            pygame.display.quit()
            pygame.quit(); #sys.exit() if sys is imported

        if self.startup_timer != None:
            self.startup_timer.cancel()
        self.comm.shut_down()

if __name__ == '__main__':
    try:
        import RPi.GPIO as gpio
        import spidev
        host_mode = False
    except (ImportError, RuntimeError):
        import pygame
        host_mode = True
    MicroServiceHandler("led", LedController, 0.01, host_mode)
