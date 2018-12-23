import time
from keypress_runner import KeyPressRunner

class BInputter():
    def __init__(self):
        self.runner = KeyPressRunner()

    def set_key_press(self, key_press):
        self.runner.set_key_press(key_press)

    def main_loop(self):
        self.runner.key_input('B', True)
        self.runner.key_input('b', False)
        while True:
            time.sleep(1)

    def shut_down(self):
        print("BInputter shut_down")
        self.runner.shut_down()
