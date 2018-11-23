from threading import Timer

class KeyPressRunner:
    def __init__(self):
        super(KeyPressRunner, self).__init__()
        self.keys = 0
        self.key_press = None
        self.timer = None
        self.relax_timer = None

    def key_input(self, c, down):
        if down:
            self.keys = self.keys + 1
        else:
            self.keys = self.keys - 1
        self.times = self.key_press.process_input(c)
        self.process(0)

    def timer_stuff(self, this_time):
        self.timer = None
        self.times |= self.key_press.process_input(this_time)
        self.times = { x for x in self.times if x > this_time }
        self.process(this_time)

    def done_relaxing(self):
        self.relax_timer = None
        self.key_press.reset()

    def process(self, this_time):
        status = self.key_press.status()
        if status == "in progress":
            if self.times:
                next_time = min(self.times)
                if self.timer: self.timer.cancel()
                self.timer = Timer((next_time-this_time)/1000.0, lambda: self.timer_stuff(next_time))
                self.timer.start()
        else:
            if self.keys == 0:
                if status == "match":
                    self.key_press.reset()
                else:
                    if self.relax_timer: self.relax_timer.cancel()
                    self.relax_timer = Timer(1, self.done_relaxing)
                    self.relax_timer.start()

