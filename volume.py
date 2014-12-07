import re

from pygmi import Button, Match, keys, events, call

_RE_VOLUME = re.compile(r'\[(\d+%)\].*\[(on|off)\]$')

class Volume(object):

    def __init__(self, name='volume', colors=None,
            channel='Master', device=None):
        self.channel = channel
        self.device = device
        self.button = Button('right', name, colors)

        keys.bind('main', (
            "Volume control",
            ('XF86AudioMute', "Toggle mute volume",
                lambda k: self.toggle()),
            ('XF86AudioRaiseVolume', "Raise the volume",
                lambda k: self.up()),
            ('XF86AudioLowerVolume', "Lower the volume",
                lambda k: self.down()),
        ))

        def click_event(button):
            return Match('RightBarClick', button, self.button.real_name)

        events.bind({
            click_event('1'): lambda *a: self.toggle(),
            click_event('3'): lambda *a: self.set_using_menu(),
            click_event('4'): lambda *a: self.up(),
            click_event('5'): lambda *a: self.down()
        })

        self.refresh()

    def refresh(self):
        self.button.label = self._mixer()

    def toggle(self):
        self.button.label = self._mixer('toggle')

    def set(self, value):
        self.button.label = self._mixer('playback', '%d%%' % value)

    def up(self, amount=5):
        self.button.label = self._mixer('playback', '%d%%+' % amount)

    def down(self, amount=5):
        self.button.label = self._mixer('playback', '%d%%-' % amount)

    def set_using_menu(self):
        levels = map(str, range(100, -10, -10))
        level = call('wmii9menu', *levels)
        if level:
            self.set(int(level))

    def _mixer(self, *args):
        cmd = ['amixer']
        if self.device:
            cmd.append('-D')
            cmd.append(self.device)
        if args:
            cmd.append('set')
        else:
            cmd.append('get')
        cmd.append(self.channel)
        if args:
            cmd += args

        value = 'ERR'
        for line in call(*cmd).split('\n'):
            m = _RE_VOLUME.search(line)
            if m:
                if m.group(2) == 'off':
                    value = '-'
                else:
                    value = '%2s' % m.group(1)
                break
        return 'V: %s' % value
