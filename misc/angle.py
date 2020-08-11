import os
import re
import subprocess
import sys
lines = subprocess.Popen('dir %s' % __file__, shell=True, stdout=subprocess.PIPE).stdout.readlines()
for line in lines:
    match = re.search('\[(.*)\]', line.decode('utf-8'))
    if match:
        script_dir = os.path.dirname(match.group(1)).replace('\\', '/')
        break
else:
    script_dir = sys.path[0]

sys.path.append(script_dir)
sys.path.append(script_dir + '/..')

from util.base import * # pylint: disable=unused-wildcard-import

class Angle():
    def __init__(self):
        self._parse_args()
        args = self.program.args
        self.args = args

        if args.is_debug:
            build_type = 'debug'
        else:
            build_type = 'release'
        self.out_dir = 'out/%s' % build_type.capitalize()
        self.build_max_fail = args.build_max_fail
        self.test_disabled = args.test_disabled
        self.test_filter = args.test_filter
        self.build_target_dict = {
            'e2e': 'angle_end2end_tests',
            'perf': 'angle_perftests',
            'unit': 'angle_unittests',
        }
        self.backup_target_dict = {
            'e2e': '//src/tests:angle_end2end_tests',
            'perf': '//src/tests:angle_perftests',
            'unit': '//src/tests:angle_unittests',
        }

        self._handle_ops()

    def sync(self):
        self.program.execute('git pull')
        self.program.execute_gclient(cmd_type='sync')

    def runhooks(self):
        self.program.execute_gclient(cmd_type='runhooks')

    def makefile(self):
        args = self.program.args

        if args.is_debug:
            gn_args = 'is_debug=true'
        else:
            gn_args = 'is_debug=false'
        if args.no_warning_as_error:
            gn_args += ' treat_warnings_as_errors=false'
        else:
            gn_args += ' treat_warnings_as_errors=true'
        if args.no_dcheck:
            gn_args += ' dcheck_always_on=false'
        else:
            gn_args += ' dcheck_always_on=true'

        gn_args += ' is_clang=true'
        quotation = Util.get_quotation()
        cmd = 'gn --args=%s%s%s gen %s' % (quotation, gn_args, quotation, self.out_dir)
        Util.ensure_dir(self.out_dir)
        Util.info('GN ARGS: {}'.format(gn_args))
        self.program.execute(cmd)

    def build(self):
        if not os.path.exists(self.out_dir):
            self.makefile()
        cmd = 'ninja -k%s -j%s -C %s' % (str(self.build_max_fail), str(Util.CPU_COUNT), self.out_dir)
        build_target = self.program.args.build_target
        if build_target == 'default':
            tmp_targets = ['']
        else:
            tmp_targets = build_target.split(',')

        for key, value in self.build_target_dict.items():
            if key in tmp_targets:
                tmp_targets[tmp_targets.index(key)] = value

        cmd += ' %s' % ' '.join(tmp_targets)
        self.program.execute(cmd)

    def _test(self, type):
        cmd = '%s%s' % (type, Util.EXEC_SUFFIX)
        if Util.HOST_OS == Util.WINDOWS:
            cmd = Util.use_backslash(cmd)
        if self.test_disabled:
            cmd += ' --gtest_also_run_disabled_tests'
        if not self.test_filter == 'all':
            cmd += ' --gtest_filter=*%s*' % self.test_filter
        if type == 'angle_perftests':
            cmd += ' --one-frame-only'
        if Util.HOST_OS == Util.LINUX:
            cmd = './' + cmd
        self.program.execute(cmd)

    def test(self):
        if Util.HOST_OS == Util.LINUX:
            Util.set_mesa(Util.PROJECT_MESA_BACKUP_DIR, self.args.test_mesa_rev)

        if self.args.test_angle_rev == 'out':
            Util.chdir(self.out_dir, verbose=True)
        else:
            rev_dir, _ = Util.get_backup_dir('%s/backup' % self.program.root_dir, self.args.test_angle_rev)
            Util.chdir('%s/backup/%s/out/Release' % (self.program.root_dir, rev_dir), verbose=True)

        tmp_targets = self.program.args.test_target.split(',')

        for key, value in self.build_target_dict.items():
            if key in tmp_targets:
                tmp_targets[tmp_targets.index(key)] = value

        for target in tmp_targets:
            self._test(target)

    def backup(self):
        Util.backup_gn_target(self.program.root_dir, self.out_dir, target_str=self.args.backup_target, target_dict=self.backup_target_dict, need_symbol=self.program.args.backup_symbol)

    def release(self):
        self.sync()
        self.runhooks()
        self.makefile()
        self.build()
        self.test()

    def _parse_args(self):
        parser = argparse.ArgumentParser(description='script for angle',
                                        formatter_class=argparse.RawTextHelpFormatter,
                                        epilog='''
examples:
python %(prog)s --sync --runhooks --makefile --build --test angle_end2end_tests
''')
        parser.add_argument('--is-debug', dest='is_debug', help='is debug', action='store_true')
        parser.add_argument('--no-warning-as-error', dest='no_warning_as_error', help='not treat warning as error', action='store_true')
        parser.add_argument('--no-dcheck', dest='no_dcheck', help='no dcheck', action='store_true')
        parser.add_argument('--sync', dest='sync', help='sync', action='store_true')
        parser.add_argument('--runhooks', dest='runhooks', help='runhooks', action='store_true')
        parser.add_argument('--makefile', dest='makefile', help='generate makefile', action='store_true')
        parser.add_argument('--build', dest='build', help='build', action='store_true')
        parser.add_argument('--build-target', dest='build_target', help='build target', default='default')
        parser.add_argument('--build-max-fail', dest='build_max_fail', help='build keeps going until N jobs fail', type=int, default=1)
        parser.add_argument('--backup', dest='backup', help='backup', action='store_true')
        parser.add_argument('--backup-target', dest='backup_target', help='backup target', default='e2e')
        parser.add_argument('--backup-symbol', dest='backup_symbol', help='backup symbol', action='store_true')
        parser.add_argument('--test', dest='test', help='test', action='store_true')
        parser.add_argument('--test-target', dest='test_target', help='test target')
        parser.add_argument('--test-disabled', dest='test_disabled', help='test disabled cases', action='store_true')
        parser.add_argument('--test-filter', dest='test_filter', help='test filter', default='all')
        parser.add_argument('--test-angle-rev', dest='test_angle_rev', help='angle revision', default='out')
        parser.add_argument('--test-mesa-rev', dest='test_mesa_rev', help='mesa revision', default='system')

        self.program = Program(parser)

    def _handle_ops(self):
        args = self.program.args
        if args.sync:
            self.sync()
        if args.runhooks:
            self.runhooks()
        if args.makefile:
            self.makefile()
        if args.build:
            self.build()
        if args.backup:
            self.backup()
        if args.test:
            self.test()

if __name__ == '__main__':
    Angle()
