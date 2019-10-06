import functools
import json
import os
import threading
import time
import urllib.parse
import uuid
import webbrowser
from wsgiref import simple_server

import requests
from werkzeug import exceptions, routing, utils, wrappers, wsgi

import whim
from whim import api, cookie, settings


class _SilentRequestHandler(simple_server.WSGIRequestHandler):
    def log_message(self, format, *args):
        del format
        del args


class Service(object):
    def __init__(self, *,
                 settings: settings.SectionSettings,
                 cookie: cookie.Cookie,
                 api: api.EditorAPI):
        self._settings = settings
        self._cookie = cookie
        self._api = api
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
                                                   handler_class=_SilentRequestHandler)
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
                    time.sleep(1)
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

    def open_licenses(self):
        webbrowser.open_new_tab(
            'http://localhost:{port}/static/licenses.html'.format(
                port=self.port,
            )
        )

    def route_version(self, request=None) -> str:
        return '{} {}'.format(whim.__name__, whim.__version__)

    def route_cookie(self, request=None) -> str:
        return self._cookie.get_value()

    def route_auth(self, request):
        if self._login_token is not None and request.args.get('login_token') == self._login_token:
            self._login_token = str(uuid.uuid4())  # Prevent reuse.
            response = utils.redirect('/')
            response.set_cookie(
                'login_token',
                self._login_token,
                httponly=True,
                samesite='Strict',
            )
            return response

        raise exceptions.Forbidden()

    def route_edit(self, path, request):
        if request.cookies.get('login_token') != self._login_token:
            raise exceptions.Forbidden()

        request.environ['PATH_INFO'] = '/static/editor.html'
        return self._app

    def route_index(self, request):
        if request.cookies.get('login_token') != self._login_token:
            raise exceptions.Forbidden()

        request.environ['PATH_INFO'] = '/static/welcome.html'
        return self._app

    def route_api(self, endpoint, request):
        if request.cookies.get('login_token') != self._login_token:
            raise exceptions.Forbidden()

        if hasattr(self._api, endpoint):
            request_data = json.loads(request.get_data())
            response_data = getattr(self._api, endpoint)(**request_data)
            return wrappers.Response(
                json.dumps(response_data),
                mimetype='application/json',
            )
        else:
            raise exceptions.NotFound()

    @property
    def _app(self):
        if self.__app is None:
            url_map = routing.Map([
                routing.Rule('/', endpoint='route_index'),
                routing.Rule('/api/<endpoint>', endpoint='route_api'),
                routing.Rule('/auth', endpoint='route_auth'),
                routing.Rule('/cookie', endpoint='route_cookie'),
                routing.Rule('/edit/<path:path>', endpoint='route_edit'),
                routing.Rule('/version', endpoint='route_version'),
            ])

            @wrappers.Request.application
            def app(request):
                adapter = url_map.bind_to_environ(request.environ)
                endpoint, values = adapter.match()
                response = getattr(self, endpoint)(request=request, **values)
                if isinstance(response, str):
                    response = wrappers.Response(
                        response,
                        mimetype='text/plain',
                    )
                return response

            app = wsgi.SharedDataMiddleware(app, {
                '/static': ('whim', 'static'),
            })
            self.__app = app
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
