# Copyright (C) 2014 Coders at Work
from component import ComponentBase
from environment import SystemEnvironment

import os


class Installer(ComponentBase):
    def is_installed(self):
        return 'installed' in self.metadata and self.metadata['installed']
    def install(self):
        pass

    def start(self):
        if not self.is_installed():
            self.install()
            self.metadata['installed'] = True
        super(Installer, self).start()


class VirtualEnvInstaller(Installer):
    def default_env(self):
        return self._habitat.system_env

    def is_installed(self):
        return os.path.exists(self['virtualenv_root'])
    def install(self):
        self._env.execute_or_die('virtualenv', self['virtualenv_root'])


