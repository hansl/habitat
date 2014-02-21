# Copyright (C) 2013 Coders at Work
from component import ComponentBase
from dictionary import Dictionary
from dependency import order_dependencies
from environment import NullEnvironment, SystemEnvironment
from metadata import MetaDataFile
from server import ServerBase

import datetime
import getpass
import inspect
import os
import pty
import re
import select
import subprocess
import sys
import threading


try:
    from Queue import Queue, Empty
except ImportError:
    # python 3.x
    from queue import Queue, Empty


class Habitat(Dictionary):
    system_env = SystemEnvironment()
    null_env = NullEnvironment()
    default_env = SystemEnvironment()

    user = getpass.getuser()
    home = os.path.expanduser("~")
    habitat_root = '%(home)s/.habitats/%(habitat_name)s'
    metadata_path = '%(habitat_root)s/metadata'

    class __ShouldThrow(object):
        pass

    def __init__(self, should_start=True, *args, **kwargs):
        self.habitat_name = self.__class__.__name__
        super(Habitat, self).__init__()
        self._args = args

        metadata_path = self['metadata_path']
        if not os.path.exists(os.path.dirname(metadata_path)):
            os.makedirs(os.path.dirname(metadata_path))
        self.metadata = MetaDataFile(metadata_path)

        all_components = [
            name
            for name in dir(self)
            if (not name.startswith('_')
                and isinstance(getattr(self, name), ComponentBase))
        ]
        for name in all_components:
            component = getattr(self, name)
            component.habitat = self
            if 'name' not in component:
                component.name = name
            if component.name not in self.metadata:
                self.metadata[component.name] = {}
            component.metadata = self.metadata[component.name]

        if should_start:
            if self._args:
                command = self._args[0]
            else:
                command = 'run'
            self.command(command, *self._args[1:])

    def command(self, command, *args):
        getattr(self.Commands, command)(self, *args)

    def _components(self):
        all_components = [
            name
            for name in dir(self)
            if (not name.startswith('_')
                and isinstance(getattr(self, name), ComponentBase))
        ]
        ordered_components = order_dependencies({
                name: (  [dep.name for dep in getattr(self, name).deps]
                       + ([getattr(self, name)._env.name]) if getattr(self, name)._env else [])
                for name in all_components
            })

        for c in ordered_components:
            yield (c, getattr(self, c))


    def _start(self):
        pass

    class Commands:
        @staticmethod
        def run(habitat, *args):
            if 0 == len(args):
                habitat.command('runall')
                return

            for server in args:
                if isinstance(server, basestring):
                    server = habitat[server]
                server.start()

            print 'Waiting for CTRL-C'
            try:
                while True:
                    sys.stdin.readlines()
            except KeyboardInterrupt:
                pass

            for server in args:
                if isinstance(server, basestring):
                    server = habitat[server]
                server.stop()

            habitat.metadata.storage.save()

        @staticmethod
        def runall(habitat):
            if not habitat._components():
                raise Exception('No components registered.')
            habitat.command('run', *[p for n, p in habitat._components()])

    # Execution of commands.
    def __open_process(self, logger, cmd, env, cwd, **kwargs):
        if logger:
            logger.info('Running command: %r' % cmd)
            if env:
                logger.info('With env (showing only all caps):')
                for key, val in env.iteritems():
                    if re.match(r'[A-Z0-9_]+', key):
                        logger.info('  %-20s = %s' % (key,val))
            logger.info('With CWD: %s' % (cwd or os.getcwd()))
            logger.info('-' * 100)

        # provide tty to enable line buffering.
        master_out_fd, slave_out_fd = pty.openpty()
        master_err_fd, slave_err_fd = pty.openpty()

        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            shell=False,
            bufsize=1,
            stderr=slave_err_fd,
            stdout=slave_out_fd,
            close_fds=True,
            **kwargs)
        return (process, (master_out_fd, slave_out_fd), (master_err_fd, slave_err_fd))

    def __exec_thread_main(self, logger, process, stdoutFn=None, endFn=None, errFn=None):
        def _stdout(msg):
            if stdoutFn:
                stdoutFn(msg)
            if logger:
                logger.info(msg)
            print 'OUT: %s' % (msg,)
        def _stderr(msg, *args):
            if logger:
                logger.error(msg, *args)
            print 'ERR: %s' % (msg,)

        try:
            process, out_fd, err_fd = process

            master_out_fd, slave_out_fd = out_fd
            master_err_fd, slave_err_fd = err_fd
            inputs = [master_out_fd, master_err_fd]

            while True:
                readables, _, _ = select.select(inputs, [], [], 0.1)
                for fd in readables:
                    if fd == master_out_fd:
                        data = os.read(master_out_fd, 1024)
                        for line in data.rstrip().split('\n'):
                            _stdout(line)
                    elif fd == master_err_fd:
                        data = os.read(master_err_fd, 1024)
                        for line in data.rstrip().split('\n'):
                            _stderr(line)

                if process.poll() is not None:
                    # We're done.
                    break

        except Exception, e:
            print 'EXCEPTION: ', e
            if errFn:
                errFn(e)

        for fd in inputs + [slave_out_fd, slave_err_fd]:
            os.close(fd)
        process.wait()

        if endFn:
            endFn(process.returncode)

    def __exec_thread(self, logger, cmd, env={}, cwd=None, stdoutFn=None, **kwargs):
        process = self.__open_process(logger, cmd, env, cwd, **kwargs)
        thread = threading.Thread(
            target=self.__exec_thread_main,
            args=(logger, process, stdoutFn))
        thread.start()
        return (thread, process[0])

    def __exec(self, logger, cmd, env={}, cwd=None, **kwargs):
        # We can use a local variable since we are joining the thread after.
        self.__stdout = []
        def pipeStdout(msg):
            self.__stdout.append(msg)

        thread, process = self.__exec_thread(
            logger,
            cmd,
            env,
            cwd,
            stdoutFn=pipeStdout,
            **kwargs)
        thread.join()

        stdout = '\n'.join(self.__stdout)
        self.__stdout = None
        return (process.returncode, stdout)

    def execute_or_die(self, cmd, env={}, cwd=None, **kwargs):
        """Run a command line tool using an environment and redirecting the
           STDOUT/STDERR to the local logs. Throw an exception if the command
           failed.
        """
        retcode, stdout = self.__exec(kwargs.get('logger', None), cmd, env, cwd)
        if retcode != 0:
            raise Exception('Command failed.')
        return stdout

    def execute_in_thread(self, cmd, env={}, cwd=None, **kwargs):
        """Run a command line tool using an environment and redirecting the
           STDOUT/STDERR to the local logs. The tool is ran in a separate
           thread.
        """
        return self.__exec_thread(kwargs.get('logger', None), cmd, env, cwd)

