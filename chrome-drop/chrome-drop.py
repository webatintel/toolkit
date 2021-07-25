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

class ChromeDrop(Program):
    SKIP_CASES = {
        #Util.LINUX: ['WebglConformance_conformance2_textures_misc_tex_3d_size_limit'],
        Util.LINUX: [],
    }
    MAX_FAIL_IN_REPORT = 20
    SEPARATOR = '|'

    def __init__(self):
        parser = argparse.ArgumentParser(description='Chrome Drop')

        parser.add_argument('--target', dest='target', help='target', default='all')
        parser.add_argument('--sync', dest='sync', help='sync', action='store_true')
        parser.add_argument('--build', dest='build', help='build', action='store_true')
        parser.add_argument('--build-chrome-rev', dest='build_chrome_rev', help='Chrome rev to build', default='latest')
        parser.add_argument('--build-skip-chrome', dest='build_skip_chrome', help='skip building chrome during build', action='store_true')
        parser.add_argument('--build-skip-mesa', dest='build_skip_build_mesa', help='skip building mesa during build', action='store_true')
        parser.add_argument('--build-skip-backup', dest='build_skip_backup', help='skip backing up chrome during build', action='store_true')
        parser.add_argument('--run', dest='run', help='run', action='store_true')
        parser.add_argument('--run-angle-rev', dest='test_angle_rev', help='ANGLE revision', default='latest')
        parser.add_argument('--run-chrome-channel', dest='run_chrome_channel', help='run chrome channel', default='build')
        parser.add_argument('--run-chrome-rev', dest='run_chrome_rev', help='Chromium revision', default='latest')
        parser.add_argument('--run-mesa-rev', dest='run_mesa_rev', help='mesa revision', default='latest')
        parser.add_argument('--run-filter', dest='run_filter', help='WebGL CTS suite to run against', default='all')  # For smoke run, we may use conformance/attribs
        parser.add_argument('--run-verbose', dest='run_verbose', help='verbose mode of run', action='store_true')
        parser.add_argument('--run-webgl-target', dest='run_webgl_target', help='run webgl target, split by comma, like "0,2"', default='all')
        parser.add_argument('--run-no-angle', dest='run_no_angle', help='run without angle', action='store_true')
        parser.add_argument('--report', dest='report', help='report')

        parser.add_argument('--batch', dest='batch', help='batch', action='store_true')
        parser.add_argument('--dryrun', dest='dryrun', help='dryrun', action='store_true')
        parser.add_argument('--mesa-dir', dest='mesa_dir', help='mesa dir')
        parser.add_argument('--run-manual', dest='run_manual', help='run manual', action='store_true')

        parser.epilog = '''
{0} {1} --batch
'''.format(Util.PYTHON, parser.prog)

        python_ver = Util.get_python_ver()
        if python_ver[0] == 3:
            super().__init__(parser)
        else:
            super(ChromeDrop, self).__init__(parser)

        args = self.args

        root_dir = self.root_dir
        self.angle_dir = '%s/angle' % self.root_dir
        self.chrome_dir = '%s/chromium/src' % root_dir
        self.chrome_backup_dir = '%s/chromium/backup' % self.root_dir
        self.dawn_dir = '%s/dawn' % self.root_dir
        if args.mesa_dir:
            self.mesa_dir = args.mesa_dir
        else:
            self.mesa_dir = '%s/mesa' % root_dir
        self.mesa_backup_dir = '%s/backup' % self.mesa_dir
        self.mesa_build_dir = '%s/build' % self.mesa_dir
        self.result_dir = '%s/result/%s' % (root_dir, self.timestamp)

        self.exec_log = '%s/exec.log' % self.result_dir
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

        self._handle_ops()

    def sync(self):
        if 'angle' in self.targets:
            cmd = '%s %s --sync --runhooks --root-dir %s' % (Util.PYTHON, Util.GNP_SCRIPT, self.angle_dir)
            self._execute(cmd)

        if 'dawn' in self.targets:
            cmd = '%s %s --sync --runhooks --root-dir %s' % (Util.PYTHON, Util.GNP_SCRIPT, self.dawn_dir)
            self._execute(cmd)

        if 'webgl' in self.targets:
            if self.target_os == Util.LINUX:
                self._execute('%s %s/mesa/mesa.py --sync --root-dir %s' % (Util.PYTHON, ScriptRepo.ROOT_DIR, self.mesa_dir))

            cmd = '%s %s --sync --runhooks --root-dir %s' % (Util.PYTHON, Util.GNP_SCRIPT, self.chrome_dir)
            if self.args.build_chrome_rev != 'latest':
                cmd += ' --rev %s' % self.args.build_chrome_rev
            self._execute(cmd)

    def build(self):
        # build mesa
        if self.target_os == Util.LINUX and not self.args.build_skip_mesa:
            self._execute('%s %s/mesa/mesa.py --build --root-dir %s' % (Util.PYTHON, ScriptRepo.ROOT_DIR, self.mesa_dir))

        if 'angle' in self.targets:
            cmd = '%s %s --makefile --build --build-target angle_e2e --backup --backup-target angle_e2e --root-dir %s' % (Util.PYTHON, Util.GNP_SCRIPT, self.angle_dir)
            self._execute(cmd)

        if 'dawn' in self.targets:
            cmd = '%s %s --makefile --build --build-target dawn_e2e --backup --backup-target dawn_e2e --root-dir %s' % (Util.PYTHON, Util.GNP_SCRIPT, self.dawn_dir)
            self._execute(cmd)

        if 'webgl' in self.targets and self.run_chrome_channel == 'build':
            if not self.args.build_skip_chrome:
                cmd = '%s %s --no-component-build --makefile --symbol-level 0 --build --build-target webgl --root-dir %s' % (Util.PYTHON, Util.GNP_SCRIPT, self.chrome_dir)
                self._execute(cmd)
            if not self.args.build_skip_backup:
                cmd = '%s %s --backup --backup-target webgl --root-dir %s' % (Util.PYTHON, Util.GNP_SCRIPT, self.chrome_dir)
                if self.target_os == Util.CHROMEOS:
                    cmd += ' --target-os chromeos'
                self._execute(cmd)

    def run(self):
        if self.target_os == Util.CHROMEOS:
            return
        Util.clear_proxy()

        if Util.HOST_OS == Util.LINUX:
            self.run_mesa_rev = Util.set_mesa(self.mesa_backup_dir, self.run_mesa_rev)

        gpu_name, gpu_driver, gpu_device_id = Util.get_gpu_info()
        Util.append_file(self.exec_log, 'GPU name%s%s' % (self.SEPARATOR, gpu_name))
        Util.append_file(self.exec_log, 'GPU driver%s%s' % (self.SEPARATOR, gpu_driver))
        Util.append_file(self.exec_log, 'GPU device id%s%s' % (self.SEPARATOR, gpu_device_id))

        if 'angle' in self.targets:
            cmd = '%s %s --run --run-target angle_e2e --run-rev latest --root-dir %s' % (Util.PYTHON, Util.GNP_SCRIPT, self.angle_dir)
            result_file = '%s/angle.json' % self.result_dir
            run_args = '--gtest_output=json:%s' % result_file
            if self.run_filter != 'all':
                run_args += ' --test-filter=*%s*' % self.run_filter
            if self.args.dryrun:
                run_args += ' --gtest_filter=*EGLAndroidFrameBufferTargetTest*'
            cmd += ' --run-args="%s"' % run_args
            self._execute(cmd)

            rev_name, _ = Util.get_backup_dir('%s/%s' % (self.angle_dir, 'backup'), 'latest')
            Util.append_file(self.exec_log, 'ANGLE Rev%s%s' % (self.SEPARATOR, rev_name))

        if 'dawn' in self.targets:
            cmd = '%s %s --run --run-target dawn_e2e --run-rev latest --root-dir %s' % (Util.PYTHON, Util.GNP_SCRIPT, self.dawn_dir)
            result_file = '%s/dawn.json' % self.result_dir
            run_args = '--gtest_output=json:%s' % result_file
            if self.run_filter != 'all':
                run_args += ' --test-filter=*%s*' % self.run_filter
            if self.args.dryrun:
                run_args += ' --gtest_filter=*BindGroupTests*'
            cmd += ' --run-args="%s"' % run_args
            self._execute(cmd)

            rev_name, _ = Util.get_backup_dir('%s/%s' % (self.dawn_dir, 'backup'), 'latest')
            Util.append_file(self.exec_log, 'Dawn Rev%s%s' % (self.SEPARATOR, rev_name))

        if 'webgl' in self.targets:
            Util.execute('vpython -m pip install pywin32 requests pathos six')
            common_cmd = 'vpython content/test/gpu/run_gpu_integration_test.py webgl_conformance --disable-log-uploads'
            if self.run_chrome_channel == 'build':
                self.chrome_rev = self.run_chrome_rev
                (chrome_rev_dir, self.chrome_rev) = Util.get_backup_dir(self.chrome_backup_dir, self.chrome_rev)
                chrome_rev_dir = '%s/%s' % (self.chrome_backup_dir, chrome_rev_dir)
                Util.chdir(chrome_rev_dir, verbose=True)
                Util.info('Use Chrome at %s' % chrome_rev_dir)

                if Util.HOST_OS == Util.WINDOWS:
                    chrome = 'out\Release\chrome.exe'
                else:
                    if os.path.exists('out/Release/chrome'):
                        chrome = 'out/Release/chrome'
                    else:
                        chrome = 'out/Default/chrome'

                common_cmd += ' --browser=exact --browser-executable=%s' % chrome
            else:
                common_cmd += ' --browser=%s' % self.run_chrome_channel
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
                self._execute('%s %s http://wp-27.sh.intel.com/workspace/project/WebGL/sdk/tests/webgl-conformance-tests.html?version=2.0.1' % (chrome, param))
                return

            if self.run_filter != 'all':
                common_cmd += ' --test-filter=*%s*' % self.run_filter
            if self.args.dryrun:
                #common_cmd += ' --test-filter=*copy-texture-image-same-texture*::*ext-texture-norm16*'
                common_cmd += ' --test-filter=*conformance/attribs*'

            if Util.HOST_OS in self.SKIP_CASES:
                skip_filter = self.SKIP_CASES[Util.HOST_OS]
                for skip_tmp in skip_filter:
                    common_cmd += ' --skip=%s' % skip_tmp
            if self.run_verbose:
                common_cmd += ' --verbose'

            Util.ensure_dir(self.result_dir)
            datetime = Util.get_datetime()

            COMB_INDEX_WEBGL = 0
            COMB_INDEX_BACKEND = 1
            if Util.HOST_OS in [Util.LINUX, Util.DARWIN]:
                all_combs = [['2.0.1']]
            elif Util.HOST_OS == Util.WINDOWS:
                all_combs = [
                    ['1.0.3', 'd3d9'],
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
                cmd = common_cmd + ' --webgl-conformance-version=%s' % comb[COMB_INDEX_WEBGL]
                result_file = ''
                if Util.HOST_OS == Util.LINUX:
                    result_file = '%s/webgl-%s.log' % (self.result_dir, comb[COMB_INDEX_WEBGL])
                elif Util.HOST_OS == Util.WINDOWS:
                    extra_browser_args += ' --use-angle=%s' % comb[COMB_INDEX_BACKEND]
                    result_file = '%s/webgl-%s-%s.log' % (self.result_dir, comb[COMB_INDEX_WEBGL], comb[COMB_INDEX_BACKEND])

                if extra_browser_args:
                    cmd += ' --extra-browser-args="%s"' % extra_browser_args
                cmd += ' --write-full-results-to %s' % result_file
                self._execute(cmd, exit_on_error=False, show_duration=True)

            rev_name, _ = Util.get_backup_dir('%s/%s' % (os.path.dirname(self.chrome_dir), 'backup'), 'latest')
            Util.append_file(self.exec_log, 'Chrome Rev%s%s' % (self.SEPARATOR, rev_name))

        self.report()

    def report(self):
        if self.args.report:
            self.result_dir = self.args.report

        regression_count = 0
        summary = 'Final summary:\n'
        details = 'Final details:\n'

        for result_file in os.listdir(self.result_dir):
            if 'angle' in result_file or 'dawn' in result_file:
                type = 'angle'
            elif 'webgl' in result_file:
                type = 'gtest_angle'
            else:
                continue
            pass_fail, fail_pass, fail_fail, pass_pass = Util.get_test_result('%s/%s' % (self.result_dir, result_file), type)
            regression_count += len(pass_fail)
            result = '%s: PASS_FAIL %s, FAIL_PASS %s, FAIL_FAIL %s PASS_PASS %s\n' % (os.path.splitext(result_file)[0], len(pass_fail), len(fail_pass), len(fail_fail), len(pass_pass))
            summary += result
            if pass_fail:
                result += '[PASS_FAIL]\n%s\n' % '\n'.join(pass_fail[:self.MAX_FAIL_IN_REPORT])
            if fail_pass:
                result += '[FAIL_PASS]\n%s\n' % '\n'.join(fail_pass[:self.MAX_FAIL_IN_REPORT])
            details += result

        Util.info(details)
        Util.info(summary)
        for line in open(self.exec_log).readlines():
            print(line.rstrip())

        report_file = '%s/report.txt' % self.result_dir
        Util.ensure_nofile(report_file)
        Util.append_file(report_file, summary)
        Util.append_file(report_file, details)

    def batch(self):
        self.sync()
        self.build()
        self.run()
        self.report()

    def _handle_ops(self):
        args = self.args
        if args.sync:
            self.sync()
        if args.build:
            self.build()
        if args.run:
            self.run()
        if args.report:
            self.report()
        if args.batch:
            self.batch()

if __name__ == '__main__':
    ChromeDrop()