import dbus
import traceback

from plugins.dbus_instance import get_session_bus
from plugins.dialog import check_dialog, dialog

_BUS = 'org.mpris.MediaPlayer2.spotify'
_PATH = '/org/mpris/MediaPlayer2'
_IFACE = 'org.mpris.MediaPlayer2.Player'

def safe(function):
    def _():
        try:
            function()
        except Exception, e:
            traceback.print_exc(e)
    return _


@safe
def toggle_meta_info():
    if check_dialog(__name__):
        return
    info = spotify_property().Metadata
    artist = ', '.join((s for s in info['xesam:artist']))
    album = info['xesam:album']
    title = info['xesam:title']
    length = long(info['mpris:length']) / 1000000L
    max_width = max(16, len(title), len(album) + 7, len(artist))
    dialog(u'Spotify%0*s\n%s\n%s\n%s\n\n%s'
        % (max_width - 7, '[%02d:%02d]' % (length / 60, length % 60),
           '-' * max_width, artist, album, title) , __name__)


@safe
def play_pause():
    spotify().PlayPause()

@safe
def stop():
    spotify().Stop()

@safe
def prev():
    spotify().Previous()

@safe
def next():
    spotify().Next()

@safe
def quit():
    spotify().Quit()


def spotify():
    return bus().get_interface(_IFACE)

def spotify_property():
    return bus().get_prop_interface(_IFACE)

def bus():
    return get_session_bus(_BUS, _PATH)
