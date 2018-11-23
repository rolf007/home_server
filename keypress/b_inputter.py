import time
from keypress_runner import KeyPressRunner

class BInputter(KeyPressRunner):
    def __init__(self):
        super(BInputter, self).__init__()

    def main_loop(self):
        self.key_input('B', True)
        self.key_input('b', False)
        while True:
            time.sleep(1)

    def shut_down(self):
        print("BInputter shut_down")
