from threading import Timer

from pygmi import Button, events, client

class Notice(object):

    def __init__(self, name='!notice', colors=None, timeout=5):
        self.timeout = timeout
        self.timer = None
        self.button = Button('right', name, colors)
        events.bind({'Notice': lambda args: self.show(args)})
        self.tick()

    def tick(self):
        self.button.label = ' '

    def show(self, notice):
        if self.timer:
            self.timer.cancel()
        self.button.label = notice
        try:
            self.timer = Timer(self.timeout, self.tick)
            self.timer.start()
        except:
            pass

def write(notice):
    client.awrite('/event', 'Notice %s' % notice.replace('\n', ' '))
