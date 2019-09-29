import os
import re
import subprocess
import sys
output = subprocess.Popen('ls -l %s' % __file__, shell=True, stdout=subprocess.PIPE).stdout.readline().decode('utf-8')
if re.search(str('->'), output):
    output = output.split(' ')[-1].strip()
    match = re.match('/(.)/', output)
    if match:
        drive = match.group(1)
        output = output.replace('/%s/' % drive, '%s:/' % drive)
    script_dir = os.path.dirname(os.path.realpath(output))
else:
    script_dir = sys.path[0]

sys.path.append(script_dir)
sys.path.append(script_dir + '/..')

from util.base import * # pylint: disable=unused-wildcard-import

class Webgl():
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
        self.mesa_dir = '%s/mesa' % root_dir
        self.mesa_build_dir = '%s/build' % self.mesa_dir
        self.depot_tools_dir = root_dir + '/depot_tools'
        self.test_dir = root_dir + '/test'
        Util.set_path(extra_path=self.depot_tools_dir.replace('/', '\\'))
        test_chrome = args.test_chrome
        if Util.host_os == 'darwin':
            if test_chrome == 'default':
                test_chrome = 'canary'
        else:
            if test_chrome == 'default':
                test_chrome = 'build'
        self.test_chrome = test_chrome
        self.result_dir = '%s/result' % self.test_dir

        if Util.host_os == 'linux':
            self.mesa_types = args.mesa_type.split(',')

        self.proxy = args.proxy
        self.skip_sync = args.skip_sync
        self. test_mesa_rev = args.test_mesa_rev
        self.test_filter = args.test_filter
        self.test_verbose = args.test_verbose
        self.test_chrome_rev = args.test_chrome_rev
        self.test_combs = args.test_combs
        self.email = args.email
        self.chrome_build_rev = args.chrome_build_rev

        self._handle_ops()

    def build(self):
        # build mesa
        if Util.host_os == 'linux':
            Util.chdir(self.mesa_dir)
            if not self.skip_sync:
                self.program.execute('python mesa.py --sync --root-dir %s' % self.mesa_dir)
            self.program.execute('python mesa.py --build --root-dir %s' % self.mesa_dir)

        # build chrome
        if self.test_chrome == 'build':
            Util.chdir(self.chrome_dir)
            if not self.skip_sync:
                cmd = 'python chromium.py --sync --runhooks --root-dir %s' % self.chrome_dir
                if self.chrome_build_rev != 'latest':
                    cmd += ' --rev %s' % self.chrome_build_rev
                self.program.execute(cmd)
            cmd = 'python chromium.py --makefile --build --backup-webgl --root-dir %s' % self.chrome_dir
            self.program.execute(cmd)

    def test(self, mesa_type=''):
        self.final_details = ''
        self.final_summary = ''
        if Util.host_os == 'linux':
            self.mesa_rev_number = self.test_mesa_rev
            if self.mesa_rev_number == 'system':
                Util.info('Use system Mesa')
            else:
                if self.mesa_rev_number == 'latest':
                    mesa_dir = self._get_latest('mesa')
                    self.mesa_rev_number = re.match('mesa-master-release-(.*)-', mesa_dir).group(1)
                else:
                    files = os.listdir(self.mesa_build_dir)
                    for file in files:
                        match = re.match('mesa-master-release-%s' % self.mesa_rev_number, file)
                        if match:
                            mesa_dir = file
                            break
                    else:
                        Util.error('Could not find mesa build %s' % self.mesa_rev_number)

                mesa_dir = self.mesa_build_dir + '/' + mesa_dir
                Util.set_env('LD_LIBRARY_PATH', mesa_dir + '/lib')
                Util.set_env('LIBGL_DRIVERS_PATH', mesa_dir + '/lib/dri')
                if mesa_type == 'iris':
                    Util.set_env('MESA_LOADER_DRIVER_OVERRIDE', 'iris')
                else:
                    Util.set_env('MESA_LOADER_DRIVER_OVERRIDE', '')
                Util.info('Use mesa at %s' % mesa_dir)

        common_cmd = 'vpython content/test/gpu/run_gpu_integration_test.py webgl_conformance --disable-log-uploads'
        if self.test_chrome == 'build':
            self.chrome_rev_number = self.test_chrome_rev
            if self.chrome_rev_number == 'latest':
                chrome_file = self._get_latest('chrome')
                self.chrome_rev_number = chrome_file.replace('.zip', '')
                if not re.match(r'\d{6}', self.chrome_rev_number):
                    Util.error('Could not find the correct revision')

            Util.chdir(self.chrome_build_dir)
            if not os.path.exists('%s' % self.chrome_rev_number):
                if not os.path.exists('%s.zip' % self.chrome_rev_number):
                    Util.error('Could not find Chromium revision %s' % self.chrome_rev_number)
                Util.ensure_dir(self.chrome_rev_number)
                self.program.execute('unzip %s.zip -d %s' % (self.chrome_rev_number, self.chrome_rev_number))

            chrome_rev_dir = '%s/%s' % (self.chrome_build_dir, self.chrome_rev_number)
            Util.chdir(chrome_rev_dir)
            Util.info('Use Chrome at %s' % chrome_rev_dir)

            if Util.host_os == 'windows':
                chrome = 'out\Default\chrome.exe'
            else:
                chrome = 'out/Default/chrome'

            common_cmd += ' --browser=exact --browser-executable=%s' % chrome
        else:
            common_cmd += ' --browser=%s' % self.test_chrome
            Util.chdir(self.chrome_src_dir)
            self.chrome_rev_number = self.test_chrome
            if Util.host_os == 'darwin':
                if self.test_chrome == 'canary':
                    chrome = '"/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"'
                else:
                    Util.error('test_chrome is not supported')
            elif Util.host_os == 'linux':
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
            self.program.execute('%s %s http://wp-27.sh.intel.com/workspace/project/readonly/WebGL/sdk/tests/webgl-conformance-tests.html?version=2.0.1' % (chrome, param))
            return

        if self.test_filter != 'all':
            common_cmd += ' --test-filter=%s' % self.test_filter
        skip_filter = self.skip_cases[Util.host_os]
        if skip_filter:
            for skip_tmp in skip_filter:
                common_cmd += ' --skip=%s' % skip_tmp
        if self.test_verbose:
            common_cmd += ' --verbose'

        Util.ensure_dir(self.result_dir)
        datetime = Util.get_datetime()

        COMB_INDEX_WEBGL = 0
        COMB_INDEX_D3D = 1
        if Util.host_os in ['linux', 'darwin']:
            all_combs = [['2.0.1']]
        elif Util.host_os == 'windows':
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
            cmd = common_cmd + ' --webgl-conformance-version=%s' % comb[COMB_INDEX_WEBGL]
            self.result_file = ''
            if Util.host_os == 'linux':
                self.result_file = '%s/%s-%s-%s-%s-%s.log' % (self.result_dir, datetime, self.chrome_rev_number, mesa_type, self.mesa_rev_number, comb[COMB_INDEX_WEBGL])
            elif Util.host_os == 'windows':
                if comb[COMB_INDEX_D3D] != '11':
                    extra_browser_args += ' --use-angle=d3d%s' % comb[COMB_INDEX_D3D]
                self.result_file = '%s/%s-%s-%s-%s.log' % (self.result_dir, datetime, self.chrome_rev_number, comb[COMB_INDEX_WEBGL], comb[COMB_INDEX_D3D])
            elif Util.host_os == 'darwin':
                self.result_file = '%s/%s-%s-%s.log' % (self.result_dir, datetime, self.chrome_rev_number, comb[COMB_INDEX_WEBGL])
            if extra_browser_args:
                cmd += ' --extra-browser-args="%s"' % extra_browser_args
            cmd += ' --write-full-results-to %s' % self.result_file
            result = self.program.execute(cmd)
            if result[0]:
                Util.warning('Failed to run test "%s"' % cmd)

            self.report(mesa_type=mesa_type)

        Util.info('Final details:\n%s' % self.final_details)
        Util.info('Final summary:\n%s' % self.final_summary)

    def run(self):
        if Util.host_os == 'linux':
            if len(self.mesa_types) > 1:
                Util.error('Only one mesa_type is support for run')
            mesa_type = self.mesa_types[0]
            test(mesa_type=mesa_type)
        else:
            test()

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

        if Util.host_os == 'linux':
            subject = 'WebGL CTS on Chrome %s and Mesa %s %s has %s Regression' % (self.chrome_rev_number, mesa_type, self.mesa_rev_number, json_result['num_regressions'])
        else:
            subject = 'WebGL CTS on Chrome %s has %s Regression' % (self.chrome_rev_number, json_result['num_regressions'])

        self.final_details += subject + '\n' + content
        Util.info(subject)
        Util.info(content)

        if self.program.args.daily and Util.host_os == 'linux' or self.email:
            Util.send_email('webperf@intel.com', 'yang.gu@intel.com', subject, content)

    def daily(self):
        self.build()
        if Util.host_os == 'linux':
            for mesa_type in self.mesa_types:
                test(mesa_type=mesa_type)
        else:
            test()

    def _parse_arg(self):
        parser = argparse.ArgumentParser(description='Chromium WebGL',
                                        formatter_class=argparse.RawTextHelpFormatter,
                                        epilog='''
examples:
python %(prog)s --proxy <host>:<port> --build --build-chrome-hash <hash>
python %(prog)s --test
    ''')
        parser.add_argument('--proxy', dest='proxy', help='proxy')
        parser.add_argument('--build', dest='build', help='build', action='store_true')
        parser.add_argument('--chrome-build-rev', dest='chrome_build_rev', help='Chrome rev to build', default='latest')
        parser.add_argument('--test', dest='test', help='test', action='store_true')
        parser.add_argument('--test-chrome-rev', dest='test_chrome_rev', help='Chromium revision', default='latest')
        parser.add_argument('--test-mesa-rev', dest='test_mesa_rev', help='mesa revision', default='latest')
        parser.add_argument('--test-filter', dest='test_filter', help='WebGL CTS suite to test against', default='all')  # For smoke test, we may use conformance_attribs
        parser.add_argument('--test-verbose', dest='test_verbose', help='verbose mode of test', action='store_true')
        parser.add_argument('--test-chrome', dest='test_chrome', help='test chrome', default='default')
        parser.add_argument('--test-combs', dest='test_combs', help='test combs, split by comma, like "0,2"', default='all')
        parser.add_argument('--daily', dest='daily', help='daily test', action='store_true')
        parser.add_argument('--run', dest='run', help='run', action='store_true')
        parser.add_argument('--dryrun', dest='dryrun', help='dryrun', action='store_true')
        parser.add_argument('--report', dest='report', help='report file')
        parser.add_argument('--email', dest='email', help='send report as email', action='store_true')
        parser.add_argument('--skip-sync', dest='skip_sync', help='skip sync', action='store_true')
        parser.add_argument('--mesa-type', dest='mesa_type', help='mesa type', default='i965,iris')

        self.program = Program(parser)

    def _handle_ops(self):
        args = self.program.args
        if args.build:
            self.build()
        if args.test:
            self.test()
        if args.run:
            self.run()
        if args.report:
            self.report()
        if args.daily:
            self.daily()

    def _get_latest(self, type):
        if type == 'mesa':
            rev_dir = self.mesa_build_dir
            rev_pattern = 'mesa-master-release-(.*)-'
        elif type == 'chrome':
            rev_dir = self.chrome_build_dir
            rev_pattern = '(\d{6}).zip'

        latest_rev = -1
        latest_file = ''
        files = os.listdir(rev_dir)
        for file in files:
            match = re.search(rev_pattern, file)
            if match:
                tmp_rev = int(match.group(1))
                if tmp_rev > latest_rev:
                    latest_file = file
                    latest_rev = tmp_rev

        return latest_file

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
    Webgl()
