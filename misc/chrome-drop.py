# pylint: disable=line-too-long, missing-function-docstring, missing-module-docstring, missing-class-docstring

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

from util.base import *  # pylint: disable=wildcard-import, unused-wildcard-import, wrong-import-position

class ChromeDrop(Program):
    SKIP_CASES = {
        # Util.LINUX: ['WebglConformance_conformance2_textures_misc_tex_3d_size_limit'],
        Util.LINUX: [],
    }
    MAX_FAIL_IN_REPORT = 100
    SEPARATOR = '|'

    def __init__(self):
        parser = argparse.ArgumentParser(description='Chrome Drop')

        parser.add_argument('--target', dest='target', help='target', default='all')
        parser.add_argument('--sync', dest='sync', help='sync', action='store_true')
        parser.add_argument('--sync-skip-mesa', dest='sync_skip_mesa', help='sync skip mesa', action='store_true')
        parser.add_argument('--build', dest='build', help='build', action='store_true')
        parser.add_argument('--build-chrome-rev', dest='build_chrome_rev', help='Chrome rev to build', default='latest')
        parser.add_argument('--build-skip-chrome', dest='build_skip_chrome', help='build skip chrome', action='store_true')
        parser.add_argument('--build-skip-mesa', dest='build_skip_mesa', help='build skip mesa', action='store_true')
        parser.add_argument('--backup', dest='backup', help='backup', action='store_true')
        parser.add_argument('--backup-skip-chrome', dest='backup_skip_chrome', help='backup skip chrome', action='store_true')
        parser.add_argument('--upload', dest='upload', help='upload', action='store_true')
        parser.add_argument('--run', dest='run', help='run', action='store_true')
        parser.add_argument('--run-angle-rev', dest='test_angle_rev', help='ANGLE revision', default='latest')
        parser.add_argument('--run-chrome-channel', dest='run_chrome_channel', help='run chrome channel', default='build')
        parser.add_argument('--run-chrome-rev', dest='run_chrome_rev', help='Chromium revision', default='latest')
        parser.add_argument('--run-mesa-rev', dest='run_mesa_rev', help='mesa revision', default='latest')
        parser.add_argument('--run-filter', dest='run_filter', help='WebGL CTS suite to run against', default='all')  # For smoke run, we may use conformance/attribs
        parser.add_argument('--run-verbose', dest='run_verbose', help='verbose mode of run', action='store_true')
        parser.add_argument('--run-webgl-target', dest='run_webgl_target', help='run webgl target, split by comma, like "0,2"', default='all')
        parser.add_argument('--run-no-angle', dest='run_no_angle', help='run without angle', action='store_true')
        parser.add_argument('--run-jobs', dest='run_jobs', help='run jobs', default=1)
        parser.add_argument('--report', dest='report', help='report')

        parser.add_argument('--batch', dest='batch', help='batch', action='store_true')
        parser.add_argument('--dryrun', dest='dryrun', help='dryrun', action='store_true')
        parser.add_argument('--mesa-dir', dest='mesa_dir', help='mesa dir')
        parser.add_argument('--run-manual', dest='run_manual', help='run manual', action='store_true')
        parser.add_argument('--no-email', dest='no_email', help='no email', action='store_true')

        parser.epilog = '''
examples:
{0} {1} --batch
{0} {1} --batch --target angle
{0} {1} --batch --target dawn
{0} {1} --target angle --run --run-filter EXTBlendFuncExtendedDrawTest
{0} {1} --target webgl --run --run-webgl-target 2
'''.format(Util.PYTHON, parser.prog)

        python_ver = Util.get_python_ver()
        if python_ver[0] == 3:
            super().__init__(parser)
        else:
            super(ChromeDrop, self).__init__(parser)

        args = self.args

        root_dir = self.root_dir
        self.angle_dir = f'{self.root_dir}/angle'
        self.chrome_dir = f'{root_dir}/chromium/src'
        self.chrome_backup_dir = f'{self.root_dir}/chromium/backup'
        self.dawn_dir = f'{self.root_dir}/dawn'
        if args.mesa_dir:
            self.mesa_dir = args.mesa_dir
        else:
            self.mesa_dir = f'{root_dir}/mesa'
        self.mesa_backup_dir = r'{self.mesa_dir}/backup'
        self.mesa_build_dir = f'{self.mesa_dir}/build'
        self.result_dir = f'{root_dir}/result/{self.timestamp}'

        self.exec_log = f'{self.result_dir}/exec.log'
        Util.ensure_nofile(self.exec_log)
        self.run_chrome_channel = args.run_chrome_channel
        self.run_chrome_rev = args.run_chrome_rev
        self.run_mesa_rev = args.run_mesa_rev
        self.run_filter = args.run_filter
        self.run_verbose = args.run_verbose
        self.run_webgl_target = args.run_webgl_target
        self.run_no_angle = args.run_no_angle

        self.target_os = args.target_os
        if not self.target_os:
            self.target_os = Util.HOST_OS

        if args.target == 'all':
            self.targets = ['angle', 'dawn', 'webgl']
        else:
            self.targets = args.target.split(',')

        self.chrome_rev = 0

        self._handle_ops()

    def sync(self):
        self._op('sync')

    def build(self):
        self._op('build')

    def backup(self):
        self._op('backup')

    def upload(self):
        self._op('upload')

    def _op(self, op):
        chrome_targets = []
        if 'webgl' in self.targets:
            chrome_targets.append('webgl')
        if 'webgpu' in self.targets:
            chrome_targets.append('webgpu')
        chrome_target = ','.join(chrome_targets)

        cmds = []
        if op == 'sync':
            if self.target_os == Util.LINUX and not self.args.sync_skip_mesa:
                cmds.append(f'{Util.PYTHON} {ScriptRepo.ROOT_DIR}/mesa/mesa.py --sync --root-dir {self.mesa_dir}')

            if 'angle' in self.targets:
                cmds.append(f'{Util.PYTHON} {Util.GNP_SCRIPT} --sync --runhooks --root-dir {self.angle_dir}')

            if 'dawn' in self.targets:
                cmds.append(f'{Util.PYTHON} {Util.GNP_SCRIPT} --sync --runhooks --root-dir {self.dawn_dir}')

            if 'webgl' in self.targets or 'webgpu' in self.targets:
                if 'webgl' in self.targets:
                    Util.chdir(f'{self.chrome_dir}/third_party/webgl/src')
                    for folder in ['conformance', 'conformance2']:
                        self._execute(f'git checkout sdk/tests/{folder}/textures/00_test_list.txt')

                cmd = f'{Util.PYTHON} {Util.GNP_SCRIPT} --sync --sync-reset --runhooks --root-dir {self.chrome_dir}'
                if self.args.build_chrome_rev != 'latest':
                    cmd += f' --rev {self.args.build_chrome_rev}'
                cmds.append(cmd)

        elif op == 'build':
            if self.target_os == Util.LINUX and not self.args.build_skip_mesa:
                cmds.append(f'{Util.PYTHON} {ScriptRepo.ROOT_DIR}/mesa/mesa.py --build --root-dir {self.mesa_dir}')

            if 'angle' in self.targets:
                cmds.append(f'{Util.PYTHON} {Util.GNP_SCRIPT} --makefile --build --build-target angle_e2e --root-dir {self.angle_dir}')

            if 'dawn' in self.targets:
                cmds.append(f'{Util.PYTHON} {Util.GNP_SCRIPT} --makefile --build --build-target dawn_e2e --root-dir {self.dawn_dir}')

            if ('webgl' in self.targets or 'webgpu' in self.targets) and self.run_chrome_channel == 'build' and not self.args.build_skip_chrome:
                cmds.append(f'{Util.PYTHON} {Util.GNP_SCRIPT} --no-component-build --makefile --symbol-level 0 --build --build-target {chrome_target} --root-dir {self.chrome_dir}')

        elif op == 'backup':
            if 'angle' in self.targets:
                cmds.append(f'{Util.PYTHON} {Util.GNP_SCRIPT} --backup --backup-target angle_e2e --root-dir {self.angle_dir}')

            if 'dawn' in self.targets:
                cmds.append(f'{Util.PYTHON} {Util.GNP_SCRIPT} --backup --backup-target dawn_e2e --root-dir {self.dawn_dir}')

            if ('webgl' in self.targets or 'webgpu' in self.targets) and not self.args.backup_skip_chrome:
                cmd = f'{Util.PYTHON} {Util.GNP_SCRIPT} --backup --backup-target {chrome_target} --root-dir {self.chrome_dir}'
                if self.target_os == Util.CHROMEOS:
                    cmd += ' --target-os chromeos'
                cmd.append(cmd)

        elif op == 'upload':
            if 'angle' in self.targets:
                cmds.append(f'{Util.PYTHON} {Util.GNP_SCRIPT} --upload --root-dir {self.angle_dir}')

            if 'dawn' in self.targets:
                cmds.append(f'{Util.PYTHON} {Util.GNP_SCRIPT} --upload --root-dir {self.dawn_dir}')

            if ('webgl' in self.targets or 'webgpu' in self.targets) and not self.args.backup_skip_chrome:
                cmd = f'{Util.PYTHON} {Util.GNP_SCRIPT} --upload --root-dir {self.chrome_dir}'
                if self.target_os == Util.CHROMEOS:
                    cmd += ' --target-os chromeos'
                cmd.append(cmd)

        for cmd in cmds:
            self._execute(cmd, exit_on_error=False)

        if op == 'sync' and 'webgl' in self.targets:
            # Skip video cases
            if 'webgl' in self.targets:
                for folder in ['conformance', 'conformance2']:
                    for line in fileinput.input(f'{self.chrome_dir}/third_party/webgl/src/sdk/tests/{folder}/textures/00_test_list.txt', inplace=True):
                        matched = re.match('video/00_test_list.txt', line)
                        if matched:
                            line = '//' + line
                        sys.stdout.write(line)
                    fileinput.close()

    def run(self):
        if self.target_os == Util.CHROMEOS:
            return

        Util.clear_proxy()

        if Util.HOST_OS == Util.LINUX:
            self.run_mesa_rev = Util.set_mesa(self.mesa_backup_dir, self.run_mesa_rev)

        gpu_name, gpu_driver, gpu_device_id = Util.get_gpu_info()
        Util.append_file(self.exec_log, f'GPU name{self.SEPARATOR}{gpu_name}')
        Util.append_file(self.exec_log, f'GPU driver{self.SEPARATOR}{gpu_driver}')
        Util.append_file(self.exec_log, f'GPU device id{self.SEPARATOR}{gpu_device_id}')

        if 'angle' in self.targets:
            cmd = f'{Util.PYTHON} {Util.GNP_SCRIPT} --run --run-target angle_e2e --run-rev latest --root-dir {self.angle_dir} --no-exit-on-error'
            run_args = ''
            if self.args.dryrun:
                run_args = '--gtest_filter=*EGLAndroidFrameBufferTargetTest*'
            elif self.run_filter != 'all':
                run_args = f'--gtest_filter=*{self.run_filter}*'
            else:
                run_args = '--gtest_filter=*D3D11*'

            if run_args:
                cmd += f' --run-args="{run_args}"'
            timer = Timer()
            self._execute(cmd, exit_on_error=False)
            Util.append_file(self.exec_log, f'ANGLE Run: {timer.stop()}')

            rev_name, _ = Util.get_backup_dir(f'{self.angle_dir}/backup', 'latest')
            output_file = f'{self.angle_dir}/backup/{rev_name}/out/Release/output.json'
            result_file = f'{self.result_dir}/angle.json'
            if os.path.exists(output_file):
                shutil.move(output_file, result_file)
            else:
                Util.ensure_file(result_file)

            Util.append_file(self.exec_log, f'ANGLE Rev{self.SEPARATOR}{rev_name}')

        if 'dawn' in self.targets:
            cmd = f'{Util.PYTHON} {Util.GNP_SCRIPT} --run --run-target dawn_e2e --run-rev latest --root-dir {self.dawn_dir} --no-exit-on-error'
            result_file = f'{self.result_dir}/dawn.json'
            run_args = f'--gtest_output=json:{result_file}'
            if self.run_filter != 'all':
                run_args += f' --gtest_filter=*{self.run_filter}*'
            if self.args.dryrun:
                run_args += ' --gtest_filter=*BindGroupTests*'
            run_args += ' --enable-backend-validation=disabled'
            run_args += ' --backend=d3d12'
            cmd += f' --run-args="{run_args}"'
            timer = Timer()
            self._execute(cmd, exit_on_error=False)
            Util.append_file(self.exec_log, f'Dawn run: {timer.stop()}')

            rev_name, _ = Util.get_backup_dir(f'{self.dawn_dir}/backup', 'latest')
            Util.append_file(self.exec_log, f'Dawn Rev{self.SEPARATOR}{rev_name}')

        if 'webgl' in self.targets:
            common_cmd1 = 'vpython3 content/test/gpu/run_gpu_integration_test.py'
            common_cmd2 = ' --disable-log-uploads'
            if self.run_chrome_channel == 'build':
                self.chrome_rev = self.run_chrome_rev
                (chrome_rev_dir, self.chrome_rev) = Util.get_backup_dir(self.chrome_backup_dir, self.chrome_rev)
                chrome_rev_dir = f'{self.chrome_backup_dir}/{chrome_rev_dir}'
                Util.chdir(chrome_rev_dir, verbose=True)
                Util.info(f'Use Chrome at {chrome_rev_dir}')

                if Util.HOST_OS == Util.WINDOWS:
                    chrome = 'out\\Release\\chrome.exe'
                else:
                    if os.path.exists('out/Release/chrome'):
                        chrome = 'out/Release/chrome'
                    else:
                        chrome = 'out/Default/chrome'

                common_cmd2 += f' --browser=exact --browser-executable={chrome}'
            else:
                common_cmd2 += f' --browser={self.run_chrome_channel}'
                Util.chdir(self.chrome_dir)
                self.chrome_rev = self.run_chrome_channel
                if Util.HOST_OS == Util.DARWIN:
                    if self.run_chrome_channel == 'canary':
                        chrome = '"/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"'
                    else:
                        Util.error('run_chrome_channel is not supported')
                elif Util.HOST_OS == Util.LINUX:
                    if self.run_chrome_channel == 'canary':
                        chrome = '/usr/bin/google-chrome-unstable'
                    elif self.run_chrome_channel == 'stable':
                        chrome = '/usr/bin/google-chrome-stable'
                    else:
                        Util.error('run_chrome_channel is not supported')
                else:
                    Util.error('run_chrome_channel is not supported')

            if self.args.run_manual:
                param = '--enable-experimental-web-platform-features --disable-gpu-process-for-dx12-vulkan-info-collection --disable-domain-blocking-for-3d-apis --disable-gpu-process-crash-limit --disable-blink-features=WebXR --js-flags=--expose-gc --disable-gpu-watchdog --autoplay-policy=no-user-gesture-required --disable-features=UseSurfaceLayerForVideo --enable-net-benchmarking --metrics-recording-only --no-default-browser-check --no-first-run --ignore-background-tasks --enable-gpu-benchmarking --deny-permission-prompts --autoplay-policy=no-user-gesture-required --disable-background-networking --disable-component-extensions-with-background-pages --disable-default-apps --disable-search-geolocation-disclosure --enable-crash-reporter-for-testing --disable-component-update'
                param += ' --use-gl=angle'
                if Util.HOST_OS == Util.LINUX and self.run_no_angle:
                    param += ' --use-gl=desktop'
                self._execute(f'{chrome} {param} http://wp-27.sh.intel.com/workspace/project/WebGL/sdk/tests/webgl-conformance-tests.html?version=2.0.1')
                return

            if self.run_filter != 'all':
                common_cmd2 += f' --test-filter=*{self.run_filter}*'
            if self.args.dryrun:
                # common_cmd2 += ' --test-filter=*copy-texture-image-same-texture*::*ext-texture-norm16*'
                common_cmd2 += ' --test-filter=*conformance/attribs*'

            if Util.HOST_OS in self.SKIP_CASES:
                skip_filter = self.SKIP_CASES[Util.HOST_OS]
                for skip_tmp in skip_filter:
                    common_cmd2 += f' --skip={skip_tmp}'
            if self.run_verbose:
                common_cmd2 += ' --verbose'

            common_cmd2 += f' --jobs={self.args.run_jobs}'

            Util.ensure_dir(self.result_dir)

            COMB_INDEX_WEBGL = 0
            COMB_INDEX_BACKEND = 1
            if Util.HOST_OS in [Util.LINUX, Util.DARWIN]:
                all_combs = [['2.0.1']]
            elif Util.HOST_OS == Util.WINDOWS:
                all_combs = [
                    ['1.0.3', 'd3d11'],
                    ['2.0.1', 'd3d11'],
                ]

            test_combs = []
            if self.run_webgl_target == 'all':
                test_combs = all_combs
            else:
                for i in self.run_webgl_target.split(','):
                    test_combs.append(all_combs[int(i)])

            for comb in test_combs:
                extra_browser_args = '--disable-backgrounding-occluded-windows'
                if Util.HOST_OS == Util.LINUX and self.run_no_angle:
                    extra_browser_args += ',--use-gl=desktop'
                cmd = common_cmd1 + f' webgl{comb[COMB_INDEX_WEBGL][0]}_conformance {common_cmd2} --webgl-conformance-version={comb[COMB_INDEX_WEBGL]}'
                result_file = ''
                if Util.HOST_OS == Util.LINUX:
                    result_file = f'{self.result_dir}/webgl-{comb[COMB_INDEX_WEBGL]}.log'
                elif Util.HOST_OS == Util.WINDOWS:
                    extra_browser_args += f' --use-angle={comb[COMB_INDEX_BACKEND]}'
                    result_file = f'{self.result_dir}/webgl-{comb[COMB_INDEX_WEBGL]}-{comb[COMB_INDEX_BACKEND]}.log'

                if extra_browser_args:
                    cmd += f' --extra-browser-args="{extra_browser_args}"'
                cmd += f' --write-full-results-to {result_file}'
                timer = Timer()
                self._execute(cmd, exit_on_error=False, show_duration=True)
                Util.append_file(self.exec_log, f'WebGL {comb[COMB_INDEX_WEBGL]} {comb[COMB_INDEX_BACKEND]} run: {timer.stop()}')

            rev_name, _ = Util.get_backup_dir(f'{os.path.dirname(self.chrome_dir)}/backup', 'latest')
            Util.append_file(self.exec_log, f'Chrome Rev{self.SEPARATOR}{rev_name}')

        if 'webgpu' in self.targets:
            gpu_name, gpu_driver, gpu_device_id = Util.get_gpu_info()

            cmd = 'vpython3 content/test/gpu/run_gpu_integration_test.py webgpu_cts --passthrough --stable-jobs'
            cmd += ' --disable-log-uploads'
            if self.run_chrome_channel == 'build':
                self.chrome_rev = self.run_chrome_rev
                print(self.chrome_backup_dir, self.chrome_rev)
                (chrome_rev_dir, self.chrome_rev) = Util.get_backup_dir(self.chrome_backup_dir, self.chrome_rev)
                chrome_rev_dir = f'{self.chrome_backup_dir}/{chrome_rev_dir}'
                # Locally update expectations.txt in webgpu_cts_tests
                self._update_webgpu_cts_expectations(chrome_rev_dir, gpu_device_id)
                Util.chdir(chrome_rev_dir, verbose=True)
                Util.info(f'Use Chrome at {chrome_rev_dir}')

                if Util.HOST_OS == Util.WINDOWS:
                    chrome = 'out\\Release\\chrome.exe'
                else:
                    if os.path.exists('out/Release/chrome'):
                        chrome = 'out/Release/chrome'
                    else:
                        chrome = 'out/Default/chrome'

                cmd += f' --browser=exact --browser-executable={chrome}'
            else:
                cmd += f' --browser={self.run_chrome_channel}'
                Util.chdir(self.chrome_dir)
                self.chrome_rev = self.run_chrome_channel
                if Util.HOST_OS == Util.DARWIN:
                    if self.run_chrome_channel == 'canary':
                        chrome = '"/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"'
                    else:
                        Util.error('run_chrome_channel is not supported')
                elif Util.HOST_OS == Util.LINUX:
                    if self.run_chrome_channel == 'canary':
                        chrome = '/usr/bin/google-chrome-unstable'
                    elif self.run_chrome_channel == 'stable':
                        chrome = '/usr/bin/google-chrome-stable'
                    else:
                        Util.error('run_chrome_channel is not supported')
                else:
                    Util.error('run_chrome_channel is not supported')

            if self.run_filter != 'all':
                cmd += f' --test-filter=*{self.run_filter}*'
            if self.args.dryrun:
                cmd += ' --test-filter=*webgpu:api,operation,adapter,requestAdapter:requestAdapter:powerPreference*'

            if self.run_verbose:
                cmd += ' --verbose'

            cmd += f' --jobs={self.args.run_jobs}'

            Util.ensure_dir(self.result_dir)

            extra_browser_args = '--js-flags=--expose-gc --force_high_performance_gpu'
            result_file = f'{self.result_dir}/webgpu.log'

            if extra_browser_args:
                cmd += f' --extra-browser-args="{extra_browser_args}"'
            cmd += f' --write-full-results-to {result_file}'
            timer = Timer()
            self._execute(cmd, exit_on_error=False, show_duration=True)
            Util.append_file(self.exec_log, f'WebGPU run: {timer.stop()}')

            rev_name, _ = Util.get_backup_dir(f'{os.path.dirname(self.chrome_dir)}/backup', 'latest')
            Util.append_file(self.exec_log, f'Chrome Rev{self.SEPARATOR}{rev_name}')

        self.report()

    def report(self):
        if self.args.report:
            self.result_dir = self.args.report

        regression_count = 0
        summary = 'Final summary:\n'
        details = 'Final details:\n'
        for result_file in os.listdir(self.result_dir):
            if 'angle' in result_file or 'webgl' in result_file or 'webgpu' in result_file:
                test_type = 'gtest_angle'
            elif 'dawn' in result_file:
                test_type = 'dawn'
            else:
                continue

            pass_fail, fail_pass, fail_fail, pass_pass = Util.get_test_result(f'{self.result_dir}/{result_file}', test_type)
            regression_count += len(pass_fail)
            result = f'{os.path.splitext(result_file)[0]}: PASS_FAIL {len(pass_fail)}, FAIL_PASS {len(fail_pass)}, FAIL_FAIL {len(fail_fail)} PASS_PASS {len(pass_pass)}\n'
            summary += result
            if pass_fail:
                result += '[PASS_FAIL]\n%s\n' % '\n'.join(pass_fail[:self.MAX_FAIL_IN_REPORT])
            if fail_pass:
                result += '[FAIL_PASS]\n%s\n' % '\n'.join(fail_pass[:self.MAX_FAIL_IN_REPORT])
            details += result

        exec_log_content = open(self.exec_log, encoding='utf-8').read()

        Util.info(details)
        Util.info(summary)
        Util.info(exec_log_content)

        report_file = f'{self.result_dir}/report.txt'
        Util.ensure_nofile(report_file)
        Util.append_file(report_file, summary)
        Util.append_file(report_file, details)

        if not self.args.no_email:
            subject = f'[Chrome Drop] {Util.HOST_NAME} {self.timestamp}'
            Util.send_email(subject, summary + '\n' + details + '\n' + exec_log_content)

    def batch(self):
        self.sync()
        self.build()
        self.backup()
        self.run()

    def _handle_ops(self):
        args = self.args
        if args.sync:
            self.sync()
        if args.build:
            self.build()
        if args.backup:
            self.backup()
        if args.run:
            self.run()
        if args.report:
            self.report()
        if args.batch:
            self.batch()
        if args.upload:
            self.upload()

    def _update_webgpu_cts_expectations(self, project_root_dir, gpu_device_id):
        expectation_file = f'{project_root_dir}/third_party/dawn/webgpu-cts/expectations.txt'

        generation = Util.get_intel_gpu_generation(f'0x{gpu_device_id}')
        if generation is None:
            Util.warning(f'Failed to update {expectation_file} because of unknown generation')
            return

        old_gpu_tag = 'intel-gen-9'
        new_gpu_tag = f'intel-gen-{generation}'
        if old_gpu_tag == new_gpu_tag:
            return

        if not os.path.exists(expectation_file):
            Util.warning(f'{expectation_file} does not exist')
            return

        tag_header_scope = False
        has_new_gpu_tag = False
        for line in fileinput.input(expectation_file, inplace=True):
            # Skip the update if the new gpu tag already exists
            if has_new_gpu_tag:
                sys.stdout.write(line)
                continue

            if re.search(new_gpu_tag, line):
                has_new_gpu_tag = True
            elif re.search('BEGIN TAG HEADER', line):
                tag_header_scope = True
            elif re.search('END TAG HEADER', line):
                tag_header_scope = False
            elif re.search(old_gpu_tag, line):
                if tag_header_scope:
                    # Append the new gpu tag to tag header
                    line = line.replace('\n', f' {new_gpu_tag}\n')
                else:
                    # Append expectation with the new gpu tag following the old one
                    line += line.replace(old_gpu_tag, new_gpu_tag)
            sys.stdout.write(line)
        fileinput.close()

if __name__ == '__main__':
    ChromeDrop()
