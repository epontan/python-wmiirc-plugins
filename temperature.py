import re
import os

from pygmi import Match, monitor, events, call, find, _

from wmiirc import program_menu
from plugins.dialog import check_dialog, dialog

_NVIDIA = re.compile(r': (\d+)\.$'), 'nvidia-settings', '-q', 'GPUCoreTemp'
_ATI = re.compile(r' (\d+)\..* C'), 'aticonfig', '--odgt'

_HWMON_PATH = '/sys/class/hwmon'
_TEMP_INPUT = 'temp1_input'

class Temperature(object):

    def __init__(self, input_path=None, name='temperature', colors=None,
            interval=6.0):
        self.input_path = self._find_temp_input(input_path)
        self.gpu = self._get_gpu()
        monitor.defmonitor(self._monitor_action,
                name = name,
                colors = colors,
                interval = interval)

        def click_event(button):
            real_name = monitor.monitors[name].button.real_name
            return Match('RightBarClick', button, real_name)

        events.bind({
            click_event(_): lambda *a: self._toggle_dialog(name)
        })

    def _monitor_action(self, monitor):
        try:
            with open(self.input_path) as f:
                temp = int(f.read()) / 1000
        except:
            temp = -1
        if self.gpu:
            return 'T: c=%d g=%d' % (temp, self._gpu_temp(*self.gpu))
        return 'T: %d' % temp

    def _toggle_dialog(self, name):
        if check_dialog(name):
            return
        info = call('sensors')
        if self.gpu:
            info += '\n\n' + call(*self.gpu[1:])
        dialog(info, name)

    def _get_gpu(self):
        if 'nvidia-settings' in program_menu.choices:
            return _NVIDIA
        elif 'aticonfig' in program_menu.choices:
            return _ATI
        else:
            return None

    def _gpu_temp(self, pattern, *args):
        for line in call(*args).split('\n'):
            m = pattern.search(line)
            if m:
                return int(m.group(1))
        return -1

    def _find_temp_input(self, input_path):
        if input_path and os.path.isfile(input_path):
            return input_path
        return find(_HWMON_PATH, _TEMP_INPUT, depth=3, followlinks=True)
