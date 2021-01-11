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

class Tfjs(Program):
    def __init__(self, parser):
        parser.add_argument('--model', dest='model', help='model', action='store_true')
        parser.add_argument('--build', dest='build', help='build')
        parser.add_argument('--run', dest='run', help='run as http server', action='store_true')
        parser.epilog = '''
examples:
python %(prog)s --provision
python %(prog)s --build --run
'''
        python_ver = Util.get_python_ver()
        if python_ver[0] == 3:
            super().__init__(parser)
        else:
            super(Tfjs, self).__init__(parser)
        args = self.args

        if args.model:
            self.model()
        if args.build:
            self.build()
        if args.run:
            self.run()

    def model(self):
        model_dir = '%s/e2e/benchmarks/local-benchmark/savedmodel' % self.root_dir
        Util.ensure_dir(model_dir)

        files = [
            'posenet/resnet50/float/model-stride32.json',
            'posenet/mobilenet/quant2/075/model-stride16.json',
            'posenet/mobilenet/quant2/075/group1-shard1of1.bin',
        ]
        for i in range(1, 24):
            files.append('posenet/resnet50/float/group1-shard%sof23.bin' % i)

        for file in files:
            file_path = '%s/%s' % (model_dir, file)
            file_path = Util.format_slash(file_path)
            if os.path.exists(file_path):
                continue
            Util.ensure_dir(os.path.dirname(file_path))
            self._execute('%s https://storage.googleapis.com/tfjs-models/savedmodel/%s -O %s' % (ScriptRepo.WGET_FILE, file, file_path))

    def build(self):
        if self.args.build == 'all':
            build_targets = ['core', 'webgpu']
        else:
            build_targets = self.args.build.split(',')

        for target in build_targets:
            if target == 'core':
                Util.chdir('%s/tfjs-core' % self.root_dir)
                self._execute('yarn && yarn tsc && yarn rollup -c --npm')
            elif target == 'webgpu':
                Util.chdir('%s/tfjs-backend-webgpu' % self.root_dir)
                self._execute('yarn && yarn build')

    def run(self):
        Util.chdir(self.root_dir)
        self._execute('npx http-server')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TFJS Script')
    Tfjs(parser)
