# Copyright (C) 2014 Coders at Work
from base import ComponentBase
from environment import SystemEnvironment

import os


BREW_INSTALLER_CELLAR = None


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
        global BREW_INSTALLER_CELLAR
        if not BREW_INSTALLER_CELLAR:
            BREW_INSTALLER_CELLAR, _ = self.execute_or_die(cmd=['brew', '--cellar'])
            BREW_INSTALLER_CELLAR = BREW_INSTALLER_CELLAR.rstrip()
        return os.path.isdir(os.path.join(BREW_INSTALLER_CELLAR, self['brew']))

    def install(self):
        self.execute_or_die(cmd=['brew', 'install', self['brew']])
