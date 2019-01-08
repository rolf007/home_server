from datetime import datetime, timezone

import os
import sys
import shutil

home_server_root = os.path.split(sys.path[0])[0]
sys.path.append(os.path.join(home_server_root, "utils"))
from mkdirp import mkdirp

class Logger():
    def __init__(self, name):
        self.log_dir = os.path.join(os.path.split(home_server_root)[0], "home_server_config", "log")
        mkdirp(self.log_dir)
        self.log_file = os.path.join(self.log_dir, "messages")
        self.name = name

    def log(self, text):
        local_time = datetime.now(timezone.utc).astimezone()
        local_time.isoformat()
        line = "%s %s: %s" % (local_time.isoformat(), self.name.ljust(12)[:12], ascii(text)[1:-1])
        print(line)
        if os.path.isfile(self.log_file):
            fsize = os.path.getsize(self.log_file)
        else:
            fsize = 0
        if fsize > 1024*1024:
            #log rotate
            shutil.copy(self.log_file, self.log_file + ".1")
            with open(self.log_file, 'w') as f:
                f.write(line + '\n')
        else:
            with open(self.log_file, 'a+') as f:
                f.write(line + '\n')

