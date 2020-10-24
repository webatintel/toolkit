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
    AQUARIUM_BASE = {
        Util.WINDOWS: {
            'd3d12': 33,
            'dawn_d3d12': 38,
            'dawn_vulkan': 38,
        },
        Util.LINUX: {
            'dawn_vulkan': 50,
        }
    }

    VIRTUAL_NAME_INFO_INDEX_REAL_TYPE = 0
    VIRTUAL_NAME_INFO_INDEX_SMOKE = 1
    VIRTUAL_NAME_INFO = {
        'aquarium_d3d12': ['aquarium', '1'],
        'aquarium_dawn_d3d12': ['aquarium', '1'],
        'aquarium_dawn_vulkan': ['aquarium', '1'],

        'angle_end2end_tests': ['gtest', 'EGLAndroidFrameBufferTargetTest'],
        'angle_perftests': ['gtest', 'BindingsBenchmark'],
        'dawn_end2end_skip_validation_tests': ['gtest', 'BindGroupTests'],
        'dawn_end2end_tests': ['gtest', 'BindGroupTests'],
        'dawn_end2end_validation_layers_tests': ['gtest', 'BindGroupTests'],
        'dawn_end2end_wire_tests': ['gtest', 'BindGroupTests'],
        'dawn_perf_tests': ['gtest', 'BufferUploadPerf.Run/D3D12_Intel'],
        'gl_tests_passthrough': ['gtest', 'SharedImageFactoryTest'],
        'vulkan_tests': ['gtest', 'BasicVulkanTest'],

        'info_collection_tests': ['telemetry_gpu_integration_test', 'InfoCollection_basic'],
        'trace_test': ['telemetry_gpu_integration_test', 'OverlayModeTraceTest_DirectComposition_Underlay_Fullsize'],
        'webgl2_conformance_d3d11_passthrough_tests': ['telemetry_gpu_integration_test', 'conformance/attribs'],
        'webgl2_conformance_gl_passthrough_tests': ['telemetry_gpu_integration_test', 'conformance/attribs'],
        'webgl2_conformance_validating_tests': ['telemetry_gpu_integration_test', 'conformance/attribs'],   # d3d11
        'webgl_conformance_d3d11_passthrough_tests': ['telemetry_gpu_integration_test', 'conformance/attribs'],
        'webgl_conformance_d3d9_passthrough_tests': ['telemetry_gpu_integration_test', 'conformance/attribs'],
        'webgl_conformance_gl_passthrough_tests': ['telemetry_gpu_integration_test', 'conformance/attribs'],
        'webgl_conformance_validating_tests': ['telemetry_gpu_integration_test', 'conformance/attribs'],
        'webgl_conformance_vulkan_passthrough_tests': ['telemetry_gpu_integration_test', 'conformance/attribs'],

        'webgpu_blink_web_tests': ['webgpu_blink_web_tests', ''],
        'webgpu_blink_web_tests_with_backend_validation': ['webgpu_blink_web_tests', ''],
    }

    REAL_TYPE_INFO_INDEX_FILTER = 0
    REAL_TYPE_INFO_INDEX_EXTRA_ARGS = 1
    REAL_TYPE_INFO = {
        'aquarium': ['--test-time', ''],
        'gtest': ['--gtest_filter', '--test-launcher-bot-mode --cfi-diag=0'],
        'telemetry_gpu_integration_test': ['--test-filter', '--retry-limit 1 --retry-only-retry-on-failure-tests'],
        'webgpu_blink_web_tests': ['--gtest_filter', '--isolated-script-test-filter=wpt_internal/webgpu/* --ignore-default-expectations --additional-expectations=../../third_party/blink/web_tests/WebGPUExpectations --additional-driver-flag=--enable-unsafe-webgpu --additional-driver-flag=--disable-gpu-sandbox'],
    }

    CHROME_CONFIG_FILES = ['chromium.gpu.fyi.json', 'chromium.dawn.json']
    CONFIG_FILE = 'config.json'

    index = 0
    TARGET_INDEX_OS = index
    index += 1
    TARGET_INDEX_PROJECT = index
    index += 1
    TARGET_INDEX_VIRTUAL_NAME = index
    index += 1
    TARGET_INDEX_REAL_NAME = index
    index += 1
    TARGET_INDEX_REAL_TYPE = index
    index += 1
    TARGET_INDEX_RUN_ARGS = index
    index += 1
    TARGET_INDEX_RUN_SHARD = index
    TARGET_INDEX_MAX = index

    UNITTEST_PATTERN_FAIL = r'^\d+ test(s?) failed:$'
    UNITTEST_PATTERN_FAIL_EXPECTED = r'^\d+ test(s?) failed as expected:$'
    UNITTEST_PATTERN_CRASH = r'^\d+ test(s?) crashed:$'
    UNITTEST_PATTERN_TIMEOUT = r'^\d+ test(s?) timed out:$'
    UNITTEST_PATTERN_SKIP = r'^\d+ test(s?) not run:$'

    EMAIL_SENDER = 'webgraphics@intel.com'
    EMAIL_ADMIN = 'yang.gu@intel.com'
    EMAIL_TO = 'yang.gu@intel.com'

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
        parser.add_argument('--email', dest='email', help='email', action='store_true')

        parser.epilog = '''
python %(prog)s --sync --build --run --run-smoke --email
'''

        python_ver = Util.get_python_ver()
        if python_ver[0] == 3:
            super().__init__(parser)
        else:
            super(GPUTest, self).__init__(parser)

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
        self.total_target_count = len(target_indexes)
        self.target_index = 1

        self.run_results = []

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

                        virtual_name = tmp_name or tmp_test
                        real_name = tmp_isolate_name or tmp_test or tmp_name

                        if virtual_name not in self.VIRTUAL_NAME_INFO.keys():
                            continue

                        if self.args.debug:
                            print(virtual_name)

                        if self.args.debug and virtual_name not in recorded_virtual_name:
                            recorded_name.append(virtual_name)

                        if [target_os, virtual_name] in recorded_os_virtual_name:
                            continue
                        else:
                            recorded_os_virtual_name.append([target_os, virtual_name])

                        # init
                        target = [0] * (self.TARGET_INDEX_MAX + 1)
                        target[self.TARGET_INDEX_RUN_SHARD] = 1
                        target[self.TARGET_INDEX_OS] = target_os
                        target[self.TARGET_INDEX_PROJECT] = 'chromium'
                        target[self.TARGET_INDEX_VIRTUAL_NAME] = virtual_name
                        target[self.TARGET_INDEX_REAL_NAME] = real_name
                        target[self.TARGET_INDEX_REAL_TYPE] = self.VIRTUAL_NAME_INFO[virtual_name][self.VIRTUAL_NAME_INFO_INDEX_REAL_TYPE]
                        if 'args' in target_detail:
                            target_run_args = target_detail['args']

                        target[self.TARGET_INDEX_RUN_ARGS] = target_run_args
                        if 'swarming' in target_detail and 'shards' in target_detail['swarming']:
                            target[self.TARGET_INDEX_RUN_SHARD] = target_detail['swarming']['shards']

                        targets.append(target)

        # aquarium
        os_backends = {
            'windows': ['d3d12', 'dawn_d3d12', 'dawn_vulkan'],
            'linux': ['dawn_vulkan']
        }
        for os in os_backends:
            for backend in os_backends[os]:
                targets.append([os, 'aquarium', 'aquarium_%s' % backend, 'aquarium', 'aquarium', ['--test-time 30', '--num-fish 30000', '--enable-msaa', '--turn-off-vsync', '--integrated-gpu', '--window-size=1920,1080', '--print-log', '--backend %s' % backend], 1])

        targets = sorted(targets, key=operator.itemgetter(self.TARGET_INDEX_OS, self.TARGET_INDEX_PROJECT, self.TARGET_INDEX_REAL_TYPE, self.TARGET_INDEX_VIRTUAL_NAME))
        config_targets = Util.load_json('%s/%s' % (script_dir, self.CONFIG_FILE))
        if config_targets != targets:
            warning = '[GPUTest] There is an update about config'
            Util.warning(warning)
            if self.args.email:
                Util.send_email(self.EMAIL_SENDER, self.EMAIL_ADMIN, warning, '')
            tmp_config = '%s/%s-%s' % (script_dir, Util.get_datetime(format='%Y%m%d'), self.CONFIG_FILE)
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
            cmd = 'python %s --root-dir %s/%s --sync --runhooks' % (Util.GNP_SCRIPT_PATH, self.root_dir, project)
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
            cmd = 'python %s --root-dir %s/%s --makefile --build --build-target %s' % (Util.GNP_SCRIPT_PATH, self.root_dir, project, ','.join(project_targets[project]))
            if self._execute(cmd, exit_on_error=False)[0]:
                error = '[GPUTest] Project %s build failed' % project
                if self.args.email:
                    Util.send_email(self.EMAIL_SENDER, self.EMAIL_ADMIN, error, '')
                Util.error(error)

    def run(self):
        Util.clear_proxy()
        args = self.args
        self.num_regressions = 0
        for target_index in self.target_indexes:
            project = self.targets[target_index][self.TARGET_INDEX_PROJECT]
            virtual_name = self.targets[target_index][self.TARGET_INDEX_VIRTUAL_NAME]
            real_name = self.targets[target_index][self.TARGET_INDEX_REAL_NAME]
            real_type = self.targets[target_index][self.TARGET_INDEX_REAL_TYPE]
            run_args = self.targets[target_index][self.TARGET_INDEX_RUN_ARGS]
            for i, run_arg in reversed(list(enumerate(run_args))):
                if run_arg.startswith('--extra-browser-args'):
                    run_arg = run_arg.replace('--extra-browser-args=', '')
                    run_args[i] = '--extra-browser-args=\\\"%s --disable-backgrounding-occluded-windows\\\"' % run_arg
                elif run_arg == '--browser=release_x64':
                    run_args[i] = '--browser=release'
                elif run_arg.startswith('--gtest-benchmark-name'):
                    run_args.remove(run_arg)
                elif run_arg in ['-v', '--show-stdout']:
                    run_args.remove(run_arg)
                elif run_arg == '--target=Release_x64':
                    run_args[i] = '--target=release'
                # we use 5912 and 3e98 in test
                elif run_arg == '3e92':
                    run_args[i] = '3e98'

            run_args = ' '.join(run_args)
            cmd = 'python %s --run --root-dir %s/%s --run-target %s --run-rev out' % (Util.GNP_SCRIPT_PATH, self.root_dir, project, real_name)
            run_shard = int(self.targets[target_index][self.TARGET_INDEX_RUN_SHARD])

            if real_type == 'gtest':
                total_shards_arg = '--test-launcher-total-shards'
                shard_index_arg = '--test-launcher-shard-index'
                output_arg = '--gtest_output'
            elif real_type in ['telemetry_gpu_integration_test', 'webgpu_blink_web_tests']:
                total_shards_arg = '--total-shards'
                shard_index_arg = '--shard-index'
                output_arg = '--write-full-results-to'

            for shard_index in range(run_shard):
                if not args.run_smoke and run_shard > 1:
                    output_file = '%s/result/%s/%s.shard%s.json' % (self.root_dir, self.timestamp, virtual_name, str(shard_index).zfill(2))
                    run_args += ' %s=%s %s=%s' % (total_shards_arg, run_shard, shard_index_arg, shard_index)
                else:
                    output_file = '%s/result/%s/%s.json' % (self.root_dir, self.timestamp, virtual_name)
                    smoke = self.VIRTUAL_NAME_INFO[virtual_name][self.VIRTUAL_NAME_INFO_INDEX_SMOKE]
                    if args.run_smoke and smoke:
                        if real_type != 'aquarium':
                            smoke = '*%s*' % smoke
                        run_args += ' %s=%s' % (self.REAL_TYPE_INFO[real_type][self.REAL_TYPE_INFO_INDEX_FILTER], smoke)

                # output
                if real_type != 'aquarium':
                    run_args += ' %s=' % output_arg
                    if real_type == 'gtest':
                        run_args += 'json:'
                    run_args += output_file
                    Util.ensure_file(output_file)

                run_args += ' %s' % self.REAL_TYPE_INFO[real_type][self.REAL_TYPE_INFO_INDEX_EXTRA_ARGS]
                self._run(virtual_name, real_type, cmd, run_args, output_file)
                if args.run_smoke:
                    break

        subject = '[GPUTest] Test on %s has %s Regressions' % (self.timestamp, self.num_regressions)

        for run_result in [subject] + self.run_results:
            print(run_result)

        Util.write_file('%s/result/%s/all.log' % (self.root_dir, self.timestamp), [subject] + self.run_results, mode='a+')

        if self.args.email:
            Util.send_email(self.EMAIL_SENDER, self.EMAIL_TO, subject, self.run_results)

    def _run(self, virtual_name, real_type, cmd, run_args, output_file=''):
        cmd += ' --run-args "%s"' % run_args
        if real_type in ['aquarium', 'gtest']:
            return_out = True
        else:
            return_out = False
        test_timer = Timer()
        ret, out = self._execute(cmd, return_out=return_out, exit_on_error=False, dryrun=False)
        test_timer.stop()

        if real_type == 'aquarium':
            if self.args.debug:
                print(out)
            lines = out.split('\r\n')
            for line in lines:
                match = re.match('Avg FPS: (.*)', line)
                if match:
                    run_fps = int(match.group(1))
                    backend = virtual_name.replace('aquarium_', '')
                    base_fps = self.AQUARIUM_BASE[Util.HOST_OS][backend]
                    if run_fps < base_fps:
                        change_type = 'REGRESSION'
                        num_regressions = 1
                    elif run_fps == base_fps:
                        change_type = 'NOCHANGE'
                        num_regressions = 0
                    else:
                        change_type = 'IMPROVEMENT'
                        num_regressions = 0
                    self.num_regressions += num_regressions
                    run_result = '%s: %s -> %s' % (change_type, base_fps, run_fps)
                    break
        elif real_type == 'gtest':
            if self.args.debug:
                print(out)
            lines = out.split('\r\n')
            error_type = ''
            results = {}
            num_regressions = 0
            for line in lines:
                if error_type:
                    match = re.match(r'^(.+) \(.+:\d+\)$', line)
                    if match:
                        if error_type in ['PASS_FAIL', 'CRASH', 'TIMEOUT']:
                            self.num_regressions += 1
                        if error_type not in results:
                            results[error_type] = [match.group(1)]
                        else:
                            results[error_type].append(match.group(1))
                        continue

                if re.match(self.UNITTEST_PATTERN_FAIL, line):
                    error_type = 'PASS_FAIL'
                elif re.match(self.UNITTEST_PATTERN_FAIL_EXPECTED, line):
                    error_type = 'FAIL_FAIL'
                elif re.match(self.UNITTEST_PATTERN_CRASH, line):
                    error_type = 'CRASH'
                elif re.match(self.UNITTEST_PATTERN_TIMEOUT, line):
                    error_type = 'TIMEOUT'
                elif re.match(self.UNITTEST_PATTERN_SKIP, line):
                    error_type = 'SKIP'

            run_result = ''
            for error_type in results:
                run_result += '[%s]\n%s' % (error_type, '\n'.join(results[error_type]))
            else:
                run_result += 'PASS: All'

        elif real_type in ['telemetry_gpu_integration_test', 'webgpu_blink_web_tests']:
            num_regressions, run_result = Util.get_gpu_integration_result(output_file)
            self.num_regressions += num_regressions

        self.run_results.append('[%s/%s, %s, %s Regressions]\n%s\n' % (self.target_index, self.total_target_count, virtual_name, num_regressions, run_result))
        self.target_index += 1

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
