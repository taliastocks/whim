import functools
import os
import threading
import time
import urllib.parse
import uuid
import webbrowser
from wsgiref import simple_server

import flask
import requests

import whim
from whim import cookie, settings, static


class SilentRequestHandler(simple_server.WSGIRequestHandler):
    def log_message(self, format, *args):
        del format
        del args


def _requires_auth(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if flask.session.get('authenticated') is True:
            return func(*args, **kwargs)
        else:
            flask.abort(403)

    return wrapper


class Service(object):
    def __init__(self, *,
                 settings: settings.SectionSettings,
                 cookie: cookie.Cookie):
        self._settings = settings
        self._cookie = cookie
        self._login_token = None
        self.__app = None

    @property
    def host(self) -> str:
        return self._settings.get_string('host')

    @property
    def port(self) -> int:
        return self._settings.get_int('port')

    def serve_forever(self):
        '''
        Serve until the cookie expires.
        '''
        # Wait for any existing servers to exit.
        for i in range(10):
            try:
                # Try to create a server. This may fail if the address is in use.
                server = simple_server.make_server(self.host, self.port, self._app,
                                                   handler_class=SilentRequestHandler)
                break
            except OSError:
                print('waiting for port {port} to be free'.format(port=self.port))
                # Address is still in use, try again in a second.
                time.sleep(1)
        else:
            raise RuntimeError('failed to bind to port {port}'.format(port=self.port))

        # Launch the editor and log in the user.
        self._login_token = str(uuid.uuid4())
        webbrowser.open_new_tab('http://localhost:{port}/auth?login_token={login_token}'.format(
            port=self.port,
            login_token=self._login_token,
        ))

        with server as httpd:
            done_serving = False

            def _serve_forever():
                nonlocal done_serving
                while not done_serving:
                    httpd.handle_request()

            # Serve requests until the cookie is expired.
            try:
                for i in range(10):  # Handle requests in a few threads.
                    threading.Thread(target=_serve_forever, daemon=True).start()

                while not self._cookie.is_expired():
                    time.sleep(5)
                print('cookie expired, quitting')
            finally:
                done_serving = True

    def is_running(self) -> bool:
        return self._get_running_version() == self.route_version() and \
            self._get_running_cookie() == self._cookie.get_value()

    def open_editor(self, path: str):
        path = os.path.abspath(path)
        webbrowser.open_new_tab(
            'http://localhost:{port}/edit/{path}'.format(
                port=self.port,
                path=path.lstrip('/'),
            )
        )

    def route_version(self) -> str:
        return '{} {}'.format(whim.__name__, whim.__version__)

    def route_cookie(self) -> str:
        return self._cookie.get_value()

    def route_auth(self):
        if self._login_token is not None and flask.request.args.get('login_token') == self._login_token:
            self._login_token = None  # Prevent reuse.
            flask.session['authenticated'] = True
            return flask.redirect(flask.url_for('.route_index'))

    @_requires_auth
    def route_edit(self, path):
        return self._app.send_static_file('editor.html')

    @_requires_auth
    def route_index(self) -> str:
        return self._app.send_static_file('welcome.html')

    @property
    def _app(self):
        if self.__app is None:
            self.__app = app = flask.Flask(__name__)
            app.secret_key = str(uuid.uuid4())
            app.route('/version')(self.route_version)
            app.route('/cookie')(self.route_cookie)
            app.route('/auth')(self.route_auth)
            app.route('/edit/<path:path>')(self.route_edit)
            app.route('/')(self.route_index)
        return self.__app

    def _get_running_version(self) -> str:
        url = 'http://localhost:{port}/version'.format(port=self.port)
        try:
            return requests.get(url, timeout=1).text
        except (requests.ConnectionError, requests.Timeout):
            return None

    def _get_running_cookie(self) -> str:
        url = 'http://localhost:{port}/cookie'.format(port=self.port)
        try:
            return requests.get(url, timeout=1).text
        except (requests.ConnectionError, requests.Timeout):
            return None
