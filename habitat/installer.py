# Copyright (C) 2014 Coders at Work
from component import ComponentBase
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
        super(Installer, self).start()
