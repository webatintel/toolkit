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

class Aquarium():
    def __init__(self):
        self._parse_args()
        args = self.program.args

        if args.is_debug:
            build_type = 'debug'
        else:
            build_type = 'release'
        self.out_dir = 'out/%s' % build_type.capitalize()
        self.is_debug = args.is_debug
        self.run_backend = args.run_backend

        self._handle_ops()

    def sync(self):
        self.program.execute('git pull')
        self.program.execute_gclient(cmd_type='sync')

    def makefile(self):
        if self.is_debug:
            args_gn = 'is_debug=true'
        else:
            args_gn = 'is_debug=false'
        quotation = Util.get_quotation()
        cmd = 'gn --args=%s%s%s gen %s' % (quotation, args_gn, quotation, self.out_dir)
        Util.ensure_dir(self.out_dir)
        Util.info('GN ARGS: {}'.format(args_gn))
        self.program.execute(cmd)

    def build(self):
        if not os.path.exists(self.out_dir):
            self.makefile()
        cmd = 'ninja -j%s -C %s aquarium' % (str(Util.CPU_COUNT), self.out_dir)
        self.program.execute(cmd)

    def run(self):
        if self.run_backend == 'default':
            if Util.HOST_OS == 'linux':
                run_backend = 'dawn_vulkan'
            elif Util.HOST_OS == 'windows':
                run_backend = 'dawn_d3d12'
        else:
            run_backend = self.run_backend

        cmd = '%s/aquarium%s --num-fish 30000 --backend %s' % (self.out_dir, Util.EXEC_SUFFIX, run_backend)
        self.program.execute(cmd)

    def _parse_args(self):
        parser = argparse.ArgumentParser(description='script for aquarium',
                                        formatter_class=argparse.RawTextHelpFormatter,
                                        epilog='''
    examples:
    python %(prog)s --sync --build
    ''')
        parser.add_argument('--is-debug', dest='is_debug', help='is debug', action='store_true')
        parser.add_argument('--sync', dest='sync', help='sync', action='store_true')
        parser.add_argument('--makefile', dest='makefile', help='generate makefile', action='store_true')
        parser.add_argument('--build', dest='build', help='build', action='store_true')
        parser.add_argument('--run', dest='run', help='run', action='store_true')
        parser.add_argument('--daily', dest='daily', help='daily', action='store_true')
        parser.add_argument('--run-backend', dest='run_backend', help='run backend', default='default')

        self.program = Program(parser)

    def _handle_ops(self):
        args = self.program.args
        if args.sync:
            self.sync()
        if args.makefile:
            self.makefile()
        if args.build:
            self.build()
        if args.run:
            self.run()
        if args.daily:
            self.sync()
            self.makefile()
            self.build()
            self.run()

if __name__ == '__main__':
    Aquarium()
