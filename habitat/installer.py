# Copyright (C) 2014 Coders at Work
from base import ComponentBase
from environment import SystemEnvironment

import os


class InstallerBase(ComponentBase):
    def is_installed(self):
        return 'installed' in self.metadata and self.metadata['installed']
    def install(self):
        pass

    def _start(self):
        if not self.is_installed():
            self.install()
            self.metadata['installed'] = True


class BrewInstaller(InstallerBase):
    def is_installed(self):
        retcode, _, _ = self.execute(cmd=['brew', 'list', self['brew']])
        return retcode == 0

    def install(self):
        self.execute_or_die(cmd=['brew', 'install', self['brew']])
