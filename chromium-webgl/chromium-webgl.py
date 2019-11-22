import os
import re
import subprocess
import sys
lines = subprocess.Popen('dir %s' % __file__, shell=True, stdout=subprocess.PIPE).stdout.readlines()
for line in lines:
    match = re.search(r'\[(.*)\]', line.decode('utf-8'))
    if match:
        script_dir = os.path.dirname(match.group(1)).replace('\\', '/')
        break
else:
    script_dir = sys.path[0]

sys.path.append(script_dir)
sys.path.append(script_dir + '/..')

from util.base import * # pylint: disable=unused-wildcard-import

class ChromiumWebgl():
    def __init__(self):
        self.skip_cases = {
            #'linux': ['WebglConformance_conformance2_textures_misc_tex_3d_size_limit'],
            'linux': [],
            'windows': [],
            'darwin': [],
        }

        self._parse_arg()
        args = self.program.args
        root_dir = self.program.root_dir
        self.chrome_dir = '%s/chromium' % root_dir
        self.chrome_build_dir = '%s/build' % self.chrome_dir
        self.chrome_src_dir = '%s/src' % self.chrome_dir
        if args.mesa_dir:
            self.mesa_dir = args.mesa_dir
        else:
            self.mesa_dir = '%s/mesa' % root_dir
        self.mesa_build_dir = '%s/build' % self.mesa_dir
        self.depot_tools_dir = '%s/depot_tools' % root_dir
        self.test_dir = '%s/test' % root_dir
        Util.prepend_path(path=self.depot_tools_dir)
        Util.set_env('GCLIENT_PY3', '1')
        test_chrome = args.test_chrome
        if Util.HOST_OS == 'darwin':
            if test_chrome == 'default':
                test_chrome = 'canary'
        else:
            if test_chrome == 'default':
                test_chrome = 'build'
        self.test_chrome = test_chrome
        self.result_dir = '%s/result' % self.test_dir

        if Util.HOST_OS == 'linux':
            mesa_type = args.mesa_type
            if mesa_type == 'default':
                if args.daily:
                    mesa_type = 'i965,iris'
                else:
                    mesa_type = 'i965'
            self.mesa_types = mesa_type.split(',')

        self.proxy = args.proxy
        self.build_skip_sync = args.build_skip_sync
        self.build_skip_chrome = args.build_skip_chrome
        self.build_skip_mesa = args.build_skip_mesa
        self.build_chrome_rev = args.build_chrome_rev
        self.test_mesa_rev = args.test_mesa_rev
        self.test_filter = args.test_filter
        self.test_verbose = args.test_verbose
        self.test_chrome_rev = args.test_chrome_rev
        self.test_combs = args.test_combs
        self.email = args.email
        self.test_no_angle = args.test_no_angle

        self._handle_ops()

    def build(self):
        # build mesa
        if Util.HOST_OS == 'linux' and not self.build_skip_mesa:
            Util.chdir(self.mesa_dir)
            if not self.build_skip_sync:
                self.program.execute('python %s/mesa/mesa.py --sync --root-dir %s' % (ScriptRepo.ROOT_DIR, self.mesa_dir))
            self.program.execute('python %s/mesa/mesa.py --build --root-dir %s' % (ScriptRepo.ROOT_DIR, self.mesa_dir))

        # build chrome
        if self.test_chrome == 'build' and not self.build_skip_chrome:
            Util.chdir('%s/chromium' % ScriptRepo.ROOT_DIR)
            if not self.build_skip_sync:
                cmd = 'python chromium.py --sync --runhooks --root-dir %s' % self.chrome_dir
                if self.build_chrome_rev != 'latest':
                    cmd += ' --rev %s' % self.build_chrome_rev
                self.program.execute(cmd, exit_on_error=False)
            Util.ensure_dir('%s/build' % self.chrome_dir)
            self.program.execute('python chromium.py --no-component-build --makefile --build --backup-webgl --out-dir out --root-dir %s' % self.chrome_dir)

    def test(self, mesa_type=''):
        self.final_details = ''
        self.final_summary = ''

        if Util.HOST_OS == 'linux':
            self.mesa_rev = self.test_mesa_rev
            if self.mesa_rev == 'system':
                Util.info('Use system Mesa')
            else:
                (rev_dir, self.mesa_rev) = Util.get_rev_dir(self.mesa_build_dir, 'mesa', self.mesa_rev)
                mesa_dir = self.mesa_build_dir + '/' + rev_dir
                Util.set_env('LD_LIBRARY_PATH', mesa_dir + '/lib')
                Util.set_env('LIBGL_DRIVERS_PATH', mesa_dir + '/lib/dri')
                if mesa_type == 'iris':
                    Util.set_env('MESA_LOADER_DRIVER_OVERRIDE', 'iris')
                else:
                    Util.set_env('MESA_LOADER_DRIVER_OVERRIDE', '')
                Util.info('Use mesa at %s' % mesa_dir)

        common_cmd = 'vpython content/test/gpu/run_gpu_integration_test.py webgl_conformance --disable-log-uploads'
        if self.test_chrome == 'build':
            self.chrome_rev = self.test_chrome_rev
            (_, self.chrome_rev) = Util.get_rev_dir(self.chrome_build_dir, 'chrome', self.chrome_rev)

            Util.chdir(self.chrome_build_dir)
            if not os.path.exists('%s' % self.chrome_rev):
                if not os.path.exists('%s.zip' % self.chrome_rev):
                    Util.error('Could not find Chromium revision %s' % self.chrome_rev)
                Util.ensure_dir(str(self.chrome_rev))
                self.program.execute('unzip %s.zip -d %s' % (self.chrome_rev, self.chrome_rev))

            chrome_rev_dir = '%s/%s' % (self.chrome_build_dir, self.chrome_rev)
            Util.chdir(chrome_rev_dir)
            Util.info('Use Chrome at %s' % chrome_rev_dir)

            if Util.HOST_OS == 'windows':
                chrome = 'out\Release\chrome.exe'
            else:
                if os.path.exists('out/Release/chrome'):
                    chrome = 'out/Release/chrome'
                else:
                    chrome = 'out/Default/chrome'

            common_cmd += ' --browser=exact --browser-executable=%s' % chrome
        else:
            common_cmd += ' --browser=%s' % self.test_chrome
            Util.chdir(self.chrome_src_dir)
            self.chrome_rev = self.test_chrome
            if Util.HOST_OS == 'darwin':
                if self.test_chrome == 'canary':
                    chrome = '"/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"'
                else:
                    Util.error('test_chrome is not supported')
            elif Util.HOST_OS == 'linux':
                if self.test_chrome == 'canary':
                    chrome = '/usr/bin/google-chrome-unstable'
                elif self.test_chrome == 'stable':
                    chrome = '/usr/bin/google-chrome-stable'
                else:
                    Util.error('test_chrome is not supported')
            else:
                Util.error('test_chrome is not supported')

        if self.program.args.run:
            param = '--enable-experimental-web-platform-features --disable-gpu-process-for-dx12-vulkan-info-collection --disable-domain-blocking-for-3d-apis --disable-gpu-process-crash-limit --disable-blink-features=WebXR --js-flags=--expose-gc --disable-gpu-watchdog --autoplay-policy=no-user-gesture-required --disable-features=UseSurfaceLayerForVideo --enable-net-benchmarking --metrics-recording-only --no-default-browser-check --no-first-run --ignore-background-tasks --enable-gpu-benchmarking --deny-permission-prompts --autoplay-policy=no-user-gesture-required --disable-background-networking --disable-component-extensions-with-background-pages --disable-default-apps --disable-search-geolocation-disclosure --enable-crash-reporter-for-testing --disable-component-update'
            param += ' --use-gl=angle'
            if Util.HOST_OS == 'linux' and self.test_no_angle:
                param += ' --use-gl=desktop'
            self.program.execute('%s %s http://wp-27.sh.intel.com/workspace/project/readonly/WebGL/sdk/tests/webgl-conformance-tests.html?version=2.0.1' % (chrome, param))
            return

        if self.test_filter != 'all':
            common_cmd += ' --test-filter=%s' % self.test_filter
        skip_filter = self.skip_cases[Util.HOST_OS]
        if skip_filter:
            for skip_tmp in skip_filter:
                common_cmd += ' --skip=%s' % skip_tmp
        if self.test_verbose:
            common_cmd += ' --verbose'

        Util.ensure_dir(self.result_dir)
        datetime = Util.get_datetime()

        COMB_INDEX_WEBGL = 0
        COMB_INDEX_D3D = 1
        if Util.HOST_OS in ['linux', 'darwin']:
            all_combs = [['2.0.1']]
        elif Util.HOST_OS == 'windows':
            all_combs = [
                ['1.0.3', '9'],
                ['1.0.3', '11'],
                ['2.0.1', '11'],
            ]

        test_combs = []
        if self.test_combs == 'all':
            test_combs = all_combs
        else:
            for i in self.test_combs.split(','):
                test_combs.append(all_combs[int(i)])

        for comb in test_combs:
            extra_browser_args = '--disable-backgrounding-occluded-windows'
            if Util.HOST_OS == 'linux' and self.test_no_angle:
                extra_browser_args += ',--use-gl=desktop'
            cmd = common_cmd + ' --webgl-conformance-version=%s' % comb[COMB_INDEX_WEBGL]
            self.result_file = ''
            if Util.HOST_OS == 'linux':
                self.result_file = '%s/%s-%s-%s-%s-%s.log' % (self.result_dir, datetime, self.chrome_rev, mesa_type, self.mesa_rev, comb[COMB_INDEX_WEBGL])
            elif Util.HOST_OS == 'windows':
                if comb[COMB_INDEX_D3D] != '11':
                    extra_browser_args += ' --use-angle=d3d%s' % comb[COMB_INDEX_D3D]
                self.result_file = '%s/%s-%s-%s-%s.log' % (self.result_dir, datetime, self.chrome_rev, comb[COMB_INDEX_WEBGL], comb[COMB_INDEX_D3D])
            elif Util.HOST_OS == 'darwin':
                self.result_file = '%s/%s-%s-%s.log' % (self.result_dir, datetime, self.chrome_rev, comb[COMB_INDEX_WEBGL])

            if extra_browser_args:
                cmd += ' --extra-browser-args="%s"' % extra_browser_args
            cmd += ' --write-full-results-to %s' % self.result_file
            result = self.program.execute(cmd, exit_on_error=False)
            self.report(mesa_type=mesa_type)

        Util.info('Final details:\n%s' % self.final_details)
        Util.info('Final summary:\n%s' % self.final_summary)

    def run(self):
        if Util.HOST_OS == 'linux':
            if len(self.mesa_types) > 1:
                Util.error('Only one mesa_type is support for run')
            mesa_type = self.mesa_types[0]
            self.test(mesa_type=mesa_type)
        else:
            self.test()

    def report(self, mesa_type=''):
        self.fail_fail = []
        self.fail_pass = []
        self.pass_fail = []
        self.pass_pass = []

        if self.program.args.report:
            self.result_file = '%s/%s' % (self.result_dir, self.program.args.report)

        json_result = json.load(open(self.result_file))
        result_type = json_result['num_failures_by_type']
        test_results = json_result['tests']
        for key, val in test_results.items():
            self._parse_result(key, val, key)

        content = 'FAIL: %s (New: %s, Expected: %s), PASS %s (New: %s, Expected: %s), SKIP: %s\n' % (result_type['FAIL'], len(self.pass_fail), len(self.fail_fail), result_type['PASS'], len(self.fail_pass), len(self.pass_pass), result_type['SKIP'])
        self.final_summary+= '\n' + content
        content += '[PASS_FAIL(%s)]\n' % len(self.pass_fail)
        if self.pass_fail:
            for c in self.pass_fail:
                content += c + '\n'

        content += '[FAIL_PASS(%s)]\n' % len(self.fail_pass)
        if self.fail_pass:
            for c in self.fail_pass:
                content += c + '\n'

        content += '[FAIL_FAIL(%s)]\n' % len(self.fail_fail)
        if self.fail_fail:
            for c in self.fail_fail:
                content += c + '\n'

        if Util.HOST_OS == 'linux':
            subject = 'WebGL CTS on Chrome %s and Mesa %s %s has %s Regression' % (self.chrome_rev, mesa_type, self.mesa_rev, json_result['num_regressions'])
        else:
            subject = 'WebGL CTS on Chrome %s has %s Regression' % (self.chrome_rev, json_result['num_regressions'])

        self.final_details += subject + '\n' + content
        Util.info(subject)
        Util.info(content)

        if self.program.args.daily and Util.HOST_OS == 'linux' or self.email:
            Util.send_email('webperf@intel.com', 'yang.gu@intel.com', subject, content)

    def daily(self):
        self.build()
        if Util.HOST_OS == 'linux':
            for mesa_type in self.mesa_types:
                self.test(mesa_type=mesa_type)
        else:
            self.test()

    def _parse_arg(self):
        parser = argparse.ArgumentParser(description='Chromium WebGL',
                                        formatter_class=argparse.RawTextHelpFormatter,
                                        epilog='''
examples:
python %(prog)s --build --build-chrome-hash <hash>
python %(prog)s --test
    ''')
        parser.add_argument('--build', dest='build', help='build', action='store_true')
        parser.add_argument('--build-chrome-rev', dest='build_chrome_rev', help='Chrome rev to build', default='latest')
        parser.add_argument('--build-skip-sync', dest='build_skip_sync', help='skip sync during build', action='store_true')
        parser.add_argument('--build-skip-chrome', dest='build_skip_chrome', help='skip building chrome during build', action='store_true')
        parser.add_argument('--build-skip-mesa', dest='build_skip_mesa', help='skip skip building mesa during build', action='store_true')
        parser.add_argument('--test', dest='test', help='test', action='store_true')
        parser.add_argument('--test-chrome-rev', dest='test_chrome_rev', help='Chromium revision', default='latest')
        parser.add_argument('--test-mesa-rev', dest='test_mesa_rev', help='mesa revision', default='latest')
        parser.add_argument('--test-filter', dest='test_filter', help='WebGL CTS suite to test against', default='all')  # For smoke test, we may use conformance_attribs
        parser.add_argument('--test-verbose', dest='test_verbose', help='verbose mode of test', action='store_true')
        parser.add_argument('--test-chrome', dest='test_chrome', help='test chrome', default='default')
        parser.add_argument('--test-combs', dest='test_combs', help='test combs, split by comma, like "0,2"', default='all')
        parser.add_argument('--test-no-angle', dest='test_no_angle', help='test without angle', action='store_true')
        parser.add_argument('--daily', dest='daily', help='daily test', action='store_true')
        parser.add_argument('--run', dest='run', help='run', action='store_true')
        parser.add_argument('--dryrun', dest='dryrun', help='dryrun', action='store_true')
        parser.add_argument('--report', dest='report', help='report file')
        parser.add_argument('--email', dest='email', help='send report as email', action='store_true')
        parser.add_argument('--mesa-type', dest='mesa_type', help='mesa type', default='default')
        parser.add_argument('--mesa-dir', dest='mesa_dir', help='mesa dir')

        self.program = Program(parser)

    def _handle_ops(self):
        args = self.program.args
        if args.build:
            self.build()
        if args.test:
            if re.search(',', args.mesa_type) and Util.HOST_OS == 'linux':
                Util.error('Only one mesa_type can be designated!')
            self.test(mesa_type=args.mesa_type)
        if args.report:
            if re.search(',', args.mesa_type) and Util.HOST_OS == 'linux':
                Util.error('Only one mesa_type can be designated!')
            self.report(mesa_type=args.mesa_type)
        if args.run:
            self.run()
        if args.daily:
            self.daily()

    def _parse_result(self, key, val, path):
        if 'expected' in val:
            if val['expected'] == 'FAIL' and val['actual'] == 'FAIL':
                self.fail_fail.append(path)
            elif val['expected'] == 'FAIL' and val['actual'] == 'PASS':
                self.fail_pass.append(path)
            elif val['expected'] == 'PASS' and val['actual'] == 'FAIL':
                self.pass_fail.append(path)
            elif val['expected'] == 'PASS' and val['actual'] == 'PASS':
                self.pass_pass.append(path)
        else:
            for new_key, new_val in val.items():
                self._parse_result(new_key, new_val, '%s/%s' % (path, new_key))

if __name__ == '__main__':
    ChromiumWebgl()
