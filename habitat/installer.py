# Copyright (C) 2014 Coders at Work
from base import ComponentBase
from environment import SystemEnvironment

import os


class InstallerBase(ComponentBase):
    def is_installed(self):
        return 'installed' in self.metadata and self.metadata['installed']
    def install(self):
        pass

    def start(self):
        if not self.is_installed():
            self.install()
            self.metadata['installed'] = True
        super(InstallerBase, self).start()


class BrewInstaller(InstallerBase):
    def is_installed(self):
        stdout, stderr = self._env.execute_or_die('brew', 'search', self['brew'])
        return bool(stdout)

    def install(self):
        self._env.execute_or_die('brew', 'install', self['brew'])
