# Copyright (C) 2014 Coders at Work
from component import ComponentBase

import os
import signal


class CommandLineToolBase(ComponentBase):
    def start(self):
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
        self.thread, self.process = self._env.execute_or_die(bin,
                                                             cwd=cwd,
                                                             env=env,
                                                             *args)
