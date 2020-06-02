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

        if args.is_debug:
            build_type = 'debug'
        else:
            build_type = 'release'
        self.out_dir = 'out/%s' % build_type.capitalize()
        self.build_max_fail = args.build_max_fail
        self.test_filter = args.test_filter
        self.target_simple_real = {
            'e2e': 'angle_end2end_tests',
            'perf': 'angle_perftests',
            'unit': 'angle_unittests',
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

        gn_args += ' is_clang = true'
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

        for simple, real in self.target_simple_real.items():
            if simple in tmp_targets:
                tmp_targets[tmp_targets.index(simple)] = real

        cmd += ' %s' % ' '.join(tmp_targets)
        self.program.execute(cmd)

    def _test(self, type):
        cmd = '%s%s' % (type, Util.EXEC_SUFFIX)
        cmd = Util.use_backslash(cmd)
        if not self.test_filter == 'all':
            cmd += ' --gtest_filter=*%s*' % self.test_filter
        self.program.execute(cmd)

    def test(self):
        if self.program.args.backup:
            Util.chdir(self.backup_dir, verbose=True)
        else:
            Util.chdir(self.out_dir, verbose=True)

        tmp_targets = self.program.args.test_target.split(',')

        for simple, real in self.target_simple_real.items():
            if simple in tmp_targets:
                tmp_targets[tmp_targets.index(simple)] = real

        for target in tmp_targets:
            self._test(target)

    def backup(self):
        date = self.program.execute('git log -1 --date=format:"%Y%m%d" --format="%ad"', return_out=True)[1].rstrip('\n').rstrip('\r')
        hash1 = self.program.execute('git rev-parse --short HEAD', return_out=True)[1].rstrip('\n').rstrip('\r')
        rev = '%s-%s' % (date, hash1)
        self.rev = rev
        Util.info('Begin to backup rev %s' % rev)
        self.backup_dir = '%s/backup/%s' % (self.program.root_dir, rev)
        if os.path.exists(self.backup_dir):
            Util.info('Backup folder "%s" alreadys exists' % self.backup_dir)
            return

        origin_files = self.program.execute('gn desc //%s //src/tests:angle_end2end_tests runtime_deps' % self.out_dir, return_out=True)[1].rstrip('\n').rstrip('\r').split('\r\n')
        exclude_files = []
        files = []
        for file in origin_files:
            if file.endswith('.pdb'):
                continue

            for exclude_file in exclude_files:
                if file.startswith(exclude_file):
                    break
            else:
                files.append(file)

        Util.chdir(self.out_dir)
        for file in files:
            if re.match(r'\./', file):
                file = file[2:]

            if re.match('initialexe/', file):
                file = file[len('initialexe/'):]

            dir_name = os.path.dirname(file)
            dst_dir = '%s/%s' % (self.backup_dir, dir_name)
            Util.ensure_dir(dst_dir)
            shutil.copy(file, dst_dir)

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
        parser.add_argument('--test', dest='test', help='test', action='store_true')
        parser.add_argument('--test-target', dest='test_target', help='test target')
        parser.add_argument('--test-filter', dest='test_filter', help='test filter', default='all')

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
