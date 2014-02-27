# Copyright (C) 2014 Coders at Work
from keyvalue import KeyValueStore
from metadata import MetaDataFile

import os
import sys


class ComponentState:
    STOPPED = 0
    RUNNING = 1


class ComponentBase(KeyValueStore):
    _habitat = None
    _state = ComponentState.STOPPED

    def __init__(self, deps=None, env=None, disabled=False, **kwargs):
        super(ComponentBase, self).__init__(**kwargs)
        self._deps = deps or []
        self._env = env
        self._disabled = disabled

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
        return self._state == ComponentState.RUNNING

    def start(self):
        self._state = ComponentState.RUNNING
    def stop(self):
        self._state = ComponentState.STOPPED

    # KeyValue related functions.
    def env(self):
        if self._env:
            return self._env.build_environment()
        else:
            return None

