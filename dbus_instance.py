import atexit
from threading import Thread, Lock

import gobject
import dbus
from dbus.mainloop.glib import DBusGMainLoop


class Bus(object):

    def __init__(self, bus, iface, path):
        self.bus = bus
        self.iface = iface
        self.path = path

    def add_callback(self, func, name, iface=None, path=None):
        if iface is None:
            iface = self.iface
        return self.bus.add_signal_receiver(
                func, dbus_interface=iface,
                signal_name=name, path=path)

    def get_interface(self, iface=None, path=None):
        if iface is None:
            iface = self.iface
        if path is None:
            path = self.path
        obj = self.bus.get_object(self.iface, path)
        return dbus.Interface(obj, dbus_interface=iface)

    def get_prop_interface(self, iface=None, path=None):
        if iface is None:
            iface = self.iface
        return Prop(self.get_interface(dbus.PROPERTIES_IFACE, path), iface)


_DBUS_INSTANCE = None
_DBUS_INSTANCE_LOCK = Lock()

class Dbus(object):

    def __init__(self):
        bus_loop = DBusGMainLoop(set_as_default=True)
        gobject.threads_init()
        dbus.mainloop.glib.threads_init()
        self.main_loop = gobject.MainLoop()
        self.thread = Thread(target=self.main_loop.run,
                name='glib_dbus_main_loop')
        self.thread.daemon = True
        self.thread.start()
        self.system_bus = dbus.SystemBus(mainloop=bus_loop)
        self.session_bus = dbus.SessionBus(mainloop=bus_loop)

    def unload(self):
        self.main_loop.quit()
        self.session_bus.close()
        self.system_bus.close()
        self.thread.join()


def get_system_bus(iface, path):
    if _DBUS_INSTANCE is None:
        _init_dbus_instance()
    return Bus(_DBUS_INSTANCE.system_bus, iface, path)

def get_session_bus(iface, path):
    if _DBUS_INSTANCE is None:
        _init_dbus_instance()
    return Bus(_DBUS_INSTANCE.session_bus, iface, path)


def _init_dbus_instance():
    global _DBUS_INSTANCE
    with _DBUS_INSTANCE_LOCK:
        if _DBUS_INSTANCE is not None:
            return
        _DBUS_INSTANCE = Dbus()

@atexit.register
def _unload_dbus_instance():
    global _DBUS_INSTANCE
    with _DBUS_INSTANCE_LOCK:
        if _DBUS_INSTANCE is None:
            return
        _DBUS_INSTANCE.unload()
        _DBUS_INSTANCE = None


_DICT_METHODS = set(('keys', 'iterkeys',
                     'values', 'itervalues',
                     'items', 'iteritems'))

class Prop(object):

    def __init__(self, prop, iface):
        self.prop = prop
        self.iface = iface

    def __getattr__(self, name):
        if name in _DICT_METHODS:
            return getattr(self.prop.GetAll(self.iface), name)
        return self.prop.Get(self.iface, name)

    def __getitem__(self, name):
        return self.prop.Get(self.iface, name)

    def __len__(self):
        return len(self.prop.GetAll(self.iface))

    def __iter__(self):
        return self.prop.GetAll(self.iface).iterkeys()

    def __list__(self):
        return list(self.prop.GetAll(self.iface))

    def __contains__(self, item):
        return item in self.prop.GetAll(self.iface)
