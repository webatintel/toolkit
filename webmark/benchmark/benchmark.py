import os
import platform
import re
import subprocess
import sys

HOST_OS = sys.platform
if HOST_OS == 'win32':
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

category_info = {
    'comprehensive': 'Comprehensive',
    'js': 'JavaScript',
    'canvas2d': 'Canvas2D',
    'webgl': 'WebGL',
    'css': 'CSS',
    'webaudio': 'WebAudio',
    'webvideo': 'WebVideo',
    'webtouch': 'WebTouch',
    'fileop': 'FileOperation',
    'localstorage': 'LocalStorage',
    'render': 'PageRendering',
}

metric_info = {
    'score': 'Score(+)',
    'fps': 'FPS(+)',
    'ms': 'ms(-)',
    's': 's(-)'
}

class Benchmark(object):
    def __init__(self, driver, case):
        self.driver = driver

        # handle states
        funcs = [func for func in dir(self) if callable(getattr(self, func))]
        self.states = []
        self.run_fail = False
        count = 0
        pattern_cond = re.compile('cond(\d+)')
        for func in funcs:
            match = pattern_cond.match(func)
            if match:
                count_temp = int(match.group(1))
                if count_temp > count:
                    count = count_temp
        for i in range(count + 1):
            self.states.append([getattr(self, 'cond' + str(i)), getattr(self, 'act' + str(i))])

        # handle general members
        config = self.CONFIG
        members = {
            'category': 'NA',
            'name': 'NA',
            'version': 'NA',
            'metric': 'NA',
            'path_type': 'internal',
            'timeout': 300,
            'sleep': 3,
            'times_run': 1,
            'times_skip': 0,
            'dryrun': False,
            'stat': 'average',
            'orientation': 'landscape',
            'device_id': 'NA',
            'target_os': 'NA',
        }
        for key in members:
            if key == 'name':
                if key in config:
                    self.__dict__[key] = config[key]
                else:
                    self.__dict__[key] = getattr(case, key)
                continue

            if hasattr(case, key):
                self.__dict__[key] = getattr(case, key)
            elif key in config:
                self.__dict__[key] = config[key]
            else:
                self.__dict__[key] = members[key]

        # handle path
        key = 'path'
        if hasattr(case, key):
            self.__dict__[key] = getattr(case, key)
        elif key in config:
            if self.version in config[key]:
                self.__dict__[key] = config[key][self.version][self.path_type]
            else:
                self.__dict__[key] = config[key][self.path_type]
        if self.path_type == 'internal':
            if not re.match('http', self.__dict__[key]):
                self.__dict__[key] = Util.INTERNAL_WEBSERVER_WEBBENCH + '/' + self.__dict__[key]
        elif self.path_type == 'local':
            self.__dict__[key] = 'file:///data/local/tmp/' + self.__dict__[key]

    def get_result(self, driver):
        if self.dryrun:
            return [str(random.randint(1, 60))]
        elif self.run_fail:
            return ['0.0']
        else:
            return self.result

    def get_result_one(self, driver):
        return '0.0'

    def get_result_periodic(self, driver, count=5, period=3):
        result = 0.0
        for i in range(1, count + 1):
            time.sleep(period)
            result_one = float(self.get_result_one(driver))
            if self.CONFIG["metric"] == metric_info['fps'] and result_one > 60:
                result_one = 60
            Util.info('Periodic result: %s' % result_one)
            result += (result_one - result) / i

        return [str(round(result, 2))]

    # Each specific benchmark only returns result in string format, we will convert them to float here.
    def run(self):
            Util.info('Begin to run "%s" version "%s"' % (self.name, self.version))
            times_run = self.times_run
            times_skip = self.times_skip
            driver = self.driver

            results = []
            for i in range(times_run):
                self.result = []
                self.state = 0
                if not self.dryrun:
                    print(self.path)
                    driver.get(self.path)
                    try:
                        WebDriverWait(driver, self.timeout, self.sleep).until(self._is_finished)
                    except Exception:
                        self.run_fail = True
                if times_skip > 0:
                    times_skip = times_skip - 1
                    continue
                result = self.get_result(driver)
                Util.info('Round result: ' + ','.join([str(x) for x in result]))
                results.append([float(x) for x in result])
                if self.run_fail:
                    break

            count_results = len(results)
            if count_results == 0:
                Util.error('There is no result for ' + self.name)

            results = sorted(results, key=lambda i: i[0])
            results_final = []
            if self.stat == 'median':
                count_results = len(results)
                if count_results % 2:
                    results_final = results[(count_results - 1) / 2]
                else:
                    results_total = results[(count_results - 1) / 2]
                    count_result = len(results[0])
                    for i in range(count_result):
                        results_total[i] += results[(count_results - 1) / 2 + 1][i]
                    for i in range(count_result):
                        results_final.append(round(results_total[i] / 2, 2))
            elif self.stat == 'average':
                results_total = results[0]
                count_result = len(results[0])
                for i in range(1, count_results):
                    for j in range(count_result):
                        results_total[j] += results[i][j]

                for i in range(count_result):
                    results_final.append(round(results_total[i] / count_results, 2))
            elif self.stat == 'min' or self.stat == 'max':
                if self.stat == 'min':
                    results_final = results[0]
                else:
                    results_final = results[-1]

            outputs = []
            for item in ['category', 'name', 'version', 'metric', 'result']:
                if item == 'category':
                    outputs.append(self.category)
                elif item == 'name':
                    outputs.append(self.__class__.__name__)
                elif item == 'version':
                    outputs.append(self.version)
                elif item == 'metric':
                    outputs.append(self.metric)
                elif item == 'result':
                    outputs.append(','.join(str(x) for x in results_final))
            return 'Case result: ' + ','.join(outputs)

    def inject_jperf(self, driver):
        if self.path_type == 'internal':
            js = '%s/jperf/jperf.js' % Util.INTERNAL_WEBSERVER_WEBBENCH
        else:
            js = 'https://raw.githubusercontent.com/gyagp/webbench/master/jperf/jperf.js'
        self.inject_js(driver, js)

    def inject_js(self, driver, js):
        script = '''
    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = '%s';
    document.head.appendChild(script);
        ''' % js
        driver.execute_script('{' + script + '}')
        time.sleep(3)

    def _is_finished(self, driver):
        if self.states[self.state][0](driver):
            act = self.states[self.state][1]
            if act:
                act(driver)
            self.state += 1
            if self.state == len(self.states):
                return True
        return False

class CssBenchmark(Benchmark):
    def inject_css_fps(self, driver):
        self.inject_jperf(driver)
        script = '''
    var cssFpsElement = document.createElement('div');
    var style = 'float:left; width:800px; height:30px: color:red;';
    cssFpsElement.setAttribute('style', style);
    cssFpsElement.setAttribute('id', 'css-fps');
    cssFpsElement.innerHTML = 'Recent FPS: 0, Average FPS: 0';
    document.body.appendChild(cssFpsElement);

    var cssFpsMeter = new window.jPerf.CSSFPSMeter();
    cssFpsMeter.start();
    document.addEventListener('CSSFPSReport',
      function(event) {
        cssFpsElement.innerHTML = 'Recent FPS: ' + event.recentFPS + ', Average FPS: ' + event.averageFPS;
      },
      false
    );
        '''
        driver.execute_script(script)

    def get_css_fps(self, driver):
        match = re.search('Average FPS: (.*)', driver.find_element_by_id('css-fps').get_attribute('innerText'))
        return match.group(1)
