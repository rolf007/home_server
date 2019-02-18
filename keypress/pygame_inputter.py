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

    def click_NAD_button(self, n):
        pass

    def main_loop(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                c = None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a: c = 'A'
                    if event.key == pygame.K_b: c = 'B'
                    if event.key == pygame.K_c: c = 'C'
                    if event.key == pygame.K_d: c = 'D'
                    if event.key == pygame.K_e: c = 'E'
                    if event.key == pygame.K_f: c = 'F'
                    if event.key == pygame.K_g: c = 'G'
                    if event.key == pygame.K_h: c = 'H'
                    if c: self.runner.key_input(c, True)
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_q:
                        self.running = False
                    if event.key == pygame.K_a: c = 'a'
                    if event.key == pygame.K_b: c = 'b'
                    if event.key == pygame.K_c: c = 'c'
                    if event.key == pygame.K_d: c = 'd'
                    if event.key == pygame.K_e: c = 'e'
                    if event.key == pygame.K_f: c = 'f'
                    if event.key == pygame.K_g: c = 'g'
                    if event.key == pygame.K_h: c = 'h'
                    if c: self.runner.key_input(c, False)

    def shut_down(self):
        print("==========PyGameInputter shut_down")
        self.runner.shut_down()
        pygame.display.quit()
        pygame.quit(); #sys.exit() if sys is imported

