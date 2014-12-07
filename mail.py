from pygmi import Button, events, wmii

class Mail(object):

    def __init__(self, name='mail', colors=None, warn_colors=None,
            warn_level=5):
        if not colors: colors = wmii.cache['normcolors']
        if not warn_colors: warn_colors = wmii.cache['urgentcolors']
        self.colors = colors
        self.warn_colors = warn_colors
        self.warn_level = warn_level
        self.button = Button('right', name, colors)
        events.bind({'Mail': lambda args: self._mail(args)})
        self._mail('init 0')

    def _mail(self, mail):
        count = int(mail.split()[1])
        if count < self.warn_level:
            self.button.colors = self.colors
        else:
            self.button.colors = self.warn_colors
        self.button.label = 'Mail: %d' % count
