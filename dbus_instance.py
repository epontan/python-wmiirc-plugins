import atexit
from threading import Thread, Lock

import gobject
import dbus
from dbus.mainloop.glib import DBusGMainLoop

_DBUS_INSTANCE_LOCK = Lock()
_DBUS_INSTANCE = None

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
        self.system_bus.close()
        self.session_bus.close()
        self.thread.join()


def get_system_bus():
    if _DBUS_INSTANCE is None:
        _init_dbus_instance()
    return _DBUS_INSTANCE.system_bus

def get_session_bus():
    if _DBUS_INSTANCE is None:
        _init_dbus_instance()
    return _DBUS_INSTANCE.session_bus


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
