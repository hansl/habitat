# Copyright (C) 2014 Coders at Work
from base import ComponentBase

import util

import os
import signal


class ServerBase(ComponentBase):
    server_cwd = None

    def _start(self, bin=None, args=None, cwd=None, env=None):
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
        if not 'port' in self:
            raise Exception('Server starting without port...?')
        if util.is_port_in_use(self['port']):
            raise Exception('Port %d for server "%s" already in use.'
                            % (self['port'], self.name))
        self.thread, self.process = self._env.execute(bin,
                                                      cwd=cwd,
                                                      env=env,
                                                      *args)

    def _stop(self):
        try:
            self.process.send_signal(signal.SIGTERM)
        except:
            pass
        self.thread.join()
        self.process = None
        self.thread = None


class PythonServer(ServerBase):
    def _start(self):
        super(PythonServer, self)._start(
            'python', [self['server_bin']] + list(self['server_args']))


class JavaServer(ServerBase):
    def _start(self):
        super(JavaServer, self)._start(
            'java', [self['server_bin']] + list(self['server_args']))
