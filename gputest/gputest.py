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

    REAL_TYPE_INFO_INDEX_FILTER = 0
    REAL_TYPE_INFO_INDEX_EXTRA_ARGS = 1
    REAL_TYPE_INFO = {
        'aquarium': ['--test-time', ''],
        'gtest': ['--gtest_filter', ''], # --cfi-diag=0
        'telemetry_gpu_integration_test': ['--test-filter', '--retry-limit 1 --retry-only-retry-on-failure-tests'],
        'webgpu_blink_web_tests': ['--isolated-script-test-filter', '--seed 4 --jobs=1 --driver-logging --no-show-results --clobber-old-results --no-retry-failures --order=natural --isolated-script-test-filter=wpt_internal/webgpu/* --ignore-default-expectations --additional-expectations=../../third_party/blink/web_tests/WebGPUExpectations --additional-driver-flag=--enable-unsafe-webgpu --additional-driver-flag=--disable-gpu-sandbox'],
    }

    VIRTUAL_NAME_INFO_INDEX_REAL_TYPE = 0
    VIRTUAL_NAME_INFO_INDEX_DRYRUN = 1
    VIRTUAL_NAME_INFO_INDEX_EXTRA_ARGS = 2
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
        'dawn_perf_tests': ['gtest', 'BufferUploadPerf.Run/D3D12_Intel', '--override-steps=1'],
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

        'webgpu_blink_web_tests': ['webgpu_blink_web_tests', 'wpt_internal/webgpu/cts.html?q=webgpu:api,validation,setViewport:*'],
        'webgpu_blink_web_tests_with_backend_validation': ['webgpu_blink_web_tests', 'wpt_internal/webgpu/cts.html?q=webgpu:api,validation,setViewport:*'],
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
    TARGET_INDEX_TOTAL_SHARDS = index
    TARGET_INDEX_MAX = index

    RESULT_FILE_PATTERN = r'^.*-(.*).log$'

    EMAIL_SENDER = 'webgraphics@intel.com'
    EMAIL_ADMIN = 'yang.gu@intel.com'
    EMAIL_TO = 'yang.gu@intel.com'

    def __init__(self):
        parser = argparse.ArgumentParser(description='GPU Test')

        parser.add_argument('--debug', dest='debug', help='debug', action='store_true')
        parser.add_argument('--target', dest='target', help='target', default='all')
        parser.add_argument('--email', dest='email', help='email', action='store_true')

        parser.add_argument('--list', dest='list', help='list', action='store_true')
        parser.add_argument('--sync', dest='sync', help='sync', action='store_true')
        parser.add_argument('--sync-skip-mesa', dest='sync_skip_mesa', help='sync skip mesa', action='store_true')
        #parser.add_argument('--sync-skip-roll-dawn', dest='sync_skip_roll_dawn', help='sync skip roll dawn', action='store_true')
        parser.add_argument('--sync-roll-dawn', dest='sync_roll_dawn', help='sync roll dawn', action='store_true')
        parser.add_argument('--build', dest='build', help='build', action='store_true')
        parser.add_argument('--build-skip-mesa', dest='build_skip_mesa', help='build skip mesa', action='store_true')
        parser.add_argument('--run', dest='run', help='run', action='store_true')
        parser.add_argument('--run-mesa-rev', dest='run_mesa_rev', help='mesa revision', default='latest')
        parser.add_argument('--dryrun', dest='dryrun', help='dryrun', action='store_true')
        parser.add_argument('--dryrun-with-shard', dest='dryrun_with_shard', help='dryrun with shard', action='store_true')
        parser.add_argument('--report', dest='report', help='report')
        parser.add_argument('--batch', dest='batch', help='batch', action='store_true')
        parser.add_argument('--mesa-type', dest='mesa_type', help='mesa type', default='iris')

        parser.epilog = '''
python %(prog)s --sync --build --run --dryrun --email
'''
        python_ver = Util.get_python_ver()
        if python_ver[0] == 3:
            super().__init__(parser)
        else:
            super(GPUTest, self).__init__(parser)

        args = self.args

        self.chromium_dir = '%s/chromium' % self.root_dir
        self.chromium_src_dir = '%s/src' % self.chromium_dir
        target_os = self.target_os
        if target_os == 'default':
            target_os = Util.HOST_OS

        self._get_targets()
        os_targets = []
        for target in self.targets:
            if target[self.TARGET_INDEX_OS] == target_os:
                os_targets.append(target)
        self.os_targets = os_targets

        target_indexes = []
        arg_target = args.target
        if arg_target == 'all':
            arg_target = '0-%d' % (len(self.os_targets) - 1)
        arg_targets = arg_target.split(',')
        for tmp_target in arg_targets:
            if '-' in tmp_target:
                tmp_targets = tmp_target.split('-')
                target_min = int(tmp_targets[0])
                target_max = int(tmp_targets[1])
                target_indexes.extend(range(target_min, target_max + 1))
            else:
                target_indexes.append(int(tmp_target))
        target_indexes = sorted(target_indexes)
        self.target_indexes = target_indexes

        if args.report:
            self.result_dir = args.report
        else:
            self.result_dir = '%s/result/%s' % (self.root_dir, self.timestamp)
            Util.ensure_dir(self.result_dir)
        self.exec_log = '%s/exec.log' % self.result_dir

        if args.email or args.batch:
            self.email = True
        else:
            self.email = False

        self._handle_ops()

    def list(self):
        for index, target in enumerate(self.os_targets):
            print('%s: %s' % (index, target[self.TARGET_INDEX_VIRTUAL_NAME]))

    def sync(self):
        projects = []
        for target_index in self.target_indexes:
            project = self.os_targets[target_index][self.TARGET_INDEX_PROJECT]
            if project not in projects:
                projects.append(project)

        if self.target_os == Util.LINUX and not self.args.sync_skip_mesa:
            projects.append('mesa')

        for project in projects:
            timer = Timer()
            if project == 'mesa':
                cmd = 'python %s/mesa/mesa.py --root-dir %s/mesa --sync' % (ScriptRepo.ROOT_DIR, self.root_dir)
            else:
                cmd = 'python %s --root-dir %s/%s --sync --runhooks' % (Util.GNP_SCRIPT_PATH, self.root_dir, project)
            dryrun = self.args.dryrun
            if self._execute(cmd, exit_on_error=False, dryrun=dryrun)[0]:
                Util.error('Sync failed')

            if project == 'aquarium' and self.args.sync_roll_dawn:
                Util.chdir('%s/aquarium/third_party/dawn' % self.root_dir)
                self._execute('git checkout master && git pull', dryrun=dryrun)
                Util.info('Roll Dawn in Aquarium to %s on %s' % (Util.get_repo_head_hash(), Util.get_repo_head_date()))

            info = 'sync %s;%s;%s' % (project, timer.stop(), cmd)
            Util.info(info)
            Util.append_file(self.exec_log, info)

    def build(self):
        project_targets = {}
        for target_index in self.target_indexes:
            project = self.os_targets[target_index][self.TARGET_INDEX_PROJECT]
            real_name = self.os_targets[target_index][self.TARGET_INDEX_REAL_NAME]
            if project not in project_targets:
                project_targets[project] = [real_name]
            elif real_name not in project_targets[project]:
                project_targets[project].append(real_name)

        if self.target_os == Util.LINUX and not self.args.build_skip_mesa:
            project_targets['mesa'] = ''

        for project in project_targets:
            timer = Timer()
            if project == 'mesa':
                cmd = 'python %s/mesa/mesa.py --root-dir %s/mesa --build' % (ScriptRepo.ROOT_DIR, self.root_dir)
            else:
                cmd = 'python %s --root-dir %s/%s --makefile --build --build-target %s' % (Util.GNP_SCRIPT_PATH, self.root_dir, project, ','.join(project_targets[project]))
            if self._execute(cmd, exit_on_error=False, dryrun=self.args.dryrun)[0]:
                error = '[GPUTest] Project %s build failed' % project
                if self.email:
                    Util.send_email(self.EMAIL_SENDER, self.EMAIL_ADMIN, error, '')
                Util.error(error)

            info = 'build %s;%s;%s' % (project, timer.stop(), cmd)
            Util.info(info)
            Util.append_file(self.exec_log, info)

    def run(self):
        all_timer = Timer()
        Util.clear_proxy()

        Util.append_file(self.exec_log, 'OS Version;%s' % Util.HOST_OS_RELEASE)

        if Util.HOST_OS == Util.LINUX:
            self.run_mesa_rev = Util.set_mesa('%s/mesa/backup' % self.root_dir, self.args.run_mesa_rev, self.args.mesa_type)
            info = 'Mesa revision;%s' % self.run_mesa_rev
            Util.append_file(self.exec_log, info)

        args = self.args
        chromium_printed = False
        for index, target_index in enumerate(self.target_indexes):
            project = self.os_targets[target_index][self.TARGET_INDEX_PROJECT]
            if project == 'chromium' and not chromium_printed:
                repo = ChromiumRepo('%s/chromium' % self.root_dir)
                info = 'Chromium revision;%s' % repo.get_working_dir_rev()
                Util.append_file(self.exec_log, info)
                chromium_printed = True
            virtual_name = self.os_targets[target_index][self.TARGET_INDEX_VIRTUAL_NAME]
            real_name = self.os_targets[target_index][self.TARGET_INDEX_REAL_NAME]
            real_type = self.os_targets[target_index][self.TARGET_INDEX_REAL_TYPE]
            config_cmd = 'python %s --run --root-dir %s/%s --run-target %s --run-rev out' % (Util.GNP_SCRIPT_PATH, self.root_dir, project, real_name)

            run_args = self.os_targets[target_index][self.TARGET_INDEX_RUN_ARGS]
            for i, run_arg in reversed(list(enumerate(run_args))):
                if run_arg.startswith('--extra-browser-args'):
                    run_arg = run_arg.replace('--extra-browser-args=', '')
                    run_args[i] = '--extra-browser-args=\\\"%s --disable-backgrounding-occluded-windows\\\"' % run_arg
                elif run_arg == '--browser=release_x64':
                    run_args[i] = '--browser=release'
                elif run_arg.startswith('--gtest-benchmark-name'):
                    run_args.remove(run_arg)
                elif run_arg in ['-v', '--show-stdout', 'angle_end2end_tests', 'angle_perftests', '--print-test-stdout']:
                    run_args.remove(run_arg)
                elif run_arg == '--target=Release_x64':
                    run_args[i] = '--target=release'
                # we use 5912 and 3e98 in test
                elif run_arg == '3e92':
                    run_args[i] = '3e98'
            config_args = ' '.join(run_args)

            extra_args = self.REAL_TYPE_INFO[real_type][self.REAL_TYPE_INFO_INDEX_EXTRA_ARGS]
            if extra_args:
                config_args += ' %s' % extra_args

            dryrun_cond = self.VIRTUAL_NAME_INFO[virtual_name][self.VIRTUAL_NAME_INFO_INDEX_DRYRUN]
            if args.dryrun and dryrun_cond:
                if real_type not in ['aquarium', 'webgpu_blink_web_tests']:
                    dryrun_cond = '*%s*' % dryrun_cond
                config_args += ' %s=%s' % (self.REAL_TYPE_INFO[real_type][self.REAL_TYPE_INFO_INDEX_FILTER], dryrun_cond)

            if real_type in ['telemetry_gpu_integration_test', 'webgpu_blink_web_tests']:
                total_shards_arg = '--total-shards'
                shard_index_arg = '--shard-index'
                output_arg = '--write-full-results-to'

            total_shards = int(self.os_targets[target_index][self.TARGET_INDEX_TOTAL_SHARDS])
            if real_type == 'gtest':
                total_shards = 1

            for shard_index in range(total_shards):
                shard_args = ''
                if total_shards > 1:
                    shard_args += ' %s=%s %s=%s' % (total_shards_arg, total_shards, shard_index_arg, shard_index)

                total_target_indexes = len(self.target_indexes)
                total_target_indexes_str = str(total_target_indexes)
                total_target_indexes_str_len = len(total_target_indexes_str)
                total_shards_str = str(total_shards)
                total_shards_str_len = len(total_shards_str)
                op = '%s_%s-%s_%s-%s' % (str(index + 1).zfill(total_target_indexes_str_len), total_target_indexes_str, str(shard_index + 1).zfill(total_shards_str_len), total_shards_str, virtual_name)
                result_file = '%s/%s.log' % (self.result_dir, op)

                if real_type in ['aquarium']:
                    shard_args += ' > %s' % result_file
                elif real_type in ['telemetry_gpu_integration_test', 'webgpu_blink_web_tests']:
                    shard_args += ' %s=' % output_arg
                    if real_type == 'gtest':
                        shard_args += 'json:'

                    shard_args += result_file
                    Util.ensure_file(result_file)

                cmd = '%s --run-args "%s%s"' % (config_cmd, config_args, shard_args)
                timer = Timer()
                self._execute(cmd, exit_on_error=False)
                info = 'run %s;%s;%s' % (op, timer.stop(), cmd)
                Util.info(info)
                Util.append_file(self.exec_log, info)

                if real_type in ['gtest']:
                    shutil.copyfile('%s/chromium/src/out/release/output.json' % self.root_dir, result_file)
                self._parse_result(result_file, verbose=True)
                if args.dryrun and not args.dryrun_with_shard:
                    break

        all_info = 'run all;%s;run()' % all_timer.stop()
        Util.info(all_info)
        Util.append_file(self.exec_log, all_info)

        self.report()

    def batch(self):
        self.sync()
        self.build()
        self.run()

    def report(self):
        results = []
        total_regressions = 0
        for line in open(self.exec_log):
            fields = line.split(';')
            results.append('== %s: %s ==' % (fields[0], fields[1].rstrip('\n')))
            name = fields[0]
            if name.startswith('run') and name != 'run all':
                op = name.replace('run ', '')
                result_file = '%s/%s.log' % (self.result_dir, op)
                num_regressions, target_results = self._parse_result(result_file)
                total_regressions += num_regressions
                results += target_results

        subject = '[GPUTest] Host %s Datetime %s Regressions %s' % (Util.HOST_NAME, self.timestamp, total_regressions)
        for result in [subject] + results:
            print(result)

        Util.append_file('%s/report.log' % self.result_dir, [subject] + results)

        if self.email:
            Util.send_email(self.EMAIL_SENDER, self.EMAIL_TO, subject, results)

    def _get_targets(self):
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
                        target[self.TARGET_INDEX_TOTAL_SHARDS] = 1
                        target[self.TARGET_INDEX_OS] = target_os
                        target[self.TARGET_INDEX_PROJECT] = 'chromium'
                        target[self.TARGET_INDEX_VIRTUAL_NAME] = virtual_name
                        target[self.TARGET_INDEX_REAL_NAME] = real_name
                        target[self.TARGET_INDEX_REAL_TYPE] = self.VIRTUAL_NAME_INFO[virtual_name][self.VIRTUAL_NAME_INFO_INDEX_REAL_TYPE]
                        if 'args' in target_detail:
                            target_run_args = target_detail['args']

                        target[self.TARGET_INDEX_RUN_ARGS] = target_run_args
                        if 'swarming' in target_detail and 'shards' in target_detail['swarming']:
                            target[self.TARGET_INDEX_TOTAL_SHARDS] = target_detail['swarming']['shards']

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
        Util.dump_json('%s/gputest/config.json' % ScriptRepo.IGNORE_DIR, targets)
        self.targets = targets

        if self.args.debug:
            print(len(recorded_virtual_name))
            recorded_virtual_name = sorted(recorded_virtual_name)
            for virtual_name in recorded_virtual_name:
                print(virtual_name)
            for target in targets:
                print(target)

    def _parse_result(self, result_file, verbose=False):
        file_name = os.path.basename(result_file)
        op = file_name.replace('.log', '')
        match = re.match(self.RESULT_FILE_PATTERN, file_name)
        virtual_name = match.group(1)
        real_type = self.VIRTUAL_NAME_INFO[virtual_name][self.VIRTUAL_NAME_INFO_INDEX_REAL_TYPE]

        if real_type == 'aquarium':
            lines = open(result_file).readlines()
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
                    results = ['%s: %s -> %s' % (change_type, base_fps, run_fps)]
                    break

        elif real_type in ['gtest', 'telemetry_gpu_integration_test', 'webgpu_blink_web_tests']:
            num_regressions, results = Util.get_test_result(result_file)

        return num_regressions, results

    def _handle_ops(self):
        args = self.args
        if args.list:
            self.list()
        if args.sync:
            self.sync()
        if args.build:
            self.build()
        if args.run:
            self.run()
        if args.batch:
            self.batch()
        if args.report:
            self.report()

if __name__ == '__main__':
    GPUTest()
