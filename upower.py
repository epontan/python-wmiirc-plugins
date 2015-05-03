import dbus

from pygmi import Button, Match, events, wmii, call, _

from plugins.dbus_instance import get_system_bus
from plugins.dialog import check_dialog, dialog

_BUS = 'org.freedesktop.UPower'
_PATH = '/org/freedesktop/UPower'
_DEV_IFACE = 'org.freedesktop.UPower.Device'

_CHARGE_STATE = '', ' *'
_WARNING_NAME = 'battery_warning'
_WARNING_LEVEL = 15


class Battery(object):

    def __init__(self, name='upower',
            colors=wmii.cache['normcolors'],
            warn_colors=wmii.cache['urgentcolors']):

        bus = get_system_bus(_BUS, _PATH)
        battery_path = ac_path = None
        for device in bus.get_interface().EnumerateDevices():
            if 'battery' in device:
                battery_path = device
            elif 'line_power' in device:
                ac_path = device
        if not battery_path or not ac_path:
            return

        self.button = Button('right', name, colors)
        self.colors = colors
        self.warn_colors = warn_colors
        self.warned = False

        def click_event(button):
            return Match('RightBarClick', button, self.button.real_name)

        events.bind({
            click_event(_): lambda *a: self.toggle_dialog()
        })

        self.battery = bus.get_prop_interface(_DEV_IFACE, battery_path)
        self.ac = bus.get_prop_interface(_DEV_IFACE, ac_path)
        self.refresh = bus.get_interface(_DEV_IFACE, battery_path).Refresh
        bus.add_callback(self.update, 'Changed', _DEV_IFACE, battery_path)
        self.update()

    def toggle_dialog(self):
        name = self.button.name
        if check_dialog(name):
            return

        self.refresh()
        online = self.ac.Online
        time_to_full = self.battery.TimeToFull
        time_to_empty = self.battery.TimeToEmpty

        if online and time_to_full == 0:
            info = 'Fully charged'
        elif online:
            info = 'Charging - %s until charged' % _format_time(time_to_full)
        else:
            info = 'Discharging - %s remaining' % _format_time(time_to_empty)

        dialog(info, name, colors=self.colors)

    def update(self):
        capacity = self.battery.Percentage
        online = self.ac.Online

        if (online or capacity > _WARNING_LEVEL) and self.warned:
            self.button.colors = self.colors
            check_dialog(_WARNING_NAME)
            self.warned = False
        elif not online and capacity <= _WARNING_LEVEL and not self.warned:
            self.button.colors = self.warn_colors
            dialog('WARNING! Battery level is low!', _WARNING_NAME,
                    colors=self.warn_colors)
            self.warned = True

        self.button.label = 'B: %2d%%%s' % (capacity, _CHARGE_STATE[online])


def _format_time(secs):
    hours = secs / 3600
    secs %= 3600
    mins = secs / 60
    secs %= 60
    return '%02d:%02d:%02d' % (hours, mins, secs)
