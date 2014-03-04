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
    wait_for_regex = r'Quit the server with CONTROL-C\.$'

    def server_cwd(self):
        return os.path.dirname(self['django_manage_path'])

    # Django commands.
    class Commands(PythonServer.Commands):
        @staticmethod
        def dbshell(component):
            DjangoCommand(
                    'dbshell',
                    name=component.name + '_DbShell',
                    habitat=component.habitat,
                    interactive=True,
                    env=component._env,
                    deps=component.deps
                ).cycle()

        @staticmethod
        def shell(component):
            DjangoCommand(
                    'shell',
                    name=component.name + '_Shell',
                    habitat=component.habitat,
                    interactive=True,
                    env=component._env,
                    deps=component.deps
                ).cycle()

        @staticmethod
        def test(component, *args):
            DjangoCommand(
                    'test', *args,
                    name=component.name + '_Test',
                    habitat=component.habitat,
                    interactive=True,
                    env=component._env,
                    deps=component.deps
                ).cycle()

        @staticmethod
        def raw(component, *args):
            """Execute a raw command by passing all arguments directly to
               manage."""
            DjangoCommand(
                    *args,
                    name=component.name + '_Raw',
                    habitat=component.habitat,
                    interactive=True,
                    env=component._env,
                    deps=component.deps
                ).cycle()
