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

        parser.epilog = '''
{0} {1} --batch
'''.format(Util.PYTHON, parser.prog)

        python_ver = Util.get_python_ver()
        if python_ver[0] == 3:
            super().__init__(parser)
        else:
            super(Angle, self).__init__(parser)
        args = self.args

        self.result_dir = '%s/result/%s' % (self.root_dir, self.timestamp)
        self.angle_dir = '%s/angle' % self.root_dir
        self._handle_ops()

    def sync(self):
        cmd = '%s %s --sync --runhooks --root-dir %s' % (Util.PYTHON, Util.GNP_SCRIPT, self.angle_dir)
        self._execute(cmd)

    def build(self):
        cmd = '%s %s --makefile --build --build-target angle_e2e --backup --backup-target angle_e2e --root-dir %s' % (Util.PYTHON, Util.GNP_SCRIPT, self.angle_dir)
        self._execute(cmd)

    def run(self):
        cmd = '%s %s --run --run-target angle_e2e --run-rev latest --root-dir %s' % (Util.PYTHON, Util.GNP_SCRIPT, self.angle_dir)
        result_file = '%s/output.json' % self.result_dir
        run_args = '--gtest_output=json:%s' % result_file
        if self.args.dryrun:
            run_args += ' --gtest_filter=*EGLAndroidFrameBufferTargetTest*'
        cmd += ' --run-args="%s"' % run_args
        self._execute(cmd)
        self.report()

    def report(self):
        if self.args.report:
            self.result_dir = self.args.report

        regression_count = 0
        summary = 'Final summary:\n'
        details = 'Final details:\n'

        for result_file in os.listdir(self.result_dir):
            if result_file in ['exec.log', 'report.txt']:
                continue
            pass_fail, fail_pass, fail_fail, pass_pass = Util.get_test_result('%s/%s' % (self.result_dir, result_file), 'angle')
            regression_count += len(pass_fail)
            result = '%s: PASS_FAIL %s, FAIL_PASS %s, FAIL_FAIL %s PASS_PASS %s\n' % (os.path.splitext(result_file)[0], len(pass_fail), len(fail_pass), len(fail_fail), len(pass_pass))
            summary += result
            if pass_fail:
                result += '[PASS_FAIL]\n%s\n' % '\n'.join(pass_fail[:self.MAX_FAIL_IN_REPORT])
            if fail_pass:
                result += '[FAIL_PASS]\n%s\n' % '\n'.join(fail_pass[:self.MAX_FAIL_IN_REPORT])
            details += result

        Util.info(details)
        Util.info(summary)

        report_file = '%s/report.txt' % self.result_dir
        Util.append_file(report_file, summary)
        Util.append_file(report_file, details)

    def batch(self):
        self.sync()
        self.build()
        self.run()
        self.report()

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
        if args.report:
            self.report()

if __name__ == '__main__':
    Angle()

