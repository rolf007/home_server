from keypress_runner import KeyPressRunner
from gpiozero import LED, Button

class RaspberryInputter():
    def __init__(self):
        self.running = True
        self.runner = KeyPressRunner()
        button2 = Button(2)
        button3 = Button(3)
        button4 = Button(4)

        button2.when_pressed = lambda: self.runner.key_input('A', True)
        button2.when_released = lambda: self.runner.key_input('a', False)
        button3.when_pressed = lambda: self.runner.key_input('B', True)
        button3.when_released = lambda: self.runner.key_input('b', False)
        button4.when_pressed = lambda: self.runner.key_input('C', True)
        button4.when_released = lambda: self.runner.key_input('c', False)

    def set_key_press(self, key_press):
        self.runner.set_key_press(key_press)

    def main_loop(self):
        while self.running:
            time.sleep(1)

    def shut_down(self):
        self.runner.shut_down()

