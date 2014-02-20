# Copyright (C) 2014 Coders at Work
from dictionary import Dictionary
from metadata import MetaDataFile, PythonCommentStorage

from distutils.version import LooseVersion

import os
import sys




class ComponentBase(Dictionary):
    __habitat = None

    def __init__(self, deps=None, env=None, **kwargs):
        self._deps = None
        self._env = env
        super(ComponentBase, self).__init__(**kwargs)

    @property
    def habitat(self):
        return self._habitat
    @habitat.setter
    def habitat(self, value):
        self.parent = value
        self._habitat = value

    @property
    def deps(self):
        return self._deps

    def start(self):
        pass
    def stop(self):
        pass


class Updater(ComponentBase):
    def version(self):
        return '0'
    def update(self):
        pass

    def start(self):
        version = LooseVersion(self.version())
        if 'version' not in self.metadata:
            should_update = True
        else:
            should_update = self.metadata['version'] < version

        if should_update:
            print '[%s] Updating to version: %s.' % (self.name, version)

            self.update()
            self.metadata['version'] = version


class Installer(ComponentBase):
    def is_installed(self):
        return 'installed' in self.metadata and self.metadata['installed']
    def install(self):
        pass

    def start(self):
        if not self.is_installed():
            self.install()
            self.metadata['installed'] = True


class VirtualEnvInstaller(Installer):
    def is_installed(self):
        return os.path.exists(self['virtualenv_root'])
    def install(self):
        self._env.execute_or_die('virtualenv', self['virtualenv_root'])


class PipUpdater(Updater):
    def version(self):
        return MetaDataFile(self['pip_requirement'], storage=PythonCommentStorage)['version']

    def update(self):
        self._env.execute_or_die('pip', 'install', '--upgrade', '-r%s' % (self['pip_requirement']))
