# Copyright (C) 2014 Coders at Work
from base import ComponentBase

import os
import signal


class CommandLineTool(ComponentBase):
    def _start(self, bin=None, args=None, cwd=None, env=None):
        if not bin:
            bin = self['tool_bin']
        if not args:
            if 'tool_args' in self:
                args = self['tool_args']
            else:
                args = []
        if not cwd and 'tool_cwd' in self:
            cwd = self['tool_cwd']
        if not env and 'tool_env' in self:
            env = self['tool_env']
        self.thread, self.process = self._env.execute_or_die(bin,
                                                             cwd=cwd,
                                                             env=env,
                                                             *args)


class PythonCommandLineTool(CommandLineTool):
    def _start(self):
        super(PythonCommandLineTool, self)._start(
            'python', [self['tool_bin']] + list(self['tool_args']))


class JavaCommandLineTool(CommandLineTool):
    def _start(self):
        super(PythonCommandLineTool, self)._start(
            'java', [self['tool_bin']] + list(self['tool_args']))
