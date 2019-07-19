import os
import re
import subprocess
import sys
output = subprocess.Popen('ls -l %s' % __file__, shell=True, stdout=subprocess.PIPE).stdout.readline()
if re.search('->', output):
    output = output.split(' ')[-1].strip()
    match = re.match('/(.)/', output)
    if match:
        drive = match.group(1)
        output = output.replace('/%s/' % drive, '%s:/' % drive)
    chromium_dir = os.path.dirname(os.path.realpath(output))
else:
    chromium_dir = sys.path[0]
sys.path.append(chromium_dir)
sys.path.append(chromium_dir + '/..')

from util.base import * # pylint: disable=unused-wildcard-import
from base import *
from repo import *

class Chromium():
    def __init__(self):
        self._parse_args()
        args = self.program.args

        self.target_arch = args.target_arch
        if self.target_arch == 'default':
            self.target_arch = 'x86_64'

        if args.target_os:
            self.target_os = args.target_os
            if self.target_os == 'default':
                self.target_os = Util.host_os

        if args.rev:
            if re.search('-', args.rev):
                tmp_revs = args.rev.split('-')
                min_rev = tmp_revs[0]
                max_rev = tmp_revs[1]
            else:
                min_rev = args.rev
                max_rev = args.rev

            if '.' in min_rev and '.' not in max_rev or '.' not in min_rev and '.' in max_rev:
                Util.error('min_rev and max_rev should be in same format')

            if '.' in min_rev:
                integer_rev = int(float(min_rev)) + 1
                src_dir = self.program.root_dir + '/src'
                repo = Repo(src_dir, self.program)
                repo.get_info(integer_rev)
                roll_count = repo.info[Repo.INFO_INDEX_REV_INFO][integer_rev][Repo.REV_INFO_INDEX_ROLL_COUNT]
                if roll_count <= 1:
                    Util.error('Rev %s cannot be built as a roll')

                tmp_min = int(min_rev.split('.')[1])
                tmp_max = int(max_rev.split('.')[1])
                for i in range(tmp_min, min(tmp_max + 1, roll_count)):
                    self._process_rev(rev='%s.%s' % (min_rev.split('.')[0], i))
            else:
                min_rev = int(min_rev)
                max_rev = int(max_rev)
                tmp_rev = min_rev
                while tmp_rev <= max_rev:
                    if (int(tmp_rev) % args.rev_stride == 0):
                        self._process_rev(rev=str(tmp_rev))
                        tmp_rev += args.rev_stride
                    else:
                        tmp_rev += 1
            return

        self._process_rev()

    def _parse_args(self):
        parser = argparse.ArgumentParser(description='Script about Chromium',
                                        formatter_class=argparse.RawTextHelpFormatter,
                                        epilog='''
examples:
python %(prog)s --sync -r 678699.1-678699.12 --build
python %(prog)s --sync -r 678699-678720 --rev-stride 10 --build
python %(prog)s --sync --runhooks --makefile --build --backup --download
        ''')

        parser.add_argument('--hash', dest='hash', help='hash of revision for sync')
        parser.add_argument('--is-debug', dest='is_debug', help='is debug', action='store_true')
        parser.add_argument('--no-component-build', dest='no_component_build', help='no component build', action='store_true')
        parser.add_argument('--no-jumbo-build', dest='no_jumbo_build', help='no jumbo build', action='store_true')
        parser.add_argument('--no-warning-as-error', dest='no_warning_as_error', help='not treat warning as error', action='store_true')
        parser.add_argument('--out-dir', dest='out_dir', help='out dir')
        parser.add_argument('-r', '--rev', dest='rev', help='revision for sync')
        parser.add_argument('--rev-stride', dest='rev_stride', help='rev stride', type=int, default=1)
        parser.add_argument('--symbol-level', dest='symbol_level', help='symbol level', type=int, default=0)
        parser.add_argument('--target-arch', dest='target_arch', help='target arch', choices=['x86', 'arm', 'x86_64', 'arm64'], default='default')
        parser.add_argument('--target-os', dest='target_os', help='target os, choices can be android, linux, chromeos, windows, darwin', default='default')

        parser.add_argument('--sync', dest='sync', help='sync to a specific rev if designated, otherwise, sync to upstream', action='store_true')
        parser.add_argument('--sync-reset', dest='sync_reset', help='do a reset before syncing', action='store_true')
        parser.add_argument('--runhooks', dest='runhooks', help='runhooks', action='store_true')
        parser.add_argument('--makefile', dest='makefile', help='generate makefile', action='store_true')
        parser.add_argument('--build', dest='build', help='build', action='store_true')
        parser.add_argument('--build-target', dest='build_target', help='target to build, choices can be chrome, webview_shell, content_shell, chrome_shell, chromedriver, cpu_features, system_webview_apk, android_webview_telemetry_shell_apk, etc.', default='default')
        parser.add_argument('--build-verbose', dest='build_verbose', help='output verbose info. Find log at out/Release/.ninja_log', action='store_true')
        parser.add_argument('--build-max-fail', dest='build_max_fail', help='build keeps going until N jobs fail', type=int, default=1)
        parser.add_argument('--backup', dest='backup', help='backup', action='store_true')
        parser.add_argument('--backup-no-symbol', dest='backup_no_symbol', help='backup no symbol', action='store_true')
        parser.add_argument('--run', dest='run', help='run', action='store_true')
        parser.add_argument('--run-extra-args', dest='run_extra_args', help='run with extra args', default='')
        parser.add_argument('--download', dest='download', help='download', action='store_true')

        self.program = Program(parser)

    def _process_rev(self, rev=''):
        args = self.program.args
        self.base = Base(args.hash, args.is_debug, args.no_component_build, args.no_jumbo_build, args.no_warning_as_error, args.out_dir, self.program, rev, self.program.root_dir, args.symbol_level, self.target_arch, self.target_os)
        self._sync()
        self._runhooks()
        self._makefile()
        self._build()
        self._backup()
        self._run()
        self._download()

    def _sync(self):
        args = self.program.args
        if not args.sync:
            return
        self.base.sync(self.program.args.sync_reset)

    def _runhooks(self):
        args = self.program.args
        if not args.runhooks:
            return
        self.base.runhooks()

    def _makefile(self):
        args = self.program.args
        if not args.makefile:
            return
        self.base.makefile()

    def _build(self):
        args = self.program.args
        if not args.build:
            return
        self.base.build(args.build_max_fail, args.build_target, args.build_verbose)

    def _backup(self):
        args = self.program.args
        if not args.backup:
            return

        self.base.backup(args.backup_no_symbol)

    def _run(self):
        args = self.program.args
        if not args.run:
            return
        self.base.run(args.run_extra_args)

    def _download(self):
        args = self.program.args
        if not args.download:
            return
        self.base.download()

if __name__ == '__main__':
    Chromium()