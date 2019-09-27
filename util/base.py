import argparse
import atexit
import calendar
import codecs
import collections
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import fileinput
from functools import wraps
import hashlib
import inspect
import json
import logging
import multiprocessing
from multiprocessing import Pool
import operator
import os
from os.path import expanduser
import pickle
import platform
import random
import re
import select
import shutil
import smtplib
import socket
import subprocess
import sys
import threading
import time

class Util:
    MAX_REV = 9999999
    host_os = platform.system().lower()
    host_os_id = ''
    host_os_release = '0.0'
    if host_os == 'linux':
        result = subprocess.check_output(['cat', '/etc/lsb-release']).decode('utf-8')
        if re.search('CHROMEOS', result[1]):
            host_os = 'chromeos'

    if host_os == 'chromeos':
        host_os_release = platform.platform()
    elif host_os == 'darwin':
        host_os_release = platform.mac_ver()[0]
    elif host_os == 'linux':
        dist = platform.dist()
        host_os_id = dist[0].lower()
        host_os_release = dist[1]
    elif host_os == 'windows':
        host_os_release = platform.version()

    proxy_address = 'child-prc.intel.com'
    proxy_port = '913'
    host_name = socket.gethostname()
    if host_os == 'windows':
        user_name = os.getenv('USERNAME')
    else:
        user_name = os.getenv('USER')
    cpu_count = multiprocessing.cpu_count()

    @staticmethod
    def execute(cmd, show_cmd=True, exit_on_error=True, return_out=False, show_duration=False, dryrun=False, log_file=''):
        orig_cmd = cmd
        if show_cmd:
            Util.cmd(orig_cmd)

        if Util.host_os == 'windows':
            cmd = '%s 2>&1' % cmd
        else:
            cmd = 'bash -o pipefail -c "%s 2>&1' % cmd
        if log_file:
            cmd += ' | tee -a %s' % log_file
        if not Util.host_os == 'windows':
            cmd += '; (exit ${PIPESTATUS})"'

        if show_duration:
            timer = Timer()

        if dryrun:
            result = [0, '']
        elif return_out:
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (out, err) = process.communicate()
            ret = process.returncode
            result = [ret, (out + err).decode('utf-8')]
        else:
            ret = os.system(cmd)
            result = [int(ret / 256), '']

        if show_duration:
            Util.info('%s was spent to execute command "%s" in function "%s"' % (timer.stop(), orig_cmd, inspect.stack()[1][3]))

        if exit_on_error and ret:
            Util.error('Failed to execute command "%s"' % orig_cmd)

        return result

    @staticmethod
    def _msg(msg, show_strace=False):
        m = inspect.stack()[1][3].upper()
        if show_strace:
            m += ', File "%s", Line: %s, Function %s' % inspect.stack()[2][1:4]
        m = '[' + m + '] ' + msg
        print(m)

    @staticmethod
    def info(msg):
        Util._msg(msg)

    @staticmethod
    def warning(msg):
        Util._msg(msg, show_strace=True)

    @staticmethod
    def cmd(msg):
        Util._msg(msg)

    @staticmethod
    def debug(msg):
        Util._msg(msg)

    @staticmethod
    def strace(msg):
        Util._msg(msg)

    @staticmethod
    def error(msg, abort=True, error_code=1):
        Util._msg(msg, show_strace=True)
        if abort:
            quit(error_code)

    @staticmethod
    def chdir(dir_path, verbose=False):
        if verbose:
            Util.info('Enter ' + dir_path)
        os.chdir(dir_path)

    @staticmethod
    def get_dir(path):
        return os.path.split(os.path.realpath(path))[0]

    @staticmethod
    def ensure_dir(dir):
        if not os.path.exists(dir):
            os.makedirs(dir)

    @staticmethod
    def ensure_nodir(dir):
        if os.path.exists(dir):
            shutil.rmtree(dir)

    @staticmethod
    def ensure_file(file_path):
        Util.ensure_dir(os.path.dirname(os.path.abspath(file_path)))
        if not os.path.exists(file_path):
            open(file_path, 'w').close()

    @staticmethod
    def ensure_nofile(file_path):
        if not os.path.exists(file_path):
            return

        os.remove(file_path)

    @staticmethod
    def pkg_installed(pkg):
        cmd = 'dpkg -s ' + pkg
        result = Util.execute(cmd, return_out=True, show_cmd=False)
        if result[0]:
            return False
        else:
            return True

    @staticmethod
    def install_pkg(pkg):
        if Util.pkg_installed(pkg):
            return True
        else:
            Util.info('Package ' + pkg + ' is installing...')
            cmd = 'sudo apt-get install --force-yes -y ' + pkg
            result = Util.execute(cmd)
            if result[0]:
                Util.warning('Package ' + pkg + ' installation failed')
                return False
            else:
                return True

    @staticmethod
    def ensure_pkg(pkgs):
        ret = True
        pkg_list = pkgs.split(' ')
        for pkg in pkg_list:
            ret &= Util.install_pkg(pkg)

        return ret

    @staticmethod
    def read_file(file_path):
        if not os.path.exists(file_path):
            return []

        f = open(file_path)
        lines = [line.rstrip('\n') for line in f]
        if len(lines) > 0:
            while (lines[-1] == ''):
                del lines[-1]
        f.close()
        return lines

    @staticmethod
    def write_file(file_path, lines):
        Util.ensure_file(file_path)
        f = open(file_path, 'w')
        for line in lines:
            f.write(line + '\n')
            print(line)
        f.close()

    @staticmethod
    def use_slash(s):
        return s.replace('\\', '/')

    @staticmethod
    def use_backslash(s):
        return s.replace('/', '\\')

    @staticmethod
    def get_datetime(format='%Y%m%d%H%M%S'):
        return time.strftime(format, time.localtime())

    @staticmethod
    def get_env(env):
        return os.getenv(env)

    @staticmethod
    def set_env(env, value):
        if value:
            os.environ[env] = value

    @staticmethod
    def set_path(extra_path=''):
        path = Util.get_env('PATH')
        if Util.host_os == 'windows':
            splitter = ';'
        elif Util.host_os in ['linux', 'darwin', 'chromeos']:
            splitter = ':'

        paths = path.split(splitter)

        if Util.host_os == 'linux':
            new_paths = ['/usr/bin', '/usr/sbin', '/workspace/project/readonly/depot_tools']
        else:
            new_paths = []

        if extra_path:
            new_paths = extra_path.split(splitter) + new_paths

        for path_new in new_paths:
            if path_new not in paths:
                paths.insert(0, path_new)

        Util.set_env('PATH', splitter.join(paths))

    @staticmethod
    def set_proxy():
        http_proxy = 'http://%s:%s' % (Util.proxy_address, Util.proxy_port)
        https_proxy = 'https://%s:%s' % (Util.proxy_address, Util.proxy_port)
        Util.set_env('http_proxy', http_proxy)
        Util.set_env('https_proxy', https_proxy)

    @staticmethod
    def get_caller_name():
        return inspect.stack()[1][3]

    @staticmethod
    def strace_function(frame, event, arg, indent=[0]):
        file_path = frame.f_code.co_filename
        function_name = frame.f_code.co_name
        file_name = file_path.split('/')[-1]
        if not file_path[:4] == '/usr' and not file_path == '<string>':
            if event == 'call':
                indent[0] += 2
                Util.strace('-' * indent[0] + '> call %s:%s' % (file_name, function_name))
            elif event == 'return':
                Util.strace('<' + '-' * indent[0] + ' exit %s:%s' % (file_name, function_name))
                indent[0] -= 2
        return Util.strace_function

    @staticmethod
    # Get the dir of symbolic link, for example: /workspace/project/chromium instead of /workspace/project/gyagp/share/python
    def get_symbolic_link_dir():
        if sys.argv[0][0] == '/':  # Absolute path
            script_path = sys.argv[0]
        else:
            script_path = os.getcwd() + '/' + sys.argv[0]
        return os.path.split(script_path)[0]

    @staticmethod
    def union_list(a, b):
        return list(set(a).union(set(b)))

    @staticmethod
    def intersect_list(a, b):
        return list(set(a).intersection(set(b)))

    @staticmethod
    def diff_list(a, b):
        return list(set(a).difference(set(b)))

