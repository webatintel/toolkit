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

class Angle(Program):
    def __init__(self):
        parser = argparse.ArgumentParser(description='Chrome Drop ANGLE')

        parser.add_argument('--sync', dest='sync', help='sync', action='store_true')
        parser.add_argument('--build', dest='build', help='build', action='store_true')
        parser.add_argument('--run', dest='run', help='run', action='store_true')
        parser.add_argument('--batch', dest='batch', help='batch', action='store_true')

        parser.add_argument('--run-angle-rev', dest='test_angle_rev', help='ANGLE revision', default='latest')
        parser.add_argument('--run-filter', dest='test_filter', help='WebGL CTS suite to run against', default='all')
        parser.add_argument('--run-verbose', dest='test_verbose', help='verbose mode of run', action='store_true')
        parser.add_argument('--dryrun', dest='dryrun', help='dryrun', action='store_true')
        parser.add_argument('--report', dest='report', help='report file')
        parser.add_argument('--email', dest='email', help='send report as email', action='store_true')

        parser.epilog = '''
python %(prog)s --batch
'''

        python_ver = Util.get_python_ver()
        if python_ver[0] == 3:
            super().__init__(parser)
        else:
            super(Angle, self).__init__(parser)
        args = self.args

        self.angle_dir = '%s/angle' % Util.get_symbolic_link_dir()
        self._handle_ops()

    def sync(self):
        cmd = 'python %s --sync --runhooks --root-dir %s' % (Util.GNP_SCRIPT_PATH, self.angle_dir)
        self._execute(cmd)

    def build(self):
        cmd = 'python %s --makefile --build --build-target angle_e2e --backup --backup-target angle_e2e --root-dir %s' % (Util.GNP_SCRIPT_PATH, self.angle_dir)
        self._execute(cmd)

    def run(self):
        cmd = 'python %s --run --run-target angle_e2e --run-rev latest --root-dir %s' % (Util.GNP_SCRIPT_PATH, self.angle_dir)
        self._execute(cmd)

    def batch(self):
        self.sync()
        self.build()
        self.run()

    def _handle_ops(self):
        args = self.args
        if args.sync:
            self.sync()
        if args.build:
            self.build()
        if args.run:
            self.run()
        if args.batch:
            self.batch()

if __name__ == '__main__':
    Angle()

