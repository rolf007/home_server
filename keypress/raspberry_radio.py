#!/usr/bin/env python3

import os
import sys

from radio import Radio
from raspberry_inputter import RaspberryInputter

home_server_root = os.path.split(sys.path[0])[0]
sys.path.append(os.path.join(home_server_root, "utils"))
from micro_service import MicroServiceHandler

inputter = RaspberryInputter()

if __name__ == '__main__':
    MicroServiceHandler("radio", Radio, inputter)
