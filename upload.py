# -*- coding:utf-8 -*-
import os
import sys
import sublime
import sublime_plugin
from .archiver import Archiver
from .settings import API_UPLOAD_URL
from .command import CommandWithStatus

sys.path.append(os.path.dirname(__file__))
import requests


class SublimeSyncUploadCommand(sublime_plugin.ApplicationCommand, CommandWithStatus):

    def __init__(self, *args, **kwargs):
        super(SublimeSyncUploadCommand, self).__init__(*args, **kwargs)
        self.running = False
        self.archive_filename = None

    def post_send(self):
        """
        Resets values
        """
        self.unset_message()
        self.running = False
        self.archive_filename = None

    def prompt_password(self):
        """
        Shows an input panel for entering password
        """
        sublime.active_window().show_input_panel(
            "Enter archive password",
            initial_text='',
            on_done=self.pack_and_send,
            on_cancel=self.pack_and_send,
            on_change=None
        )

    def pack_and_send(self, password=None):
        """
        Create archive and send it to the API
        """
        self.set_message("Creating archive...")

        archiver = Archiver()
        excluded_dir = os.path.relpath(os.path.dirname(__file__), os.path.join(sublime.packages_path(), os.pardir))
        self.archive_filename = archiver.pack_packages(password=password, excluded_dir=excluded_dir)

        self.send_to_api()

    def send_to_api(self):
        """
        Send archive file to API
        """
        self.set_message("Sending archive...")
        f = open(self.archive_filename, 'rb')

        files = {
            'package': f.read(),
            'version': sublime.version()[:1],
            'username': self.username,
            'api_key': self.api_key,
        }

        # Send data and delete temporary file
        response = requests.post(url=API_UPLOAD_URL, files=files)

        f.close()
        os.unlink(self.archive_filename)

        if response.status_code == 200:
            self.set_message("Successfuly sent archive")

        elif response.status_code == 403:
            self.set_message("Error while sending archive: wrong credentials")

        self.post_send()

    def start(self):
        """
        Create an archive of all packages and settings
        """
        settings = sublime.load_settings('sublime-sync.sublime-settings')

        self.running = True
        self.username = settings.get('username', '')
        self.api_key = settings.get('api_key', '')
        self.encrypt = settings.get('encrypt', False)

        if self.encrypt:
            self.prompt_password()
        else:
            self.pack_and_send()

    def run(self, *args):
        if self.running:
            self.set_quick_message("Already working on a backup...")
            return
        sublime.set_timeout_async(self.start, 0)
