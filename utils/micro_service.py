import os
import sys
import traceback
import time

home_server_root = os.path.split(sys.path[0])[0]
home_server_config = os.path.join(os.path.split(home_server_root)[0], "home_server_config", os.path.split(sys.path[0])[1])

sys.path.append(os.path.join(home_server_root, "logger"))
from logger import Logger

class MicroServiceHandler():
    def __init__(self, name, T, *args):
        logger = Logger(name)
        logger.log(">>> started %s" % T.__name__)
        t = None
        self.exc_info = None
        def exc_cb(ei):
            self.exc_info = ei
        try:
            t = T(logger, exc_cb, *args)
            while self.exc_info is None:
                if hasattr(T, "main_loop"):
                    t.main_loop()
                else:
                    time.sleep(2.0)
            new_exc = Exception("Error: Thread threw an exception: %s" % self.exc_info[1])
            raise new_exc.with_traceback(self.exc_info[2])
        except KeyboardInterrupt:
            logger.log("Received Ctrl-C")
        except:
            for line in traceback.format_exc().split('\n'):
                logger.log(line)
        if t is not None:
            t.shut_down()
        logger.log("<<< ended %s" % T.__name__)

