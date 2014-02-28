# Copyright (C) 2013 Coders at Work
from base import ComponentBase
from keyvalue import KeyValueStore
from dependency import order_dependencies
from environment import NullEnvironment, SystemEnvironment
from executer import Executer
from metadata import MetaDataFile

import util

from collections import OrderedDict

import datetime
import getpass
import inspect
import os
import pty
import re
import select
import subprocess
import sys
import textwrap
import threading


try:
    from Queue import Queue, Empty
except ImportError:
    # python 3.x
    from queue import Queue, Empty


class Habitat(ComponentBase):
    class KeyValueDefault:
        user = getpass.getuser()
        home = os.path.expanduser("~")
        habitat_root = '%(home)s/.habitats/%(habitat_name)s'
        metadata_path = '%(habitat_root)s/metadata'

        base_port = 8000
        host = '127.0.0.1'

    class __ShouldThrow(object):
        pass

    def __init__(self, should_start=True, *args, **kwargs):
        self.executer = Executer()
        self.habitat_name = self.__class__.__name__
        super(Habitat, self).__init__(name='%(habitat_name)s')
        self._args = args
        self._port_map = {}

        # We absolutely need a metadata file.
        metadata_path = self['metadata_path']
        if not os.path.exists(os.path.dirname(metadata_path)):
            os.makedirs(os.path.dirname(metadata_path))
        self.metadata = MetaDataFile(metadata_path)

        for name, component in self.get_all_components().iteritems():
            component.habitat = self
            component.name = name
            if component.name not in self.metadata:
                self.metadata[component.name] = {}
            component.metadata = self.metadata[component.name]

        # If we should start the Habitat, run the first argument as a command.
        if should_start:
            if self._args:
                command = self._args[0]
            else:
                command = 'run'
            self.command(command, *self._args[1:])

    def port(self):
        c = self.get_component_from_stack()
        if not c:
            c = self
        if c not in self._port_map:
            port = self['base_port'] + len(self._port_map.keys())
            while util.is_port_in_use(port):
                port += 1
            self._port_map[c] = port
        return self._port_map[c]

    def command(self, command, *args):
        getattr(self.Commands, command)(self, *args)

    def _start(self):
        for server in self.get_all_components().values():
            server.start()

        self.metadata.storage.save()        

    def wait_if_needed(self):
        # If we are running a component, we wait for a CTRL-C from the user.
        should_wait = False
        for name, component in self.get_all_components().iteritems():
            if component.is_running():
                should_wait = True
                break

        if should_wait:
            print 'Waiting for CTRL-C...'
            try:
                while True:
                    sys.stdin.readlines()
            except KeyboardInterrupt:
                pass

    def _stop(self):
        for name, component in reversed(self.get_all_components().items()):
            if component.is_running():
                component.stop()

        self.metadata.storage.save()        

    def get_all_components(self):
        return {
            name: getattr(self, name)
            for name in dir(self)
            if (not name.startswith('_')
                and hasattr(self, name)
                and isinstance(getattr(self, name), ComponentBase))
        }

    def get_component(self, name):
        if isinstance(name, basestring):
            return self[name]
        if isinstance(name, ComponentBase):
            return name
        raise Exception('Invalid component: %s' % name)

    def get_component_from_stack(self):
        i = 2
        # Get the first stack level out of Habitat
        stack = inspect.stack()[i]
        while 'self' in stack[0].f_locals and isinstance(stack[0].f_locals["self"], Habitat):
            i += 1
            stack = inspect.stack()[i]
        if 'self' in stack[0].f_locals and isinstance(stack[0].f_locals["self"], ComponentBase):
            return stack[0].f_locals["self"]
        return None

    def execute_or_die(self, cmd, env={}, cwd=None, **kwargs):
        """Run a command line tool using an environment and redirecting the
           STDOUT/STDERR to the local logs. Throw an exception if the command
           failed.
        """
        return self.executer.execute_or_die(cmd, env, cwd, **kwargs)

    def execute_in_thread(self, cmd, env={}, cwd=None, **kwargs):
        """Run a command line tool using an environment and redirecting the
           STDOUT/STDERR to the local logs. The tool is ran in a separate
           thread.
        """
        return self.executer.execute_in_thread(cmd, env, cwd, **kwargs)

    def execute_interactive(self, cmd, env={}, cwd=None, **kwargs):
        """Run a command line tool using an environment and redirecting the
           STDOUT/STDERR to the local logs. The tool is ran interactively.
        """
        return self.executer.execute_interactive(cmd, env, cwd, **kwargs)

    class Commands:
        @staticmethod
        def run(habitat, *args):
            """Run a list of components by their names."""
            habitat.start()
            habitat.wait_if_needed()
            habitat.stop()

        @staticmethod
        def show(habitat, *args):
            """Output all variables as they are evaluated in each component
               or the habitat itself.

               Usage: show <variable> <variable...>
            """
            if not args:
                habitat.command('help', 'show')
                return
            for key in args:
                if key in habitat:
                    print '%25s["%s"] == "%s"' % (
                        habitat.habitat_name, key, habitat[key])

                for name, component in habitat.get_all_components().iteritems():
                    if key in component:
                        print '%25s["%s"] == "%s"' % (name, key, component[key])

        @staticmethod
        def help(habitat, *args):
            """Output all accepted commands and their docstring if available.
            """
            print '   Command          Description'
            print '-' * 80
            for method in dir(habitat.Commands):
                if method.startswith('_'):
                    continue
                if args and not method in args:
                    continue

                doc = getattr(habitat.Commands, method).__doc__
                if not doc:
                    print '   %-16s' % (method)
                else:
                    doc = textwrap.fill(doc, 60, subsequent_indent=' ' * 20)
                    print '   %-16s %-60s' % (method, doc)

