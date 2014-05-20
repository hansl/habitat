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

        if self.get('force_update', False):
            should_update = True
        elif 'version' not in self.metadata:
            should_update = True
        else:
            should_update = self.metadata['version'] < version

        if should_update:
            print '[%s] Updating to version: %s.' % (self.name, version)

            self.update()
            self.metadata['version'] = version

    class Commands(ComponentBase.Commands):
        @staticmethod
        def force_update(component):
            version = component.version()
            if not isinstance(version, LooseVersion):
                version = LooseVersion(version)

            if 'version' not in component.metadata:
                print '[%s] Updating to version: %s.' % (component.name, version)
            else:
                print '[%s] Updating to version: %s (from %s).' % (
                        component.name, version, component.metadata['version'])

            component.update()
            component.metadata['version'] = version


class PipUpdater(Updater):
    def version(self):
        return MetaDataFile(self['pip_requirement'], storage=PythonCommentStorage)['version']

    def update(self):
        self._env.execute_or_die(cmd=[
            'pip', 'install', '--upgrade', '-r%s' % (self['pip_requirement'])])


class NpmUpdater(Updater):
    class KeyValueDefault:
        npm_root = '%(habitat_root)s'
        npm_global = False

    def version(self):
        with open(self['npm_json_path'], 'r') as fin:
            npm_file = json.load(fin)
        return npm_file['version']

    def update(self):
        root = self['npm_root']
        component = os.path.dirname(self['npm_json_path'])

        # Check if need an install.
        with open(self['npm_json_path'], 'r') as fin:
            npm_file = json.load(fin)

        component_path = os.path.join(self['npm_root'], 'npm_components', npm_file['name'])

        if os.path.isdir(component_path):
            command = 'update'
        else:
            command = 'install'

        arguments = [
            '--loglevel=error',
            '--color=false'
        ]
        if self['npm_global']:
            arguments += ['-g']

        self.execute_or_die(
            cmd=['npm', command, component] + arguments,
            cwd=root)


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

        command = 'install'

        self.execute_or_die(cmd=['bower', command, component], cwd=root)
