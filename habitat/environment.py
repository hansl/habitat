# Copyright (C) 2014 Coders at Work
from component import ComponentBase
from habitat import NullHabitat

import os
import sys


class NullEnvironment(object):
    """An empty environment."""
    def install(self):
        pass
    def build_environment(self):
        return {}
    def find_binary(self, name):
        return None


class SystemEnvironment(ComponentBase):
    """The most basic environment.

    By default, every environment inherits from this one. It is the environment
    in which Habitat itself runs. Not that Habitat itself may run in a
    different environment (or a chroot), and as such this environment might not
    represent the actual System.

    This environment look for binaries in os.environ['PATH'] and inherits all
    variables from os.environ.
    """
    _parent = NullEnvironment
    def build_environment(self):
        return self.extend_environment({})
    def extend_environment(self, env):
        return dict(env.items() + os.environ.items())
    def find_binary(self, name):
        paths = self.binary_path(name)
        if paths:
            return paths[0]
        else:
            return None
    def binary_path(self, name):
        return [
            os.path.join(path, name)
            for path in os.environ['PATH'].split(os.pathsep)
            if (    os.path.isfile(os.path.join(path, name))
                and os.access(os.path.join(path, name), os.X_OK))
        ]


class EnvironmentBase(ComponentBase):
    _habitat = NullHabitat()
    _parent = NullEnvironment()

    def __init__(self, parent=None, **kwargs):
        if parent:
            self._parent = parent
        super(EnvironmentBase, self).__init__(**kwargs)

    # Used by Habitat.
    def install(self):
        """Create the environment and return."""
        pass
    def is_installed(self):
        return True

    # Interface
    def find_binary(self, name):
        path = self.binary_path(name)
        if path:
            return path[0]
        else:
            return self._parent.find_binary(name)

    def build_environment(self):
        return dict(self.extend_environment(self._parent.build_environment()))
    def execute(self, cmd, *args, **kwargs):
        return self._habitat.execute_in_thread(
            cmd=(self.find_binary(cmd),) + args,
            logger=None,
            env=self.build_environment(),
            **kwargs
            )
    def execute_or_die(self, cmd, *args, **kwargs):
        return self._habitat.execute_or_die(
            cmd=(self.find_binary(cmd),) + args,
            logger=None,
            env=self.build_environment(),
            **kwargs
            )

    # Defined by subclasses.
    def extend_environment(self, env):
        return env
    def binary_path(self, name):
        return []

    # Helpers
    def _path_helper(self, env, name, *args, **kwargs):
        path_list = env.get(name, '').split(os.pathsep)
        if kwargs.get('prioritize', False):
            path_list[0:0] = args
        else:
            path_list += args
        env[name] = os.pathsep.join(path_list)


class ComponentBinHelperMixin(object):
    def binary_path(self, name):
        bin_root = self['bin_root']
        if isinstance(bin_root, basestring):
            bin_root = [bin_root]
        return [
            os.path.join(path, name)
            for path in self.build_environment()['PATH'].split(os.pathsep)
            if (    os.path.isfile(os.path.join(path, name))
                and os.access(os.path.join(path, name), os.X_OK))
        ]


class VirtualEnvEnvironment(ComponentBinHelperMixin, EnvironmentBase):
    # virtualenv_root = '%(habitat_root)s'
    bin_root = '%(virtualenv_root)s/bin'

    def extend_environment(self, env):
        habitat_root = os.path.abspath(self['virtualenv_root'])
        self._path_helper(env, 'PATH', os.path.join(habitat_root, 'bin'), prioritize=True)

        site_packages = os.path.join(habitat_root, 'lib', 'python%s' % sys.version[:3], 'site-packages')
        self._path_helper(env, 'PYTHONPATH', site_packages, prioritize=True)
        return env

