# Copyright (C) 2014 Coders at Work
from base import ComponentBase

import os
import sys


DEFAULT_ENVIRONMENT = {
    'IS_HABITAT': 'true'
}


class NullEnvironment(ComponentBase):
    """An empty environment."""
    def build_environment(self):
        return {}
    def find_binary(self, name):
        return None


class EnvironmentBase(ComponentBase):
    _habitat = None

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
        elif self._env:
            return self._env.find_binary(name)
        else:
            return None

    def build_environment(self):
        env = DEFAULT_ENVIRONMENT
        if self._env:
            self._env = self._habitat.get_component(self._env)
            env = dict(self._env.build_environment().items() + env.items())
        return self.extend_environment(env)

    def execute(self, cmd, **kwargs):
        env = kwargs.pop('env', {})
        return self._habitat.execute(
            cmd=[self.find_binary(cmd[0]),] + cmd[1:],
            logger=None,
            env=dict(self.build_environment().items() + env.items()),
            **kwargs
            )
    def execute_in_thread(self, cmd, **kwargs):
        env = kwargs.pop('env', {})
        return self._habitat.execute_in_thread(
            cmd=[self.find_binary(cmd[0]),] + cmd[1:],
            logger=None,
            env=dict(self.build_environment().items() + env.items()),
            **kwargs
            )
    def execute_or_die(self, cmd, *args, **kwargs):
        env = kwargs.pop('env', {})
        return self._habitat.execute_or_die(
            cmd=[self.find_binary(cmd[0]),] + cmd[1:],
            logger=None,
            env=dict(self.build_environment().items() + env.items()),
            **kwargs
            )
    def execute_interactive(self, cmd, *args, **kwargs):
        env = kwargs.pop('env', {})
        return self._habitat.execute_interactive(
            cmd=[self.find_binary(cmd[0]),] + cmd[1:],
            logger=None,
            env=dict(self.build_environment().items() + env.items()),
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

    class Commands(ComponentBase.Commands):
        @staticmethod
        def shell(component):
            """Start a shell in the Space virtual environment."""
            component.start()
            component.execute_interactive(['bash', '-i'])
            component.stop()


class SystemEnvironment(EnvironmentBase):
    """The most basic environment.

    By default, every environment inherits from this one. It is the environment
    in which Habitat itself runs. Not that Habitat itself may run in a
    different environment (or a chroot), and as such this environment might not
    represent the actual System.

    This environment look for binaries in os.environ['PATH'] and inherits all
    variables from os.environ.
    """
    def extend_environment(self, env):
        return dict(env.items() + os.environ.items())
    def binary_path(self, name):
        return [
            os.path.join(path, name)
            for path in os.environ['PATH'].split(os.pathsep)
            if (    os.path.isfile(os.path.join(path, name))
                and os.access(os.path.join(path, name), os.X_OK))
        ]


class ComponentBinHelperMixin(object):
    def binary_path(self, name):
        bin_root = self['bin_root']
        if isinstance(bin_root, basestring):
            bin_root = [bin_root]
        return [
            os.path.join(path, name)
            for path in self.build_environment()['PATH'].split(os.pathsep)
            if (    (os.path.isfile(os.path.join(path, name))
                     or os.path.islink(os.path.join(path, name)))
                and os.access(os.path.join(path, name), os.X_OK))
        ]


class VirtualEnvEnvironment(ComponentBinHelperMixin, EnvironmentBase):
    class KeyValueDefault:
        virtualenv_root = '%(habitat_root)s'
        bin_root = '%(virtualenv_root)s/bin'

    def extend_environment(self, env):
        root = os.path.abspath(self['virtualenv_root'])
        self._path_helper(env, 'PATH', self['bin_root'], prioritize=True)

        site_packages = os.path.join(root, 'lib', 'python%s' % sys.version[:3], 'site-packages')
        self._path_helper(env, 'PYTHONPATH', site_packages, prioritize=True)

        env['VIRTUALENV'] = root
        return env
