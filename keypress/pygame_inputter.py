import pygame
from keypress_runner import KeyPressRunner

class PyGameInputter(KeyPressRunner):
    def __init__(self):
        super(PyGameInputter, self).__init__()
        self.running = True
        pygame.display.init()
        pygame.display.set_mode((100,100))

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
                    self.key_input(c, True)
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
                    self.key_input(c, False)

    def shut_down(self):
        print("==========PyGameInputter shut_down")
        if self.timer: self.timer.cancel()
        if self.relax_timer: self.relax_timer.cancel()
        pygame.display.quit()
        pygame.quit(); #sys.exit() if sys is imported

