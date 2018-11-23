from keypress_runner import KeyPressRunner

class RaspberryInputter(KeyPressRunner):
    def __init__(self):
        super(RaspberryInputter, self).__init__()
        from gpiozero import LED, Button
        self.running = True
        button2 = Button(2)
        button3 = Button(3)
        button4 = Button(4)

        button2.when_pressed = lambda: self.key_input('A', True)
        button2.when_released = lambda: self.key_input('a', False)
        button3.when_pressed = lambda: self.key_input('B', True)
        button3.when_released = lambda: self.key_input('b', False)
        button4.when_pressed = lambda: self.key_input('C', True)
        button4.when_released = lambda: self.key_input('c', False)

    def main_loop(self):
        while self.running:
            time.sleep(1)

    def shut_down(self):
        pass

