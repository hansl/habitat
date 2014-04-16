# Copyright (C) 2014 Coders at Work
from base import ComponentBase
from environment import SystemEnvironment
from metadata import MetaDataFile, PythonCommentStorage

from distutils.version import LooseVersion

import json
import os
import re


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
            'pip', 'install', '-q', '--upgrade', '-r%s' % (self['pip_requirement'])])


class BowerUpdater(Updater):
    class KeyValueDefault:
        bower_root = '%(habitat_root)s'

    def version(self):
        with open(self['bower_json_path'], 'r') as fin:
            bower_file = json.load(fin)
        return bower_file['version']

    def update(self):
        root = self['bower_root']
        component = os.path.dirname(self['bower_json_path'])

        # Check if need an install.
        with open(self['bower_json_path'], 'r') as fin:
            bower_file = json.load(fin)

        component_path = os.path.join(self['bower_root'], 'bower_components', bower_file['name'])

        if os.path.isdir(component_path):
            command = 'update'
        else:
            command = 'install'

        self.execute_or_die(cmd=['bower', command, component], cwd=root)
