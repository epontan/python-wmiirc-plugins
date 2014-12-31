import dbus

from pygmi import Button, Match, events, call, _

from plugins.dbus_instance import get_system_bus
from plugins.dialog import check_dialog, dialog


_NM_BUS = _NM_IFACE = 'org.freedesktop.NetworkManager'
_NM_PATH = '/org/freedesktop/NetworkManager'
_NM_CONN_ACTIVE = '%s.Connection.Active' % _NM_IFACE
_NM_ACCESS_POINT = '%s.AccessPoint' % _NM_IFACE
_NM_AP_PATH = '%s/AccessPoint' % _NM_PATH

class NetworkManager(object):

    def __init__(self, name='network', colors=None):
        self.button = Button('right', name, colors)
        self.ap_signal = None
        _add(self._prop_changed, _NM_IFACE, 'PropertiesChanged')
        conns = _get(_NM_PATH, _NM_IFACE, 'ActiveConnections')
        if conns:
            self._handle_connection(conns[0])
        else:
            self.button.label = 'N: -'

        def click_event(button):
            return Match('RightBarClick', button, self.button.real_name)

        events.bind({
            click_event(_): lambda *a: self._toggle_dialog(name)
        })

    def _toggle_dialog(self, name):
        if check_dialog(name):
            return
        dialog(call('nm-tool'), name)

    def _handle_connection(self, path):
        ap_path = _get(path, _NM_CONN_ACTIVE, 'SpecificObject')
        if ap_path.startswith(_NM_AP_PATH):
            strength = int(_get(ap_path, _NM_ACCESS_POINT, 'Strength'))
            self.button.label = 'N: %2d%%' % strength
            if self.ap_signal is not None:
                self.ap_signal.remove()
            self.ap_signal = _add(self._ap_prop_changed,
                    _NM_ACCESS_POINT, 'PropertiesChanged', ap_path)
        else:
            self.button.label = 'N: eth' # Assume ethernet

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


_WICD_BUS = _WICD_IFACE = 'org.wicd.daemon'
_WICD_PATH = '/org/wicd/daemon'

class Wicd(object):

    def __init__(self, name='network', colors=None):
        self.button = Button('right', name, colors)
        self.iface = None
        self.conn = None
        _add(self._status_changed, _WICD_IFACE, 'StatusChanged')
        _async_get(self._status_changed, _WICD_IFACE,
                'GetConnectionStatus', _WICD_PATH)

        def click_event(button):
            return Match('RightBarClick', button, self.button.real_name)

        events.bind({
            click_event(_): lambda *a: self._toggle_dialog(name)
        })

    def _toggle_dialog(self, name):
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


# Helpers functions
def _add(func, iface, name, path=None):
    return get_system_bus().add_signal_receiver(
            func, dbus_interface=iface, signal_name=name, path=path)

def _get(path, iface, name):
    obj = get_system_bus().get_object(iface, path)
    return obj.Get(iface, name, dbus_interface=dbus.PROPERTIES_IFACE)

def _async_get(func, iface, name, path):
    obj = get_system_bus().get_object(iface, path)
    getattr(obj, name)(
            dbus_interface=iface,
            reply_handler=lambda args: func(*args),
            error_handler=_)
