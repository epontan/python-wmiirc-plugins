import os
from datetime import datetime
from threading import Thread, Lock, Event

from pygmi import Button, Tag, Client, Match, events, confpath

from plugins.dialog import check_dialog, dialog

import work_time

class Work(object):

    def __init__(self, name='work', colors=None,
            interval=60.0, path=None):
        self.interval = interval
        if not path:
            path = os.path.join(confpath[0], 'track')
        if not os.path.isdir(path):
            os.makedirs(path)
        self.path = path
        self.button = Button('right', name, colors)
        self.lock_proc = None
        self.lock_proc_lock = Lock() # oh the imagination
        self.work_time = work_time.WorkTime(self._today())
        self.active = True
        self.track('STARTED')

        def click_event(button):
            real_name = self.button.real_name
            return Match('RightBarClick', button, real_name)

        events.bind({
            click_event('1'): lambda *a: self._toggle_dialog(name)
        })

    def _toggle_dialog(self, name):
        if check_dialog(name):
            return
        dialog('Worked time:\n  %s (%.2f)\n\nLunch:\n  %s (%.2f)' % (
            self.work_time.get_time_worked(),
            self.work_time.get_time_worked_decimal(),
            self.work_time.get_time_lunched(),
            self.work_time.get_time_lunched_decimal()),
            name)

    def locked(self, proc):
        if not self.active:
            return
        with self.lock_proc_lock:
            self.lock_proc = proc
            self.thread_event.set()
            self.track('LOCKED')

    def track(self, state, *activity):
        with self.thread_lock:
            now = datetime.now()
            today = self._today(now)
            time = now.strftime('%Y-%m-%d %H:%M:%S')
            record = '%s|%s|%s' % (state, time, '|'.join(activity))
            self.work_time.analyze(record)
            open(today, 'a').write('%s\n' % record)

    def _loop(self):
        while self.active:
            with self.lock_proc_lock:
                if self.lock_proc:
                    self.lock_proc.wait()
                    self.lock_proc = None
                    self.track('UNLOCKED')
            tag = Tag('sel').id
            try:
                props = Client('sel').props
            except:
                props = 'NULL'
            self.track('NORMAL', tag, props)
            self.button.label = 'W: %s' % self.work_time.get_time_worked()
            self.thread_event.wait(self.interval)
            if self.thread_event.is_set():
                self.thread_event.clear()

    _active = False
    def _set_active(self, val):
        self._active = bool(val)
        if val:
            self.thread_lock = Lock()
            self.thread_event = Event()
            self.thread = Thread(target=self._loop)
            self.thread.daemon = True
            self.thread.start()
    active = property(lambda self: self._active, _set_active)

    def _today(self, now=None):
        if not now:
            now = datetime.now()
        return os.path.join(self.path, now.strftime('%Y_%m_%d'))
