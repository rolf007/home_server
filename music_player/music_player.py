#!/usr/bin/env pyhton
#https://raspberrypi.stackexchange.com/questions/43720/disable-wifi-wlan0-on-pi-3
#To completely disable the onboard WiFi from the firmware on the Pi3, add
#dtoverlay=pi3-disable-wifi
#in /boot/config.txt.
#https://makezine.com/projects/tutorial-raspberry-pi-gpio-pins-and-python/

import RPi.GPIO as GPIO
#set up GPIO using BCM numbering
GPIO.setmode(GPIO.BCM)
#setup GPIO using Board numbering
GPIO.setmode(GPIO.BOARD)
GPIO.setup(23, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
if(GPIO.input(23) ==1):
    print(?Button 1 pressed?)

GPIO.wait_for_edge(23, GPIO.RISING)
print(?Button 1 Pressed?)
GPIO.wait_for_edge(23, GPIO.FALLING)
print(?Button 1 Released?)


GPIO.cleanup()

