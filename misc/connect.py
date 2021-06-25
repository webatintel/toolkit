import os
import platform
import re
import subprocess
import sys

HOST_OS = platform.system().lower()
if HOST_OS == 'windows':
    lines = subprocess.Popen('dir %s' % __file__.replace('/', '\\'), shell=True, stdout=subprocess.PIPE).stdout.readlines()
    for line in lines:
        match = re.search(r'\[(.*)\]', line.decode('utf-8'))
        if match:
            script_dir = os.path.dirname(match.group(1)).replace('\\', '/')
            break
    else:
        script_dir = sys.path[0]
else:
    lines = subprocess.Popen('ls -l %s' % __file__, shell=True, stdout=subprocess.PIPE).stdout.readlines()
    for line in lines:
        match = re.search(r'.* -> (.*)', line.decode('utf-8'))
        if match:
            script_dir = os.path.dirname(match.group(1))
            break
    else:
        script_dir = sys.path[0]

sys.path.append(script_dir)
sys.path.append(script_dir + '/..')

from util.base import * # pylint: disable=unused-wildcard-import


class Connect(Program):
    def __init__(self, parser):
        parser.add_argument('--check', dest='check', help='check')
        parser.add_argument('--connect', dest='connect', help='connect')

        parser.epilog = '''
examples:
  {0} {1} --check wp-27
  {0} {1} --connect wp-27
'''.format(Util.PYTHON, parser.prog)

        python_ver = Util.get_python_ver()
        if python_ver[0] == 3:
            super().__init__(parser)
        else:
            super(Connect, self).__init__(parser)
        self._handle_ops()

    def check(self):
        self._check(self.args.check)

    def _check(self, target_host_name):
        cmd = 'ls'
        if Util.HOST_NAME != target_host_name:
            cmd = Util.remotify_cmd(target_host_name, cmd)
        ret = Util.execute(cmd, timeout=3)
        if ret:
            Util.info('Could not connect to %s' % target_host_name)
            return False
        else:
            Util.info('Could already connect to %s' % target_host_name)
            return True

    def connect(self):
        target_host_name = self.args.connect
        if self._check(target_host_name):
            return True

        cmd = 'cat ~/.ssh/id_rsa.pub | ssh wp@%s \"cat - >>~/.ssh/authorized_keys\"' % target_host_name
        Util.execute(cmd)

    def _handle_ops(self):
        args = self.args
        if args.check:
            self.check()
        if args.connect:
            self.connect()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script for connect')
    Connect(parser)