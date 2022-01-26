import unittest
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

class WebdriverTest(Program):
    def __init__(self, parser):
        parser.add_argument('--browser-name', dest='browser_name', default='chrome_canary', help='browser name')
        parser.epilog = '''
examples:
{0} {1} --browser-name chrome_beta
'''.format(Util.PYTHON, parser.prog)

        python_ver = Util.get_python_ver()
        if python_ver[0] == 3:
            super().__init__(parser)
        else:
            super(WebdriverTest, self).__init__(parser)
        args = self.args

        Util.clear_proxy()
        driver = Util.get_webdriver(browser_name=args.browser_name, debug=True)
        driver.get('https://www.figma.com/proto/wAfdtgm44S6eV0LumCHt46/Prototyping-in-Figma?node-id=0%3A627&scaling=min-zoom&page-id=0%3A1&starting-point-node-id=0%3A2')

        if (True):
            #element = driver.find_element(By.TAG_NAME, 'body')
            element = driver.find_element(By.XPATH, '//*[@id="viewerContainer"]/div/div/canvas')
            for i in range(10):
                print('right key')
                element.send_keys(Keys.ARROW_RIGHT)
                time.sleep(3)
            for i in range(2):
                print('left key')
                element.send_keys(Keys.ARROW_LEFT)
                time.sleep(2)
        time.sleep(5)
        #self.driver.quit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='test webdriver')
    WebdriverTest(parser)
