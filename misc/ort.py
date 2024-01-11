'''
git clone --recursive https://github.com/Microsoft/onnxruntime
install cmake, node.js, python, ninja

[usage]
set PYTHON=C:/Users/ygu5/AppData/Local/Programs/Python/Python311
set PATH=%PYTHON%;%PYTHON%/Scripts;%PATH%
python ort.py --build

[reference]
https://onnxruntime.ai/docs/build/web.html
https://gist.github.com/fs-eire/a55b2c7e10a6864b9602c279b8b75dce
'''

import os
import re
import subprocess
import sys

HOST_OS = sys.platform
if HOST_OS == 'win32':
    lines = subprocess.Popen('dir %s' % __file__.replace('/', '\\'), shell=True, stdout=subprocess.PIPE).stdout.readlines()
    for tmp_line in lines:
        match = re.search(r'\[(.*)\]', tmp_line.decode('utf-8'))
        if match:
            SCRIPT_DIR = os.path.dirname(match.group(1)).replace('\\', '/')
            break
    else:
        SCRIPT_DIR = sys.path[0]
else:
    lines = subprocess.Popen('ls -l %s' % __file__, shell=True, stdout=subprocess.PIPE).stdout.readlines()
    for tmp_line in lines:
        match = re.search(r'.* -> (.*)', tmp_line.decode('utf-8'))
        if match:
            SCRIPT_DIR = os.path.dirname(match.group(1))
            break
    else:
        SCRIPT_DIR = sys.path[0]

sys.path.append(SCRIPT_DIR)
sys.path.append(SCRIPT_DIR + '/..')

from util.base import *

class Ort(Program):
    def __init__(self):
        parser = argparse.ArgumentParser(description='ORT')

        parser.add_argument('--sync', dest='sync', help='sync', action='store_true')
        parser.add_argument('--build', dest='build', help='build', action='store_true')
        parser.add_argument('--build-type', dest='build_type', help='build type, can be Debug, MinSizeRel, Release or RelWithDebInfo', default='MinSizeRel')
        parser.add_argument('--build-skip-wasm', dest='build_skip_wasm', help='build skip wasm', action='store_true')
        parser.add_argument('--build-skip-pull-wasm', dest='build_skip_pull_wasm', help='build skip pull wasm', action='store_true')
        parser.add_argument('--lint', dest='lint', help='lint', action='store_true')

        parser.add_argument('--disable-wasm-simd', dest='disable_wasm_simd', help='disable wasm simd', action='store_true')
        parser.add_argument('--enable-wasm-threads', dest='enable_wasm_threads', help='enable wasm threads', action='store_true')
        parser.add_argument('--disable-wasm-threads', dest='disable_wasm_threads', help='disable wasm threads', action='store_true')
        parser.add_argument('--enable-webgpu', dest='enable_webgpu', help='enable webgpu', action='store_true')
        parser.add_argument('--enable-webnn', dest='enable_webnn', help='enable webnn', action='store_true')

        parser.epilog = '''
examples:
{0} {1} --build
'''.format(Util.PYTHON, parser.prog)

        super().__init__(parser)
        self._handle_ops()

    def sync(self):
        pass

    def build(self):
        timer = Timer()
        root_dir = self.root_dir

        Util.chdir(root_dir, verbose=True)
        if Util.HOST_OS == Util.WINDOWS:
            build_cmd = 'build.bat'
            os_dir = 'Windows'
        else:
            build_cmd = './build.sh'
            os_dir = 'Linux'

        build_type = self.args.build_type
        disable_wasm_simd = self.args.disable_wasm_simd
        if self.args.enable_wasm_threads:
            enable_wasm_threads = True
        elif self.args.disable_wasm_threads:
            enable_wasm_threads = False
        elif Util.HOST_NAME in ['wp-27']:
            enable_wasm_threads = True
        else:
            enable_wasm_threads = False

        if self.args.enable_webnn:
          enable_wasm_threads = False

        if not self.args.build_skip_wasm:
          cmd = f'{build_cmd} --config {build_type} --build_wasm --target onnxruntime_webassembly --skip_tests --parallel --enable_lto --disable_exceptions'
          if not disable_wasm_simd:
            cmd += ' --enable_wasm_simd'
          if enable_wasm_threads:
            cmd += ' --enable_wasm_threads'

          if self.args.enable_webgpu:
            webgpu_cmd = f'{cmd} --use_jsep'
            Util.execute(webgpu_cmd, show_cmd=True, show_duration=True)

          if self.args.enable_webnn:
            webnn_cmd = f'{cmd} --use_webnn'
            Util.execute(webnn_cmd, show_cmd=True, show_duration=True)

        Util.chdir(f'{root_dir}/js', verbose=True)
        Util.execute('npm ci', show_cmd=True)

        Util.chdir(f'{root_dir}/js/common', verbose=True)
        Util.execute('npm ci', show_cmd=True)


        Util.chdir(f'{root_dir}/js/web', verbose=True)
        #Util.execute('npx cross-env ELECTRON_GET_USE_PROXY=true GLOBAL_AGENT_HTTPS_PROXY=http://proxy-us.intel.com:914 npm install -D electron', show_cmd=True)
        Util.execute('npm ci', show_cmd=True)
        if not self.args.build_skip_pull_wasm:
          Util.execute('npm run pull:wasm', show_cmd=True, exit_on_error=False)

        Util.chdir(f'{root_dir}/js/web', verbose=True)
        file_name = 'ort-wasm'
        if not disable_wasm_simd:
            file_name += '-simd'
        if enable_wasm_threads:
            file_name += '-threaded'

        if self.args.enable_webgpu:
          Util.copy_file(f'{root_dir}/build/{os_dir}/{build_type}', f'{file_name}.js', f'{root_dir}/js/web/lib/wasm/binding', f'{file_name}.jsep.js', need_bk=False, show_cmd=True)
          Util.copy_file(f'{root_dir}/build/{os_dir}/{build_type}', f'{file_name}.wasm', f'{root_dir}/js/web/dist', f'{file_name}.jsep.wasm', need_bk=False, show_cmd=True)

        if self.args.enable_webnn:
          Util.copy_file(f'{root_dir}/build/{os_dir}/{build_type}', f'{file_name}.js', f'{root_dir}/js/web/lib/wasm/binding', f'{file_name}.js', need_bk=False, show_cmd=True)
          Util.copy_file(f'{root_dir}/build/{os_dir}/{build_type}', f'{file_name}.wasm', f'{root_dir}/js/web/dist', f'{file_name}.wasm', need_bk=False, show_cmd=True)
          #Util.copy_file(f'{root_dir}/build/{os_dir}/{build_type}', f'{file_name}.worker.js', f'{root_dir}/js/web/lib/wasm/binding', f'{file_name}.worker.js', need_bk=False, show_cmd=True)

        Util.execute('npm run build', show_cmd=True)

        Util.info(f'{timer.stop()} was spent to build')

    def lint(self):
        Util.chdir(f'{self.root_dir}/js', verbose=True)
        Util.execute('npm run lint', show_cmd=True)

    def _handle_ops(self):
        args = self.args
        if args.sync:
            self.sync()
        if args.build:
            self.build()
        if args.lint:
            self.lint()
if __name__ == '__main__':
    Ort()
