import asyncio
import os
import sys
import traceback

home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])

sys.path.append(os.path.join(home_server_root, "logger"))
from logger import Logger

class MicroServiceHandler():
    def __init__(self, name, T, *args):
        loop = asyncio.get_event_loop()
        self.logger = Logger(name)
        self.logger.log(">>> started %s" % T.__name__)
        try:
            t = T(self.logger, self.exc_cb, *args)
            try:
                loop.run_forever()
            except KeyboardInterrupt:
                self.logger.log("Received Ctrl-C")
            finally:
                t.shut_down()
        except Exception as e:
            for line in traceback.format_exc().split('\n'):
                self.logger.log(line)
        self.logger.log("<<< ended %s" % T.__name__)

    async def exc_cb(self, ei):
        for line in traceback.format_exc().split('\n'):
            self.logger.log(line)
        exit(1)
