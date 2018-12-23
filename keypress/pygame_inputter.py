import pygame
from keypress_runner import KeyPressRunner

class PyGameInputter():
    def __init__(self):
        self.running = True
        self.runner = KeyPressRunner()
        pygame.display.init()
        pygame.display.set_mode((100,100))

    def set_key_press(self, key_press):
        self.runner.set_key_press(key_press)

    def main_loop(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                c = None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        c = 'A'
                    if event.key == pygame.K_b:
                        c = 'B'
                    if event.key == pygame.K_c:
                        c = 'C'
                    if event.key == pygame.K_d:
                        c = 'D'
                    self.runner.key_input(c, True)
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_q:
                        self.running = False
                    if event.key == pygame.K_a:
                        c = 'a'
                    if event.key == pygame.K_b:
                        c = 'b'
                    if event.key == pygame.K_c:
                        c = 'c'
                    if event.key == pygame.K_d:
                        c = 'd'
                    self.runner.key_input(c, False)

    def shut_down(self):
        print("==========PyGameInputter shut_down")
        self.runner.shut_down()
        pygame.display.quit()
        pygame.quit(); #sys.exit() if sys is imported

