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

result_file = ''

class Webmark():
    def __init__(self):
        global result_file

        self._parse_args()
        args = self.program.args

        config_file = args.config
        if not os.path.isfile(config_file):
            Util.error(config_file + ' is not a valid file')
        f = open(config_file)
        data = json.load(f)
        f.close()

        result_file = '%s/%s.txt' % (ScriptRepo.IGNORE_WEBMARK_RESULT_DIR, self.program.timestamp)
        Util.ensure_file(result_file)

        Suites(data).run()

    def _parse_args(self):
        parser = argparse.ArgumentParser(description='Automation tool to measure the performance of browser and web runtime with benchmarks',
                                        formatter_class=argparse.RawTextHelpFormatter,
                                        epilog='''
examples:
python %(prog)s --config config.json
    ''')

        parser.add_argument('--config', dest='config', help='config file to put in all the configurations')
        parser.add_argument('--dryrun', dest='codryrunnfig', help='dryrun')
        self.program = Program(parser)

class Suites():
    FORMAT = [
        ['suites', 'M', 'A'],
    ]

    def __init__(self, data):
        self.data = data
        self.suites = []
        Format.format(self)

    def run(self):
        for suite in self.suites:
            suite.run()

class Browser():
    FORMAT = [
        ['name', 'M', 'P'],
        ['path', 'O', 'P'],
        ['options', 'O', 'P'],
        ['webdriver_path', 'O', 'P'],
    ]

    def __init__(self, data):
        self.data = data
        Format.format(self)

class Suite():
    FORMAT = [
        ['name', 'O', 'P'],
        ['description', 'O', 'P'],
        ['browser', 'M', 'O'],
        ['cases', 'M', 'A'],
    ]

    def __init__(self, data):
        self.data = data
        self.cases = []
        Format.format(self)

    def run(self):
        if Util.HOST_OS == 'windows':
            webdriver = Util.get_webdriver(browser_name=self.browser.name, browser_path=self.browser.path, browser_options=self.browser.options, webdriver_path=self.browser.webdriver_path)
            for case in self.cases:
                case.run(webdriver)

            try:
                webdriver.quit()
            except Exception:
                pass

class Case():
    FORMAT = [
        ['name', 'M', 'P'],
        ['*', 'O', 'P'],
    ]

    def __init__(self, data):
        self.data = data
        Format.format(self)

    def run(self, driver):
        name = self.name
        exec('from benchmark.' + name.lower() + ' import ' + name)
        benchmark = eval(name)(driver, self)
        result = benchmark.run()
        f = open(result_file, 'a+')
        f.write(result + '\n')
        f.close()

class Format():
    NAME = 0
    REQUIRED = 1  # (O)ptional or (M)andatory
    TYPE = 2  # A for Array, O for Object, P for Property
    DEFAULT = 3

    @staticmethod
    def format_has_member(format, member):
        for f in format:
            if f[Format.NAME] == member or f[Format.NAME] == '*':
                return f
        return None

    @staticmethod
    def format(instance):
        # Check if all mandatory members in FORMAT are satisfied
        for format in instance.FORMAT:
            if format[Format.REQUIRED] == 'M' and not format[Format.NAME] in instance.data:
                Util.error(format[Format.NAME] + ' is not defined in ' + instance.__class__.__name__)
                quit()

        for member in instance.data:
            # Check all members in instance are recognized
            format = Format.format_has_member(instance.FORMAT, member)
            if not format:
                Util.warning('Can not recognize ' + member + ' in ' + instance.__class__.__name__)
                continue

            if format[Format.NAME] == '*':
                format_name = member
            else:
                format_name = format[Format.NAME]
            format_type = format[Format.TYPE]
            instance_data = instance.data[format_name]
            if format_type == 'P':
                instance.__dict__[format_name] = instance_data
            elif format_type == 'O':
                instance.__dict__[format_name] = eval(format_name.capitalize())(instance_data)
            elif format_type == 'A':
                for element in instance_data:
                    instance.__dict__[format_name].append(eval(format_name.capitalize()[:-1])(element))

        # set default
        for format in instance.FORMAT:
            format_name = format[Format.NAME]
            if not hasattr(instance, format_name):
                if len(format) > Format.DEFAULT:
                    instance.__dict__[format_name] = format_type = format[Format.DEFAULT]
                else:
                    format_type = format[Format.TYPE]
                    if format_type == 'P':
                        instance.__dict__[format_name] = ''
                    elif format_type == 'O':
                        instance.__dict__[format_name] = None
                    elif format_type == 'A':
                        instance.__dict__[format_name] = []

if __name__ == '__main__':
    Webmark()
