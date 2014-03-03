# Copyright (C) 2013 Coders at Work
from base import ComponentBase
from keyvalue import KeyValueStore
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

        timeout = 30

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

    def command(self, name, *args):
        if hasattr(self.Commands, name):
            getattr(self.Commands, name)(self, *args)
        elif (    name in self
              and isinstance(self[name], ComponentBase)
              and len(args) > 0
              and hasattr(self[name].Commands, args[0])):
            component = self[name]
            name, args = args[0], args[1:]
            getattr(component.Commands, name)(component, *args)
        else:
            self.command('help')

    def _start(self):
        for component in self.get_all_components().values():
            component.start()
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

    def execute(self, **kwargs):
        """Run a command line tool using an environment and redirecting the
           STDOUT/STDERR to the local logs. Throw an exception if the command
           failed.
        """
        return self.executer.execute(**kwargs)

    def execute_or_die(self, **kwargs):
        """Run a command line tool using an environment and redirecting the
           STDOUT/STDERR to the local logs. Throw an exception if the command
           failed.
        """
        return self.executer.execute_or_die(**kwargs)

    def execute_in_thread(self, **kwargs):
        """Run a command line tool using an environment and redirecting the
           STDOUT/STDERR to the local logs. The tool is ran in a separate
           thread.
        """
        return self.executer.execute_in_thread(**kwargs)

    def execute_interactive(self, **kwargs):
        """Run a command line tool using an environment and redirecting the
           STDOUT/STDERR to the local logs. The tool is ran interactively.
        """
        return self.executer.execute_interactive(**kwargs)

    class Commands:
        @staticmethod
        def run(habitat, *args):
            """Run a list of components by their names."""
            try:
                habitat.start()
                habitat.wait_if_needed()
            except Exception, ex:
                print ex
            finally:
                habitat.stop(force=True)

        @staticmethod
        def depgraph(habitat, *args):
            """Show the list of dependencies from the habitat."""
            def print_curr_node(tree, depname, level, shown=[]):
                deps = tree[depname]
                print '%s%s' % ('    ' * level, depname)
                for dep in reversed(deps):
                    print_curr_node(tree, dep, level + 1)
                    tree[dep] = []

            all_components = habitat.get_all_components()
            component_tree = {
                    name: [dep.name for dep in component.deps]
                    for name, component in all_components.iteritems()
                }
            all_deps = util.order_dependencies(component_tree)

            for name in reversed(all_deps):
                if component_tree[name]:
                    print_curr_node(component_tree, name, 0)

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
            all_commands = [
                method
                for method in dir(habitat.Commands)
                if not method.startswith('_') and not method in args
            ]
            length = sorted([len(cmd) for cmd in all_commands])[-1] + 4

            format_str = '  %%%ss  %%s' % str(length)
            print format_str % ('Command', 'Description')
            print '-' * (length + 70)
            for method in dir(habitat.Commands):
                if method.startswith('_'):
                    continue
                if args and not method in args:
                    continue

                doc = getattr(habitat.Commands, method).__doc__ or ''
                doc = textwrap.fill(doc, 60, subsequent_indent=' ' * (length + 4))
                print format_str % (method, doc)