class Timer():
    def __init__(self, microsecond=False):
        self.timer = [0, 0]
        if microsecond:
            self.timer[0] = datetime.datetime.now()
        else:
            self.timer[0] = datetime.datetime.now().replace(microsecond=0)

    def stop(self, microsecond=False):
        if microsecond:
            self.timer[1] = datetime.datetime.now()
        else:
            self.timer[1] = datetime.datetime.now().replace(microsecond=0)

        return self.timer[1] - self.timer[0]

class MainRepo:
    tmp_dir = Util.get_dir(__file__)
    while not os.path.exists(tmp_dir + '/.git'):
        tmp_dir = Util.get_dir(tmp_dir)
    root_dir = Util.use_slash(tmp_dir)
    tool_dir = '%s/tool' % root_dir
    ignore_dir = '%s/ignore' % root_dir
    ignore_log_dir = '%s/log' % ignore_dir
    ignore_timestamp_dir = '%s/timestamp' % ignore_dir
    ignore_chromium_dir = '%s/chromium' % ignore_dir
    ignore_chromium_selfbuilt_dir = '%s/selfbuilt' % ignore_chromium_dir
    ignore_chromium_download_dir = '%s/download' % ignore_chromium_dir
    ignore_chromium_boto_file = '%s/boto.conf' % ignore_chromium_dir

