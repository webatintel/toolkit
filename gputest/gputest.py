import os
import platform
import re
import subprocess
import sys

HOST_OS = platform.system().lower()
if HOST_OS == 'windows':
    lines = subprocess.Popen('dir %s' % __file__.replace(
        '/', '\\'), shell=True, stdout=subprocess.PIPE).stdout.readlines()
    for line in lines:
        match = re.search(r'\[(.*)\]', line.decode('utf-8'))
        if match:
            script_dir = os.path.dirname(match.group(1)).replace('\\', '/')
            break
    else:
        script_dir = sys.path[0]
else:
    lines = subprocess.Popen(
        'ls -l %s' % __file__, shell=True, stdout=subprocess.PIPE).stdout.readlines()
    for line in lines:
        match = re.search(r'.* -> (.*)', line.decode('utf-8'))
        if match:
            script_dir = os.path.dirname(match.group(1))
            break
    else:
        script_dir = sys.path[0]

sys.path.append(script_dir)
sys.path.append(script_dir + '/..')

from util.base import *  # pylint: disable=unused-wildcard-import

class GPUTest(Program):
    CHROME_CONFIG_FILES = ['chromium.gpu.fyi.json', 'chromium.dawn.json']
    CHROME_TARGET_VIRTUAL_NAMES = [
        'angle_end2end_tests', # angle_end2end_tests

        'angle_perftests', # angle_perftests

        'dawn_end2end_skip_validation_tests', # dawn_end2end_tests
        'dawn_end2end_tests', # dawn_end2end_tests
        'dawn_end2end_validation_layers_tests', # dawn_end2end_tests
        'dawn_end2end_wire_tests', # dawn_end2end_tests

        'dawn_perf_tests', # dawn_perf_tests

        'gl_tests_passthrough', # gl_tests

        'vulkan_tests', # vulkan_tests

        'info_collection_tests', # telemetry_gpu_integration_test
        'trace_test', # telemetry_gpu_integration_test
        'webgl2_conformance_d3d11_passthrough_tests', # telemetry_gpu_integration_test
        'webgl2_conformance_gl_passthrough_tests', # telemetry_gpu_integration_test
        'webgl2_conformance_validating_tests',   # telemetry_gpu_integration_test, d3d11
        'webgl_conformance_d3d11_passthrough_tests', # telemetry_gpu_integration_test
        'webgl_conformance_d3d9_passthrough_tests', # telemetry_gpu_integration_test
        'webgl_conformance_gl_passthrough_tests', # telemetry_gpu_integration_test
        'webgl_conformance_validating_tests', # telemetry_gpu_integration_test, d3d11
        'webgl_conformance_vulkan_passthrough_tests', # telemetry_gpu_integration_test

        'webgpu_blink_web_tests', # webgpu_blink_web_tests
        'webgpu_blink_web_tests_with_backend_validation', # webgpu_blink_web_tests
    ]

    index = 0
    TARGET_INDEX_OS = index
    index += 1
    TARGET_INDEX_PROJECT = index
    index += 1
    TARGET_INDEX_VIRTUAL_NAME = index
    index += 1
    TARGET_INDEX_REAL_NAME = index
    index += 1
    TARGET_INDEX_RUN_ARGS = index
    index += 1
    TARGET_INDEX_RUN_SHARD = index
    TARGET_INDEX_MAX = index

    CONFIG_FILE = 'config.json'

    def __init__(self):
        parser = argparse.ArgumentParser(description='GPU Test')

        parser.add_argument('--debug', dest='debug', help='debug', action='store_true')
        parser.add_argument('--target', dest='target', help='target', default='all')
        parser.add_argument('--check', dest='check', help='check', action='store_true')
        parser.add_argument('--list', dest='list', help='list', action='store_true')
        parser.add_argument('--sync', dest='sync', help='sync', action='store_true')
        parser.add_argument('--build', dest='build', help='build', action='store_true')
        parser.add_argument('--run', dest='run', help='run', action='store_true')
        parser.add_argument('--run-smoke', dest='run_smoke', help='run smoke tests', action='store_true')

        parser.epilog = '''
python %(prog)s --sync --build --run --target 1-2,4-6,8
'''

        super().__init__(parser)

        self.chromium_dir = '%s/chromium' % self.root_dir
        self.chromium_src_dir = '%s/src' % self.chromium_dir
        target_os = self.target_os
        if target_os == 'default':
            target_os = Util.HOST_OS

        targets = []
        for target in Util.load_json('%s/%s' % (script_dir, self.CONFIG_FILE)):
            if target[self.TARGET_INDEX_OS] == target_os:
                targets.append(target)
        self.targets = targets

        target_indexes = []
        target_str = self.args.target
        if target_str == 'all':
            target_str = '0-%s' % (len(self.targets) - 1)
        targets = target_str.split(',')
        for target in targets:
            if '-' in target:
                tmp_targets = target.split('-')
                target_min = int(tmp_targets[0])
                target_max = int(tmp_targets[1])
                target_indexes.extend(range(target_min, target_max + 1))
            else:
                target_indexes.append(int(target))
        target_indexes = sorted(target_indexes)
        self.target_indexes = target_indexes

        self._handle_ops()

    def check(self):
        targets = []
        recorded_os_virtual_name = []
        if self.args.debug:
            recorded_virtual_name = []

        for config_file in self.CHROME_CONFIG_FILES:
            configs = Util.load_json('%s/testing/buildbot/%s' % (self.chromium_src_dir, config_file))
            for config in configs:
                if not re.search('Intel', config):
                    continue

                if re.search('Linux', config):
                    target_os = Util.LINUX
                elif re.search('Win10', config):
                    target_os = Util.WINDOWS
                else:
                    continue

                if self.args.debug:
                    print(config)

                target_types = configs[config]
                for target_type in target_types:
                    for target_detail in target_types[target_type]:
                        if 'name' in target_detail:
                            tmp_name = target_detail['name']
                        else:
                            tmp_name = ''
                        if 'test' in target_detail:
                            tmp_test = target_detail['test']
                        else:
                            tmp_test = ''
                        if 'isolate_name' in target_detail:
                            tmp_isolate_name = target_detail['isolate_name']
                        else:
                            tmp_isolate_name = ''

                        target_virtual_name = tmp_name or tmp_test
                        target_real_name = tmp_isolate_name or tmp_test or tmp_name

                        if target_virtual_name not in self.CHROME_TARGET_VIRTUAL_NAMES:
                            continue

                        if self.args.debug:
                            print(target_virtual_name)

                        if self.args.debug and target_virtual_name not in recorded_virtual_name:
                            recorded_name.append(target_virtual_name)

                        if [target_os, target_virtual_name] in recorded_os_virtual_name:
                            continue
                        else:
                            recorded_os_virtual_name.append([target_os, target_virtual_name])

                        # init
                        target = [0] * (self.TARGET_INDEX_MAX + 1)
                        target[self.TARGET_INDEX_RUN_SHARD] = 1
                        target[self.TARGET_INDEX_OS] = target_os
                        target[self.TARGET_INDEX_PROJECT] = 'chromium'
                        target[self.TARGET_INDEX_VIRTUAL_NAME] = target_virtual_name
                        target[self.TARGET_INDEX_REAL_NAME] = target_real_name
                        if 'args' in target_detail:
                            target_run_args = target_detail['args']

                        target[self.TARGET_INDEX_RUN_ARGS] = target_run_args
                        if 'swarming' in target_detail and 'shards' in target_detail['swarming']:
                            target[self.TARGET_INDEX_RUN_SHARD] = target_detail['swarming']['shards']

                        targets.append(target)

        os_backends = {
            'windows': ['d3d12', 'dawn_d3d12', 'dawn_vulkan'],
            'linux': ['dawn_vulkan']
        }

        for os in os_backends:
            for backend in os_backends[os]:
                targets.append([os, 'aquarium', 'aquarium_%s' % backend, 'aquarium', ['--test-time 30', '--num-fish 30000', '--enable-msaa', '--turn-off-vsync', '--integrated-gpu', '--window-size=1920,1080', '--print-log', '--backend %s' % backend], 1])

        targets = sorted(targets, key=operator.itemgetter(0, 1, 3, 2))
        config_targets = Util.load_json('%s/%s' % (script_dir, self.CONFIG_FILE))
        if config_targets != targets:
            Util.warning('There is an update of config')
            tmp_config = '%s-%s' % (Util.get_datetime(format='%Y%m%d'), self.CONFIG_FILE)
            Util.ensure_file(tmp_config)
            Util.dump_json(tmp_config, targets)

        if self.args.debug:
            print(len(recorded_virtual_name))
            recorded_virtual_name = sorted(recorded_virtual_name)
            for virtual_name in recorded_virtual_name:
                print(virtual_name)
            for target in targets:
                print(target)

    def list(self):
        for index, target in enumerate(self.targets):
            print('%s: %s' % (index, target[self.TARGET_INDEX_VIRTUAL_NAME]))

    def sync(self):
        projects = []
        for target_index in self.target_indexes:
            project = self.targets[target_index][self.TARGET_INDEX_PROJECT]
            if project not in projects:
                projects.append(project)

        for project in projects:
            cmd = 'python3 %s --root-dir %s/%s --sync --runhooks' % (Util.GNP_SCRIPT_PATH, self.root_dir, project)
            if self._execute(cmd, exit_on_error=False)[0]:
                Util.error('Sync failed')

    def build(self):
        project_targets = {}
        for target_index in self.target_indexes:
            project = self.targets[target_index][self.TARGET_INDEX_PROJECT]
            real_name = self.targets[target_index][self.TARGET_INDEX_REAL_NAME]
            if project not in project_targets:
                project_targets[project] = [real_name]
            elif real_name not in project_targets[project]:
                project_targets[project].append(real_name)

        for project in project_targets:
            cmd = 'python3 %s --out-dir out --root-dir %s/%s --makefile --build --build-target %s' % (Util.GNP_SCRIPT_PATH, self.root_dir, project, ','.join(project_targets[project]))
            if self._execute(cmd, exit_on_error=False)[0]:
                Util.error('Build failed')

    def run(self):
        for target_index in self.target_indexes:
            project = self.targets[target_index][self.TARGET_INDEX_PROJECT]
            virtual_name = self.targets[target_index][self.TARGET_INDEX_VIRTUAL_NAME]
            real_name = self.targets[target_index][self.TARGET_INDEX_REAL_NAME]
            run_args = self.targets[target_index][self.TARGET_INDEX_RUN_ARGS]
            for i in range(len(run_args)):
                run_arg = run_args[i]
                if run_arg.startswith('--extra-browser-args'):
                    run_arg = run_arg.replace('--extra-browser-args=', '')
                    run_args[i] = '--extra-browser-args=\\\"%s --disable-backgrounding-occluded-windows\\\"' % run_arg
                elif run_arg == '--browser=release_x64':
                    run_args[i] = '--browser=release'
                elif run_arg == '-v':
                    run_args[i] = ''
                elif run_arg == '--show-stdout':
                    run_args[i] = ''

            run_args = ' '.join(run_args)
            cmd = 'python3 %s --run --out-dir out --root-dir %s/%s --run-target %s --run-rev out' % (Util.GNP_SCRIPT_PATH, self.root_dir, project, real_name)
            if real_name in ['angle_end2end_tests', 'angle_perftests', 'gl_tests', 'vulkan_tests']:
                run_shard = int(self.targets[target_index][self.TARGET_INDEX_RUN_SHARD])
                for index in range(run_shard):
                    if run_shard > 1:
                        run_args += ' --test-launcher-total-shards=%s --test-launcher-shard-index=%s --test-launcher-summary-output=%s/result/%s/%s.shard%s.json' % (run_shard, index, self.root_dir, self.timestamp, virtual_name, str(index).zfill(2))
                    else:
                        run_args += ' --test-launcher-summary-output=%s/result/%s/%s.json' % (run_shard, index, self.root_dir, self.timestamp, virtual_name)
                    run_args += ' --test-launcher-bot-mode --cfi-diag=0' # undocumented args
                    self._run(cmd, run_args)
            # gtest
            elif real_name in ['dawn_end2end_tests', 'dawn_perf_tests']:
                run_shard = int(self.targets[target_index][self.TARGET_INDEX_RUN_SHARD])
                for index in range(run_shard):
                    if run_shard > 1:
                        run_args += ' --test-launcher-total-shards=%s --test-launcher-shard-index=%s --gtest-output=%s/result/%s/%s.shard%s.json' % (run_shard, index, self.root_dir, self.timestamp, virtual_name, str(index).zfill(2))
                    else:
                        run_args += ' --gtest-output=%s/result/%s/%s.json' % (run_shard, index, self.root_dir, self.timestamp, virtual_name)
                    run_args += ' --test-launcher-bot-mode --cfi-diag=0' # undocumented args
                    self._run(cmd, run_args)
            elif real_name == 'webgpu_blink_web_tests':
                run_shard = int(self.targets[target_index][self.TARGET_INDEX_RUN_SHARD])
                for index in range(run_shard):
                    if run_shard > 1:
                        run_args += ' --total-shards=%s --shard-index=%s --write-full-results-to=%s/result/%s/%s.shard%s.json' % (run_shard, index, self.root_dir, self.timestamp, virtual_name, index.zfill(2))
                    else:
                        run_args += ' --write-full-results-to=%s/result/%s/%s.json' % (self.root_dir, self.timestamp, virtual_name)
                    run_args += '  --isolated-script-test-filter=wpt_internal/webgpu/* --ignore-default-expectations --additional-expectations=../third_party/blink/web_tests/WebGPUExpectations --additional-driver-flag=--enable-unsafe-webgpu --additional-driver-flag=--disable-gpu-sandbox' # undocumented args
                    self._run(cmd, run_args)
            elif real_name == 'telemetry_gpu_integration_test':
                run_shard = int(self.targets[target_index][self.TARGET_INDEX_RUN_SHARD])
                for index in range(run_shard):
                    if run_shard > 1:
                        run_args += ' --total-shards=%s --shard-index=%s --write-full-results-to=%s/result/%s/%s.shard%s.json' % (run_shard, index, self.root_dir, self.timestamp, virtual_name, index.zfill(2))
                    else:
                        run_args += ' --write-full-results-to=%s/result/%s/%s.json' % (self.root_dir, self.timestamp, virtual_name)
                    #run_args += ' --retry-only-retry-on-failure-tests' # undocumented args
                    self._run(cmd, run_args)
            elif real_name == 'aquarium':
                if self.args.run_smoke:
                    run_args += ' --test-time 1'
                lines = self._run(cmd, run_args, return_out=True).split('\n')
                for line in lines:
                    match = re.match('Avg FPS: (.*)', line)
                    if match:
                        print(match.group(1))
                        break
            else:
                self._run(cmd, run_args)

    def _run(self, cmd, run_args, return_out=False):
        cmd += ' --run-args "%s"' % run_args
        ret, out = self._execute(cmd, return_out=return_out, exit_on_error=False, dryrun=False)
        if ret:
            Util.warning('Run failed')
        if return_out:
            return out

    def _handle_ops(self):
        args = self.args
        if args.check:
            self.check()
        if args.list:
            self.list()
        if args.sync:
            self.sync()
        if args.build:
            self.build()
        if args.run:
            self.run()

if __name__ == '__main__':
    GPUTest()
