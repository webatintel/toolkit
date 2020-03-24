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

        self._handle_ops()

    def sync(self):
        self.program.execute_gclient(cmd_type='sync', job_count=1)

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
        gn_args += ' is_clang = false'
        quotation = Util.get_quotation()
        cmd = 'gn --args=%s%s%s gen %s' % (quotation, gn_args, quotation, self.out_dir)
        Util.ensure_dir(self.out_dir)
        Util.info('GN ARGS: {}'.format(gn_args))
        self.program.execute(cmd)

    def build(self):
        if not os.path.exists(self.out_dir):
            self.makefile()
        cmd = 'ninja -k%s -j%s -C %s' % (str(self.build_max_fail), str(Util.CPU_COUNT), self.out_dir)
        self.program.execute(cmd)

    def test(self):
        cmd = '%s/%s%s' % (self.out_dir, self.program.args.test, Util.EXEC_SUFFIX)
        cmd = Util.use_backslash(cmd)
        if not self.test_filter == 'all':
            cmd += ' --gtest_filter=*%s*' % self.test_filter
        self.program.execute(cmd)

    def _parse_args(self):
        parser = argparse.ArgumentParser(description='script for angle',
                                        formatter_class=argparse.RawTextHelpFormatter,
                                        epilog='''
    examples:
    python %(prog)s --sync --build
    ''')
        parser.add_argument('--is-debug', dest='is_debug', help='is debug', action='store_true')
        parser.add_argument('--no-warning-as-error', dest='no_warning_as_error', help='not treat warning as error', action='store_true')
        parser.add_argument('--sync', dest='sync', help='sync', action='store_true')
        parser.add_argument('--makefile', dest='makefile', help='generate makefile', action='store_true')
        parser.add_argument('--build', dest='build', help='build', action='store_true')
        parser.add_argument('--build-max-fail', dest='build_max_fail', help='build keeps going until N jobs fail', type=int, default=1)
        parser.add_argument('--test', dest='test', help='test')
        parser.add_argument('--test-filter', dest='test_filter', help='test filter', default='all')

        self.program = Program(parser)

    def _handle_ops(self):
        args = self.program.args
        if args.sync:
            self.sync()
        if args.makefile:
            self.makefile()
        if args.build:
            self.build()
        if args.test:
            self.test()

if __name__ == '__main__':
    Angle()
