from benchmark.benchmark import *

class galactic(Benchmark):
    CONFIG = {
        'category': category_info['canvas2d'],
        'name': 'Galactic',
        'version': 'mobile',
        'metric': metric_info['fps'],
        'path': {
            'desktop': {
                'external': 'http://ie.microsoft.com/testdrive/Performance/Galactic/Default.html',
                'internal': 'webbench/canvas2d/microsoft/testdrive/Performance/Galactic/Default.html'
            },
            'mobile': {
                'external': 'http://ie.microsoft.com/testdrive/Performance/Galactic/Default.html',
                'internal': 'webbench/canvas2d/microsoft/testdrive/mobile/Performance/Galactic/'
            }
        },
    }

    def __init__(self, driver, case):
        super(galactic, self).__init__(driver, case)

    def cond0(self, driver):
        if self.version == 'mobile':
            self.e = driver.find_element_by_id('FPS_text')
            respite = 0
        elif self.version == 'desktop':
            self.e = driver.find_element_by_id('miniview')
            respite = 3
        else:
            error('version: %s is not supported' % self.version)

        if self.e:
            time.sleep(respite)
            return True
        else:
            return False

    def act0(self, driver):
        self.result = self.get_result_periodic(driver)

    def get_result_one(self, driver):
        return str(driver.execute_script('return gFpsData.AvgFps'))
