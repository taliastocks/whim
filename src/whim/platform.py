import sys
import webbrowser


def init_cygwin():
    webbrowser.register(
        'cygstart',
        None,
        webbrowser.GenericBrowser('cygstart'),
        -1,
    )


def init():
    if sys.platform == 'cygwin':
        init_cygwin()
