import dbus

from plugins.dbus_instance import get_session_bus
from plugins.dialog import check_dialog, dialog

def toggle_meta_info():
    if check_dialog(__name__):
        return
    _spotify_player('GetMetadata', _handle_meta_data_reply)

def _handle_meta_data_reply(info):
    artist = ', '.join((str(s) for s in info['xesam:artist']))
    album = str(info['xesam:album'])
    title = str(info['xesam:title'])
    year = str(info['xesam:contentCreated'])[:4]
    length = long(info['mpris:length']) / 1000000L
    max_width = max(16, len(title), len(album) + 7, len(artist))
    dialog('Spotify%0*s\n%s\n%s\n%s (%s)\n\n%s'
        % (max_width - 7, '[%02d:%02d]' % (length / 60, length % 60),
           '-' * max_width, artist, album, year, title) , __name__)


def play_pause():
    _spotify_player('PlayPause')


def stop():
    _spotify_player('Stop')


def prev():
    _spotify_player('Previous')


def next():
    _spotify_player('Next')


def quit():
    _spotify_player('Quit')


def _spotify_player(method, reply_handler=None):
    if not reply_handler:
        reply_handler = _handle_pass
    try:
        player = get_session_bus().get_object('com.spotify.qt', '/')
        getattr(player, method)(
                dbus_interface='org.freedesktop.MediaPlayer2',
                reply_handler=reply_handler,
                error_handler=_handle_pass)
    except:
        pass

def _handle_pass(*args):
    pass
