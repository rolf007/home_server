#!/usr/bin/env python3

from radio import Radio
from pygame_inputter import PyGameInputter

inputter = PyGameInputter()

radio = Radio(inputter)
try:
    radio.main_loop()
except KeyboardInterrupt:
    pass
radio.shut_down()
