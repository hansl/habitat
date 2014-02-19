# Copyright (C) 2013 Coders at Work
from component import ComponentBase
from dictionary import Dictionary
from server import ServerBase

import datetime
import getpass
import inspect
import os
import re
import subprocess
import sys
import threading


class NullHabitat(object):
    def __contains__(self, name):
        raise Exception('Cannot find variable "%s".' % (name,))
    def __getitem__(self, name):
        raise Exception('Cannot find variable "%s".' % (name,))
    def __setitem__(self, name, value):
        raise Exception('Cannot find variable "%s".' % (name,))


class Habitat(Dictionary):
    user = getpass.getuser()
    home = os.path.expanduser("~")
    habitat_root = '%(home)s/.habitats/%(habitat_name)s'

    class __ShouldThrow(object):
        pass

    def __init__(self, should_start=True, *args, **kwargs):
        self.habitat_name = self.__class__.__name__
        super(Habitat, self).__init__()
        self._args = args

        for component in self._components():
            component.habitat = self

        if should_start:
            self._start()

    def _components(self):
        for name in dir(self):
            if name.startswith('_'):
                continue
            value = getattr(self, name)
            if isinstance(value, ComponentBase):
                yield value

    def _start(self):
        if self._args:
            command = self._args[0]
        else:
            command = 'run'
        getattr(self, command)(*self._args[1:])

    def run(self, *args):
        if 0 == len(args):
            self.runall()
            return

        for server in args:
            if isinstance(server, basestring):
                server = self[server]
            server.start()
        print 'Waiting for CTRL-C'
        try:
            while True:
                sys.stdin.readlines()
        except KeyboardInterrupt:
            pass

        for server in args:
            if isinstance(server, basestring):
                server = self[server]
            server.stop()

    def runall(self):
        return self.run(*[
            self[name]
            for name in dir(self)
            if isinstance(getattr(self, name), ServerBase)
            ])

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
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            shell=False,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            **kwargs)
        return process

    def __exec_thread_main(self, logger, process, stdoutFn=None, endFn=None, errFn=None):
        def _stdout(msg, *args):
            if stdoutFn:
                stdoutFn(msg, *args)
            if logger:
                logger.info(msg, *args)
            print 'OUT: ', msg
        def _stderr(msg, *args):
            if logger:
                logger.error(msg, *args)
            print 'ERR: ', msg

        try:
            out = ''
            err = ''
            while process.poll() is None:
                out += process.stdout.read(1024)
                err += process.stdout.read(1024)
                if re.search(r'\n', out):
                    out_lines = out.split('\n')
                    for line in out_lines:
                        _stdout(str(line))
                    if out[-1] == '\n':
                        out = ''
                    else:
                        out = out_lines[-1]

                if re.search(r'\n', err):
                    err_lines = err.split('\n')
                    for line in err_lines:
                        stderr(str(line))
                    if err[-1] == '\n':
                        err = ''
                    else:
                        err = err_lines[-1]

            _stdout('%s' % out.rstrip())
            _stderr('%s' % err.rstrip())

            stdoutdata, stderrdata = process.communicate()
            for out in stdoutdata.split('\n'):
                _stdout('%s' % out.rstrip())
            for err in stderrdata.split('\n'):
                _stderr('%s' % err.rstrip())
        except Exception, e:
            if errFn:
                errFn(e)

        if endFn:
            endFn(process.returncode)

    def __exec_thread(self, logger, cmd, env={}, cwd=None, stdoutFn=None, **kwargs):
        process = self.__open_process(logger, cmd, env, cwd, **kwargs)
        thread = threading.Thread(
            target=self.__exec_thread_main,
            args=(logger, process, stdoutFn))
        thread.start()
        return (thread, process)

    def __exec(self, logger, cmd, env={}, cwd=None, **kwargs):
        self.__stdout = ''
        def pipeStdout(msg, *args):
            self.__stdout += msg % args

        thread, process = self.__exec_thread(
            logger,
            cmd,
            env,
            cwd,
            stdoutFn=pipeStdout,
            **kwargs)
        thread.join()

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
        # component = self.component_from_stack()
        return self.__exec_thread(kwargs.get('logger', None), cmd, env, cwd)

