# Copyright (C) 2014 Coders at Work
from base import ComponentBase

import os
import signal


class CommandLineTool(ComponentBase):
    def _start(self, bin=None, args=None, cwd=None, env=None):
        daemon = False
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

        daemon = 'daemon' in self and self['daemon']
        interactive = 'interactive' in self and self['interactive']

        if daemon:
            self.thread, self.process = self.execute_in_thread(cmd=[bin] + args,
                                                               cwd=cwd,
                                                               env=env,
                                                               interactive=interactive)
        else:
            self.thread, self.process = self.execute_or_die(cmd=[bin] + args,
                                                            cwd=cwd,
                                                            env=env,
                                                            interactive=interactive)

class PythonCommandLineTool(CommandLineTool):
    def _start(self):
        super(PythonCommandLineTool, self)._start(
            'python', [self['tool_bin']] + list(self['tool_args']))


class JavaCommandLineTool(CommandLineTool):
    def _start(self):
        super(PythonCommandLineTool, self)._start(
            'java', [self['tool_bin']] + list(self['tool_args']))
