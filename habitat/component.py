# Copyright (C) 2014 Coders at Work
from dictionary import Dictionary
from metadata import MetaDataFile

import os
import sys


class ComponentBase(Dictionary):
    __habitat = None

    def __init__(self, deps=None, env=None):
        super(ComponentBase, self).__init__()
        self._deps = deps or []
        self._env = env

    @property
    def habitat(self):
        return self._habitat
    @habitat.setter
    def habitat(self, value):
        self.parent = value
        self._habitat = value
        if isinstance(self._env, basestring):
            self._env = self[self._env]

    @property
    def deps(self):
        return self._deps

    def start(self):
        pass
    def stop(self):
        pass

    # Dictionary related functions.
    def env(self):
        return self._env.build_environment()

