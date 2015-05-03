import dbus

from pygmi import Button, Match, events, call, _

from plugins.dbus_instance import get_system_bus
from plugins.dialog import check_dialog, dialog


_NM_BUS = 'org.freedesktop.NetworkManager'
_NM_PATH = '/org/freedesktop/NetworkManager'
_NM_CONN_ACTIVE = '%s.Connection.Active' % _NM_BUS
_NM_ACCESS_POINT = '%s.AccessPoint' % _NM_BUS
_NM_AP_PATH = '%s/AccessPoint' % _NM_PATH

class NetworkManager(object):

    def __init__(self, name='network', colors=None):
        self.button = Button('right', name, colors)
        self.ap_signal = None

        self.bus = get_system_bus(_NM_BUS, _NM_PATH)
        self.bus.add_callback(self._prop_changed, 'PropertiesChanged')
        conns = self.bus.get_prop_interface().ActiveConnections
        if conns:
            self._handle_connection(conns[0])
        else:
            self.button.label = 'N: -'

        def click_event(button):
            return Match('RightBarClick', button, self.button.real_name)

        events.bind({
            click_event(_): lambda *a: self.toggle_dialog()
        })

    def toggle_dialog(self):
        name = self.button.name
        if check_dialog(name):
            return
        dialog(call('nm-tool'), name)

    def _handle_connection(self, path):
        ap_path = self.bus.get_prop_interface(
                _NM_CONN_ACTIVE, path).SpecificObject

        if ap_path.startswith(_NM_AP_PATH):
            strength = self.bus.get_prop_interface(
                    _NM_ACCESS_POINT, ap_path).Strength
            self.button.label = 'N: %2d%%' % strength

            if self.ap_signal is not None:
                self.ap_signal.remove()
            self.ap_signal = self.bus.add_callback(
                    self._ap_prop_changed, 'PropertiesChanged',
                    _NM_ACCESS_POINT, ap_path)

        else:
            self.button.label = 'N: e' # Assume ethernet

    def _prop_changed(self, props):
        if 'PrimaryConnection' in props:
            conn = props['PrimaryConnection']
            if conn == '/': return
            self._handle_connection(conn)
            return

        elif 'ActiveConnections' in props:
            if not props['ActiveConnections']:
                if self.ap_signal is not None:
                    self.ap_signal.remove()
                    self.ap_signal = None
                self.button.label = 'N: -'
                return

        if 'ActivatingConnection' in props:
            self.button.label = 'N: *'

    def _ap_prop_changed(self, props):
        if 'Strength' in props:
            self.button.label = 'N: %2d%%' % int(props['Strength'])


class Wicd(object):

    def __init__(self, name='network', colors=None):
        self.button = Button('right', name, colors)
        self.iface = None
        self.conn = None

        bus = get_system_bus('org.wicd.daemon', '/org/wicd/daemon')
        bus.add_callback(self._status_changed, 'StatusChanged')
        bus.get_interface().GetConnectionStatus(
                reply_handler=lambda args: self._status_changed(*args),
                error_handler=lambda args: None)

        def click_event(button):
            return Match('RightBarClick', button, self.button.real_name)

        events.bind({
            click_event(_): lambda *a: self.toggle_dialog()
        })

    def toggle_dialog(self):
        name = self.button.name
        if check_dialog(name):
            return

        if self.conn and self.iface[0] == 'wireless':
            dialog('    IP: %s\n'
                   '  Name: %s\n'
                   'Signal: %s%%\n'
                   ' Speed: %s'
                    % (self.conn[0], self.conn[1],
                        self.conn[2], self.conn[4]), name)

        elif self.conn:
            dialog('IP: %s' % self.conn[0], name)

        elif self.iface:
            if self.iface[0] == 'wireless':
                target = 'wireless network "%s" ...' % self.iface[1]
            else:
                target = '%s interface ...' % self.iface[0]
            dialog('Connecting to %s' % target, name)

        else:
            dialog('Not connected', name)


    def _status_changed(self, state, info):
        if state == 1:
            self.conn = None
            self.iface = info
            iface = 'w' if info[0] == 'wireless' else 'e'
            self.button.label = 'N: %s *' % iface

        elif state == 2:
            if not self.iface:
                self.iface = ('wireless',)
            self.conn = info
            self.button.label = 'N: %s%%' % info[2]

        elif state == 3:
            if not self.iface:
                self.iface = ('wired',)
            self.conn = info
            self.button.label = 'N: e'

        else:
            self.iface = None
            self.conn = None
            self.button.label = 'N: -'
