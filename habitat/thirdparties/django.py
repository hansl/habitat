# Copyright (C) 2014 Coders at Work
from .. import PythonServer
from .. import PythonCommandLineTool

import os


class DjangoCommand(PythonCommandLineTool):
    tool_bin = '%(django_manage_path)s'
    tool_env = {
        'DJANGO_SETTINGS_MODULE': '%(django_settings)s'
    }

    def __init__(self, command, *args, **kwargs):
        self._args = [command] + list(args)
        super(DjangoCommand, self).__init__(**kwargs)

    def tool_args(self):
        return self._args

    def tool_cwd(self):
        return os.path.dirname(self['django_manage_path'])


class DjangoServer(PythonServer):
    server_bin = '%(django_manage_path)s'
    server_args = ['runserver', '%(host)s:%(port)s']
    server_env = {
        'DJANGO_SETTINGS_MODULE': '%(django_settings)s'
    }

    def server_cwd(self):
        return os.path.dirname(self['django_manage_path'])
