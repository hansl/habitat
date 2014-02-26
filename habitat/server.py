# Copyright (C) 2014 Coders at Work
from component import ComponentBase

import os
import signal


class ServerBase(ComponentBase):
    server_cwd = None

    def start(self, bin=None, args=None, cwd=None, env=None):
        if not bin:
            bin = self['server_bin']
        if not args:
            if 'server_args' in self:
                args = self['server_args']
            else:
                args = []
        if not cwd and 'server_cwd' in self:
            cwd = self['server_cwd']
        if not env and 'server_env' in self:
            env = self['server_env']
        self.thread, self.process = self._env.execute(bin,
                                                      cwd=cwd,
                                                      env=env,
                                                      *args)
        super(ServerBase, self).start()

    def stop(self):
        try:
            self.process.send_signal(signal.SIGTERM)
        except:
            pass
        self.thread.join()
        self.process = None
        self.thread = None
        super(ServerBase, self).stop()


class PythonServer(ServerBase):
    def start(self):
        super(PythonServer, self).start(
            'python', [self['server_bin']] + list(self['server_args']))


class JavaServer(ServerBase):
    def start(self):
        super(JavaServer, self).start(
            'java', [self['server_bin']] + list(self['server_args']))
