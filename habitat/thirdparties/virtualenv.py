# Copyright (C) 2014 Coders at Work
from .. import Installer as InstallerBase

import os

class Installer(InstallerBase):
    virtualenv_root = '%(habitat_root)s/virtualenv'

    def is_installed(self):
        return os.path.exists(self['virtualenv_root'])
    def install(self):
        self._env.execute_or_die('virtualenv', self['virtualenv_root'])
