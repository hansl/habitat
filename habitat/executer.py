# Copyright (C) 2013 Coders at Work
import os
import pty
import re
import select
import subprocess
import sys
import threading


try:
    from Queue import Empty
    from Queue import Queue
except ImportError:
    # python 3.x
    from queue import Empty
    from queue import Queue


class Executer(object):
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
            close_fds=True)
        return (process, (master_out_fd, slave_out_fd), (master_err_fd, slave_err_fd))

    def __exec_thread_main(self, logger, process, stdoutFn=None, stderrFn=None, endFn=None, errFn=None):
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
                        if not stdoutFn or bool(stdoutFn(data)):
                            if logger:
                                logger.info(data)
                            for line in data.rstrip().split('\n'):
                                print 'OUT: %s' % (line,)
                    elif fd == master_err_fd:
                        data = os.read(master_err_fd, 1024)
                        if not stderrFn or bool(stderrFn(data)):
                            if logger:
                                logger.error(data)
                            for line in data.rstrip().split('\n'):
                                print 'ERR: %s' % (line,)

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

    def __exec_thread(self, logger, cmd, env={}, cwd=None, stdoutFn=None, stderrFn=None, **kwargs):
        process = self.__open_process(logger, cmd, env, cwd, **kwargs)
        thread = threading.Thread(
            target=self.__exec_thread_main,
            args=(logger, process, stdoutFn, stderrFn))
        thread.start()
        return (thread, process[0])

    def __exec(self, logger, cmd, env={}, cwd=None, interactive=False, **kwargs):
        # We can use a local variable since we are joining the thread after.
        self.__stdout = []
        self.__stderr = []
        def pipeStdout(msg):
            if interactive:
                sys.stdout.write(msg)
                sys.stdout.flush()
            else:
                for line in msg.split('\n'):
                    sys.stdout.write('>>> %s\n' % (line))
            self.__stdout.append(msg)
        def pipeStderr(msg):
            if interactive:
                sys.stderr.write(msg)
            else:
                for line in msg.split('\n'):
                    sys.stdout.write('ERR %s\n' % (line))
            self.__stderr.append(msg)

        print '... %s' % (cmd,)
        thread, process = self.__exec_thread(
            logger,
            cmd,
            env,
            cwd,
            stdoutFn=pipeStdout,
            stderrFn=pipeStderr,
            **kwargs)
        thread.join()

        stdout = '\n'.join(self.__stdout)
        stderr = '\n'.join(self.__stderr)
        self.__stdout = None
        self.__stderr = None

        print '\n\n'
        return (process.returncode, stdout, stderr)

    def execute(self, cmd, env={}, cwd=None, **kwargs):
        """Run a command line tool using an environment and redirecting the
           STDOUT/STDERR to the local logs. Throw an exception if the command
           failed.
        """
        return self.__exec(kwargs.pop('logger', None), cmd, env=env, cwd=cwd, **kwargs)

    def execute_or_die(self, cmd, env={}, cwd=None, **kwargs):
        """Run a command line tool using an environment and redirecting the
           STDOUT/STDERR to the local logs. Throw an exception if the command
           failed.
        """
        retcode, stdout, stderr = self.__exec(kwargs.pop('logger', None), cmd, env=env, cwd=cwd, **kwargs)
        if retcode != 0:
            raise Exception('Command failed.')
        return stdout, stderr

    def execute_in_thread(self, cmd, env={}, cwd=None, **kwargs):
        """Run a command line tool using an environment and redirecting the
           STDOUT/STDERR to the local logs. The tool is ran in a separate
           thread.
        """
        return self.__exec_thread(kwargs.pop('logger', None), cmd, env, cwd, **kwargs)

    def execute_interactive(self, cmd, env={}, cwd=None, **kwargs):
        """Run a command line tool using an environment and redirecting the
           STDOUT/STDERR to the local logs. The tool is ran interactively.
        """
        return self.__exec(kwargs.pop('logger', None), cmd, env, cwd,
                           interactive=True, **kwargs)

