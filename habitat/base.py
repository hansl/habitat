# Copyright (C) 2014 Coders at Work
from keyvalue import KeyValueStore
from metadata import MetaDataFile

import os
import sys


last_component_id = 0


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
    _name = None
    _env = None

    def __init__(self, habitat=None, deps=None, env=None, disabled=False, **kwargs):
        super(ComponentBase, self).__init__(**kwargs)
        self._deps = deps or []
        self._env = env
        self._disabled = disabled

        global last_component_id
        last_component_id += 1
        self._id = last_component_id

        if habitat:
            self.habitat = habitat

    @property
    def habitat(self):
        return self._habitat
    @habitat.setter
    def habitat(self, value):
        self.parent = value
        self._habitat = value

    @property
    def deps(self):
        if self._env:
            return self._deps + [self._env]
        else:
            return self._deps

    @property
    def name(self):
        if self._name is None:
            return '__%s_%d' % (self.__class__.__name__, self._id)
        return self._name
    @name.setter
    def name(self, value):
        self._name = value
    

    def is_running(self):
        return self._state == ComponentState.RUNNING

    def _start(self):
        pass
    def _stop(self):
        pass

    def cycle(self, force=False):
        self.start(force)
        self.stop()

    def start(self, force=False):
        if self._state == ComponentState.RUNNING:
            return
        if self._disabled and not force:
            return
        if self._state != ComponentState.STOPPED:
            raise InvalidComponentState(self.name, self._state)

        self._state = ComponentState.STARTING
        for dep in self.deps:
            dep.start()

        print 'Starting component "%s"...' % (self.name, )
        self._start()
        self._state = ComponentState.RUNNING
    def stop(self, force=False):
        if self._state == ComponentState.STOPPED:
            return
        if self._state != ComponentState.RUNNING and not force:
            raise InvalidComponentState(self.name, self._state)

        self._state = ComponentState.STOPPING
        for dep in self.deps:
            dep.stop()

        print 'Stopping component "%s"...' % (self.name, )
        self._stop()
        self._state = ComponentState.STOPPED

    def execute(self, **kwargs):
        if self._env is None:
            raise Exception('No environment.')
        return self._env.execute(**kwargs)

    def execute_or_die(self, **kwargs):
        if self._env is None:
            raise Exception('No environment.')
        return self._env.execute_or_die(**kwargs)

    def execute_interactive(self, **kwargs):
        if self._env is None:
            raise Exception('No environment.')
        return self._env.execute_interactive(**kwargs)

    def execute_in_thread(self, **kwargs):
        if self._env is None:
            raise Exception('No environment.')
        return self._env.execute_in_thread(**kwargs)

    # KeyValue related functions.
    def env(self):
        if self._env:
            return self._env.build_environment()
        else:
            return None


class NullComponent(ComponentBase):
    """Component that can be used to simplify the dependency graph. It does
       not implement anything.
    """
    pass

