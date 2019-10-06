import multiprocessing
import os
import subprocess
import sys
import time
from urllib import parse
import uuid
import webbrowser

import fire

from whim import api, cookie, platform, service, settings


class ServiceProcess(multiprocessing.Process):
    def join(self):
        pass  # Don't actually wait for the child process to exit.


def main(filename=None, *,
         settings_dir='~/.whim',
         restart=False,
         shutdown=False,
         serve_foreground=False,
         licenses=False):
    settings_dir = os.path.expandvars(os.path.expanduser(settings_dir))

    my_settings = settings.Settings(
        settings_dir=settings_dir,
    )

    my_cookie = cookie.Cookie(my_settings.get_section(cookie.__name__))

    my_service = service.Service(
        settings=my_settings.get_section(service.__name__),
        cookie=my_cookie,
        api=api.EditorAPI(),
    )

    if serve_foreground:
        print('starting service')
        my_service.serve_forever()
        return

    if shutdown:
        my_cookie.reset()
        return

    if restart or not my_service.is_running():
        my_cookie.reset()  # Create a fresh cookie so existing services exit.

        # Start the service in a child process.
        ServiceProcess(target=my_service.serve_forever).start()

        # Wait for the service to start.
        for i in range(10):
            print('waiting for the service to start')
            if my_service.is_running():
                print('service has started')
                break
            time.sleep(1)
        else:
            raise RuntimeError('service failed to start')

    if filename is not None:
        filename = os.path.expandvars(os.path.expanduser(filename))
        my_service.open_editor(filename)

    if licenses:
        my_service.open_licenses()


if __name__ == '__main__':
    platform.init()
    fire.Fire(main)
