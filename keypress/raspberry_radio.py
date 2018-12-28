#!/usr/bin/env python3

from radio import Radio
from raspberry_inputter import RaspberryInputter

inputter = RaspberryInputter()

radio = Radio(inputter)
try:
    radio.main_loop()
except KeyboardInterrupt:
    pass
radio.shut_down()
