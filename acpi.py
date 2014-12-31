import re
import sys
import traceback
from collections import deque

from pygmi import Match, monitor, events, wmii, find, _

from wmiirc import program_menu
from plugins.dialog import check_dialog, dialog

_POWER_SUPPLY_PATH = '/sys/class/power_supply'

_BAT_CAPACITY = 'capacity'
_BAT_CURRENT_NOW = re.compile(r'^(current|power)_now$')
_BAT_CHARGE_NOW = re.compile(r'^(charge|energy)_now$')
_BAT_CHARGE_FULL = re.compile(r'^(charge|energy)_full$')
_BAT_STATUS = 'status'
_AC_ONLINE = 'online'

_CHARGE_STATE = '', ' *'
_WARNING_NAME = 'battery_warning'
_WARNING_LEVEL = 15

_CURRENT_AVG_SAMPLES = 10

class Battery(object):

    def __init__(self, bat_path=None, ac_path=None,
            name='battery', colors=None, interval=4.0):
        self.bat_capacity_path = _find_path(bat_path, _BAT_CAPACITY)
        self.bat_current_now_path = _find_path(bat_path, _BAT_CURRENT_NOW)
        self.bat_charge_now_path = _find_path(bat_path, _BAT_CHARGE_NOW)
        self.bat_charge_full_path = _find_path(bat_path, _BAT_CHARGE_FULL)
        self.bat_status_path = _find_path(bat_path, _BAT_STATUS)
        self.ac_online_path = _find_path(ac_path, _AC_ONLINE)
        self.current_avg = deque(maxlen=_CURRENT_AVG_SAMPLES)
        self.warned = False
        monitor.defmonitor(self._monitor_action,
                name = name,
                colors = colors,
                interval = interval)
        if not colors: colors = wmii.cache['normcolors']
        self.colors = self.normcolors = colors

        def click_event(button):
            real_name = monitor.monitors[name].button.real_name
            return Match('RightBarClick', button, real_name)

        events.bind({
            click_event(_): lambda *a: self._toggle_dialog(name)
        })

    def _monitor_action(self, monitor):
        try: self.current_avg.append(int(_read(self.bat_current_now_path)))
        except: pass

        try:
            capacity = int(_read(self.bat_capacity_path))
            if capacity > 100: capacity = 100
            online = int(_read(self.ac_online_path))
            if (online or capacity > _WARNING_LEVEL) and self.warned:
                self.colors = self.normcolors
                monitor.button.colors = self.colors
                check_dialog(_WARNING_NAME)
                self.warned = False
            elif not online and capacity <= _WARNING_LEVEL and not self.warned:
                self.colors = wmii.cache['urgentcolors']
                monitor.button.colors = self.colors
                dialog('WARNING! Battery level is low!', _WARNING_NAME,
                    colors=self.colors)
                self.warned = True
        except Exception, e:
            traceback.print_exc(sys.stdout)
            capacity = -1
            online = 0
            monitor.active = False

        return 'B: %2d%%%s' % (capacity, _CHARGE_STATE[online])

    def _toggle_dialog(self, name):
        if check_dialog(name):
            return
        try:
            current_now = sum(self.current_avg) / len(self.current_avg)
            charge_now = int(_read(self.bat_charge_now_path))
            status = _read(self.bat_status_path)
            if status == 'Discharging':
                info = '%s - %s remaining' % (
                    status, _format_time(charge_now, current_now))
            elif status == 'Charging':
                charge_full = int(_read(self.bat_charge_full_path))
                info = '%s - %s until charged' % (
                    status, _format_time(charge_full - charge_now, current_now))
            else:
                info = 'Status: %s' % status
            dialog(info, name, colors=self.colors)
        except Exception, e:
            traceback.print_exc(sys.stdout)
            dialog('Error', name)


def _read(path):
    with open(path) as f:
        return f.read().rstrip()

def _format_time(amount, rate):
    secs = 3600 * amount / rate
    hours = secs / 3600
    secs %= 3600
    mins = secs / 60
    secs %= 60
    return '%02d:%02d:%02d' % (hours, mins, secs)


def _find_path(path, target):
    if not path:
        path = _POWER_SUPPLY_PATH
    return find(path, target, depth=3, followlinks=True)