class Program():
    def __init__(self, parser):
        parser.add_argument('--root-dir', dest='root_dir', help='set root directory')
        parser.add_argument('--timestamp', dest='timestamp', help='timestamp')
        parser.add_argument('--log-file', dest='log_file', help='log file')

        parser.add_argument('--extra-path', dest='extra_path', help='extra path for execution, such as path for depot_tools')
        parser.add_argument('--fixed-timestamp', dest='fixed_timestamp', help='fixed timestamp for test sake. We may run multiple tests and results are in same dir', action='store_true')
        parser.add_argument('--strace', dest='strace', help='system trace', action='store_true')

        args = parser.parse_args()

        if args.root_dir:
            root_dir = args.root_dir
        elif os.path.islink(sys.argv[0]):
            root_dir = Util.get_symbolic_link_dir()
        else:
            root_dir = os.path.abspath(os.getcwd())

        if args.timestamp:
            timestamp = args.timestamp
        elif args.fixed_timestamp:
            timestamp = Util.get_datetime(format='%Y%m%d')
        else:
            timestamp = Util.get_datetime()

        if args.log_file:
            log_file = args.log_file
        else:
            script_name = sys.argv[0].split('/')[-1].replace('.py', '')
            log_file = MainRepo.ignore_log_dir + '/' + script_name + '-' + timestamp + '.log'
        Util.info('Log file: %s' % log_file)

        if args.strace:
            sys.settrace(Util.strace_function)

        Util.ensure_dir(root_dir)
        Util.ensure_dir(MainRepo.ignore_timestamp_dir)
        Util.ensure_dir(MainRepo.ignore_log_dir)
        Util.set_path(args.extra_path)

        self.args = args
        self.root_dir = root_dir
        self.timestamp = timestamp
        self.log_file = log_file

    def execute(self, cmd, show_cmd=True, exit_on_error=True, return_out=False, show_duration=False, dryrun=False):
        return Util.execute(cmd=cmd, show_cmd=show_cmd, exit_on_error=exit_on_error, return_out=return_out, show_duration=show_duration, dryrun=dryrun, log_file=self.log_file)
