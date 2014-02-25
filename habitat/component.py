# Copyright (C) 2014 Coders at Work
from dictionary import Dictionary
from metadata import MetaDataFile

import os
import sys


class ComponentBase(Dictionary):
    class State:
        STOPPED = 0
        RUNNING = 1

    _habitat = None
    _state = State.STOPPED

    def __init__(self, deps=None, env=None, **kwargs):
        super(ComponentBase, self).__init__(**kwargs)
        self._deps = deps or []
        self._env = env

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

    def state(self, state):
        self._state = state
    def is_running(self):
        return self._state

    def start(self):
        self._state = ComponentBase.State.RUNNING
    def stop(self):
        self._state = ComponentBase.State.STOPPED

    # Dictionary related functions.
    def env(self):
        if self._env:
            return self._env.build_environment()
        else:
            return None

