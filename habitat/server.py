# Copyright (C) 2014 Coders at Work
from base import ComponentBase

import util

import datetime
import os
import re
import signal
import time


class ServerBase(ComponentBase):
    server_cwd = None

    def _start(self, bin=None, args=None, cwd=None, env=None, wait_for_regex=None):
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
        if not wait_for_regex and 'wait_for_regex' in self:
            wait_for_regex = self['wait_for_regex']

        stdoutFn = None
        self._waiting = False
        if wait_for_regex:
            self._waiting = True
            def stdoutWait(msg):
                msg = msg.strip()
                if re.search(wait_for_regex, msg):
                    self._waiting = False
                return True
            stdoutFn = stdoutWait

        def cancelFn():
            self._waiting = False

        self.thread, self.process = self.execute_in_thread(cmd=[bin] + args,
                                                           cwd=cwd,
                                                           env=env,
                                                           stdoutFn=stdoutFn,
                                                           errFn=cancelFn)
        timeout = self['timeout']
        startDate = datetime.datetime.now()
        while self._waiting:
            if (datetime.datetime.now() - startDate).total_seconds() > timeout:
                self.process.send_signal(signal.SIGTERM)
                raise Exception('Timing out while starting a server.')
            time.sleep(0.1)

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
