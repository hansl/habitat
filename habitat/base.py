# Copyright (C) 2014 Coders at Work
from keyvalue import KeyValueStore
from metadata import MetaDataFile

import os
import sys


class InvalidComponentState(Exception):
    def __init__(self, name, state):
        super(InvalidComponentState, self).__init__(
            u'Component "%s" is in an invalid state: %s.' % (name, state))


class ComponentState:
    STOPPED = 0
    STARTING = 1
    RUNNING = 2
    STOPPING = 3


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

    def is_running(self):
        return self._state == ComponentState.RUNNING

    def _start(self):
        pass
    def _stop(self):
        pass

    def start(self):
        if self._state == ComponentState.RUNNING:
            return
        if self._disabled:
            return
        if self._state != ComponentState.STOPPED:
            raise InvalidComponentState(self.name, self._state)

        self._state = ComponentState.STARTING
        for dep in self.deps:
            dep.start()
        self._start()
        self._state = ComponentState.RUNNING
    def stop(self):
        if self._state == ComponentState.STOPPED:
            return
        if self._disabled:
            return
        if self._state != ComponentState.RUNNING:
            raise InvalidComponentState(self.name, self._state)
        self._state = ComponentState.STOPPING
        for dep in self.deps:
            dep.stop()
        self._stop()
        self._state = ComponentState.STOPPED

    # KeyValue related functions.
    def env(self):
        if self._env:
            return self._env.build_environment()
        else:
            return None

