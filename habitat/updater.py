# Copyright (C) 2014 Coders at Work
from base import ComponentBase
from environment import SystemEnvironment
from metadata import MetaDataFile, PythonCommentStorage

from distutils.version import LooseVersion

import os


class Updater(ComponentBase):
    def version(self):
        return '0'
    def update(self):
        pass

    def _start(self):
        version = self.version()
        if not isinstance(version, LooseVersion):
            version = LooseVersion(version)

        if 'version' not in self.metadata:
            should_update = True
        else:
            should_update = self.metadata['version'] < version

        if should_update:
            print '[%s] Updating to version: %s.' % (self.name, version)

            self.update()
            self.metadata['version'] = version


class PipUpdater(Updater):
    def version(self):
        return MetaDataFile(self['pip_requirement'], storage=PythonCommentStorage)['version']

    def update(self):
        self._env.execute_or_die(cmd=[
            'pip', 'install', '--upgrade', '-r%s' % (self['pip_requirement'])])
