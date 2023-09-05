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

        parser.epilog = '''
examples:
{0} {1} --sync --build
'''.format(Util.PYTHON, parser.prog)

        super().__init__(parser)
        self._handle_ops()

    def sync(self):
        pass

    def build(self):
        root_dir = self.root_dir

        Util.chdir(root_dir, verbose=True)
        if Util.HOST_OS == Util.WINDOWS:
            build_cmd = 'build.bat'
        else:
            build_cmd = 'build.sh'
        Util.execute(f'{build_cmd} --config Release --build_wasm --enable_wasm_simd --use_jsep --target onnxruntime_webassembly --skip_tests --parallel')

        Util.chdir(f'{root_dir}/js', verbose=True)
        Util.execute('npm ci')

        Util.chdir(f'{root_dir}/js/common', verbose=True)
        Util.execute('npm ci')


        Util.chdir(f'{root_dir}/js/web', verbose=True)
        Util.execute('npx cross-env ELECTRON_GET_USE_PROXY=true GLOBAL_AGENT_HTTPS_PROXY=http://proxy-us.intel.com:914 npm install -D electron')
        Util.execute('npm ci')
        Util.execute('npm run pull:wasm')

        Util.chdir(f'{root_dir}/js/web', verbose=True)
        Util.copy_file(f'{root_dir}/build/Windows/Release', 'ort-wasm-simd.js', f'{root_dir}/js/web/lib/wasm/binding', 'ort-wasm-simd.jsep.js')
        Util.copy_file(f'{root_dir}/build/Windows/Release', 'ort-wasm-simd.wasm', f'{root_dir}/js/web/dist', 'ort-wasm-simd.jsep.wasm')
        Util.execute('npm run build')


    def _handle_ops(self):
        args = self.args
        if args.sync:
            self.sync()
        if args.build:
            self.build()
if __name__ == '__main__':
    Ort()
