import re
from pygmi import Client, events, keys, call

_RE_POS = re.compile(r'^x:(\d+)\s+y:(\d+)')
_RE_DPY_GEO = re.compile(r'^(\d+)\s+(\d+)')
_RE_WIN_GEO = re.compile(r'^\s*Geometry:\s+(\d+)x(\d+)',  re.MULTILINE)

class NXHandler(object):

    def __init__(self):
        self.mode = 0
        self.win = None
        self.pos_nx = None
        self.pos_dpy = None

    def check_client(self, c):
        if c == '<nil>':
            return
        if self.mode == 2:
            setattr(keys, 'mode', 'main')
            self.mode = 0
        try:
            win = Client(c)
            if win.label.startswith('NX - ') and win.fullscreen:
                self.win = win
                self.mode = 1
        except:
            pass

    def check_area(self, a):
        if a != '~':
            return
        if self.mode == 1:
            setattr(keys, 'mode', 'nx')
            self.mode = 2

    def toggle(self):
        if not self.win:
            return
        pos = _point(_RE_POS, 'xdotool', 'getmouselocation')
        if self.win == Client('sel'):
            self.pos_nx = pos
            if self.pos_dpy:
                x, y = self.pos_dpy
            else:
                x, y = map(lambda v: v / 2, _point(_RE_DPY_GEO,
                    'xdotool', 'getdisplaygeometry'))
            call('xdotool', 'mousemove', str(x), str(y), background=True)
        else:
            self.pos_dpy = pos
            if self.pos_nx:
                x, y = self.pos_nx
            else:
                x, y = map(lambda v: v / 2, _point(_RE_WIN_GEO,
                    'xdotool', 'getwindowgeometry', str(self.win.id)))
            call('xdotool', 'mousemove', '--window', str(self.win.id), str(x), str(y),
                    background=True)

    def reset(self):
        self.pos_nx = None
        self.pos_dpy = None

    def toggle_fullscreen(self):
        if self.win:
            self.win.fullscreen = not self.win.fullscreen


def _point(pattern, *cmd):
    m = pattern.search(call(*cmd))
    return (int(m.group(1)), int(m.group(2)))
