# Copyright (C) 2014 Coders at Work
from component import ComponentBase

import os
import signal


class ServerBase(ComponentBase):
    # server_cwd = None

    def __init__(self, env):
        self._env = env
        super(ServerBase, self).__init__()

    def start(self, bin=None, args=None, cwd=None):
        if not bin:
            bin = self['server_bin']
        if not args:
            args = self['server_args']
        if not cwd:
            cwd = self['server_cwd']
        self.thread, self.process = self._env.execute(bin, *args, cwd=cwd)

    def stop(self):
        try:
            self.process.send_signal(signal.SIGTERM)
        except:
            pass
        self.thread.join()
        self.process = None
        self.thread = None


class PythonServer(ServerBase):
    def start(self):
        super(PythonServer, self).start('python', [self['server_bin']] + list(self['server_args']))


class DjangoServer(PythonServer):
    server_bin = '%(manage_path)s'
    server_args = ['runserver']

    def server_cwd(self):
        return os.path.dirname(self['manage_path'])
