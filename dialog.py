from pygmi import wmii, call

dialogs = {}

def check_dialog(ref, toggle=True):
    if ref in dialogs:
        dialog = dialogs[ref]
        alive = dialog.poll() is None
        if toggle:
            if alive:
                dialog.terminate()
            del dialogs[ref]
        return alive
    return False


def dialog(message, ref=None, colors=None, font=None, toggle=True):
    if ref and check_dialog(ref, toggle):
        return

    if not colors: colors = wmii.cache['normcolors']
    if not font: font = wmii.cache['font']

    dialog = call('wmiir', 'setsid', 'wmii-dialog',
            '-fn', font,
            '-fg', colors[0],
            '-bg', colors[1],
            '-br', colors[2],
            message, background=True)

    if ref:
        dialogs[ref] = dialog
