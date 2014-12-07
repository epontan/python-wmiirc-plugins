from datetime import datetime
from pygmi import Match, monitor, events, call, wmii

from plugins.dialog import check_dialog, dialog

class Clock(object):

    def __init__(self, name='clock', colors=None,
            interval=2.0, format='%Y-%m-%d w%V %H:%M'):
        self.format = format
        self.calendar_process = None
        monitor.defmonitor(self._monitor_action,
                name = name,
                colors = colors,
                interval = interval)

        def click_event(button):
            real_name = monitor.monitors[name].button.real_name
            return Match('RightBarClick', button, real_name)

        events.bind({
            click_event('1'): lambda *a: self.toggle_calendar(),
            click_event('3'): lambda *a: self.toggle_tz_time_dialog(name)
        })

    def toggle_calendar(self):
        if self.calendar_process:
            self.calendar_process.terminate()
            self.calendar_process = None
        else:
            self.calendar_process = call('wmiir', 'setsid',
                    'wmii-cal', '-nc', '-fn', wmii['font'],
                    background=True)

    def toggle_tz_time_dialog(self, name):
        if check_dialog(name):
            return
        sweden = call('date', env={'TZ': 'Europe/Stockholm'})
        montreal = call('date', env={'TZ': 'America/Montreal'})
        shanghai = call('date', env={'TZ': 'Asia/Shanghai'})
        dialog("  Sweden: %s\n\nMontreal: %s\n\nShanghai: %s"
                % (sweden, montreal, shanghai), name)

    def _monitor_action(self, monitor):
        return datetime.now().strftime(self.format)
