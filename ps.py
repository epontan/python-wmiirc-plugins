import re

from pygmi import Match, monitor, events, call, _

from plugins.dialog import check_dialog, dialog

_RE_MEMINFO = re.compile(r'^([^:]+):\s*(\d+)')

class Cpu(object):

    def __init__(self, name='cpu', colors=None,
            interval=2.0):
        self.last_cpu_sum = 0
        self.last_cpu_idle = 0
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
        return 'C: %2d%%' % self._get_cpu_percent()

    def _toggle_dialog(self, name):
        if check_dialog(name):
            return
        dialog(call('top', '-b', '-i', '-n', '1'), name)

    def _get_cpu_percent(self):
        with open('/proc/stat') as f:
            cpu_stat = [long(n) for n in f.readline()[3:].split()]
        cpu_sum = sum(cpu_stat)
        idle = cpu_stat[3]
        idle_diff = idle - self.last_cpu_idle
        idle_check = (0, idle_diff)
        total = cpu_sum - self.last_cpu_sum - idle_check[idle_diff < 0]
        self.last_cpu_sum = cpu_sum
        self.last_cpu_idle = idle
        return 100 - idle_check[idle_diff > 0] * 100 / total


# Real memory usage in Linux (include tmpfs)
# http://calimeroteknik.free.fr/blag/?article20/really-used-memory-on-gnu-linux
class Memory(object):

    def __init__(self, name='memory', colors=None,
            interval=6.0):
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
        return 'M: %2d%%' % self._get_used_percent()

    def _toggle_dialog(self, name):
        if check_dialog(name):
            return
        free = call('free', '-h')
        df = call('df', '-h', '--type=tmpfs')
        dialog('%s\n\n%s' % (free, df), name)

    def _get_used_percent(self):
        def _extract(s):
            m = _RE_MEMINFO.search(s)
            return m.group(1), int(m.group(2))

        with open('/proc/meminfo') as f:
            meminfo = dict(map(_extract, f.readlines()))
        return round(100 - (meminfo['MemFree'] +
            meminfo['Buffers'] +
            meminfo['SReclaimable'] +
            meminfo['Cached'] -
            meminfo['Shmem']) / float(meminfo['MemTotal']) * 100)

