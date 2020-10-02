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

        parser.add_argument('--build', dest='build', help='build', action='store_true')
        parser.add_argument('--build-skip-sync', dest='build_skip_sync', help='skip sync during build', action='store_true')
        parser.add_argument('--build-skip-build-angle', dest='build_skip_build_angle', help='skip building ANGLE during build', action='store_true')
        parser.add_argument('--test', dest='test', help='test', action='store_true')
        parser.add_argument('--test-angle-rev', dest='test_angle_rev', help='ANGLE revision', default='latest')
        parser.add_argument('--test-filter', dest='test_filter', help='WebGL CTS suite to test against', default='all')  # For smoke test, we may use conformance_attribs
        parser.add_argument('--test-verbose', dest='test_verbose', help='verbose mode of test', action='store_true')
        parser.add_argument('--release', dest='release', help='release', action='store_true')
        parser.add_argument('--dryrun', dest='dryrun', help='dryrun', action='store_true')
        parser.add_argument('--report', dest='report', help='report file')
        parser.add_argument('--email', dest='email', help='send report as email', action='store_true')

        parser.epilog = '''
python %(prog)s --release
'''

        super().__init__(parser)
        args = self.args

        self.angle_dir = '%s/angle' % Util.get_symbolic_link_dir()
        self.build_skip_sync = args.build_skip_sync
        self.build_skip_build_angle = args.build_skip_build_angle
        self._handle_ops()

    def build(self):
        Util.chdir(self.angle_dir)
        if not self.build_skip_sync:
            cmd = 'python3 %s --sync --runhooks --root-dir %s' % (Util.GNP_SCRIPT_PATH, self.angle_dir)
            self._execute(cmd, exit_on_error=False)
        Util.ensure_dir('%s/backup' % self.angle_dir)
        if not self.build_skip_build_angle:
            cmd = 'python3 %s --makefile --build --build-target angle_e2e --backup --backup-target angle_e2e --root-dir %s' % (Util.GNP_SCRIPT_PATH, self.angle_dir)
            self._execute(cmd)

    def test(self):
        Util.chdir(self.angle_dir)
        cmd = 'python3 %s --test --test-target angle_e2e --test-rev latest --root-dir %s' % (Util.GNP_SCRIPT_PATH, self.angle_dir)
        self._execute(cmd)

    def release(self):
        self.build()
        if Util.HOST_OS == 'linux':
            for mesa_type in self.mesa_types:
                self.test(mesa_type=mesa_type)
        else:
            self.test()

    def _handle_ops(self):
        args = self.args
        if args.build:
            self.build()
        if args.test:
            self.test()
        if args.release:
            self.release()

if __name__ == '__main__':
    Angle()

