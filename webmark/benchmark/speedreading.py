from benchmark.benchmark import *

class speedreading(Benchmark):
    CONFIG = {
        'category': category_info['canvas2d'],
        'name': 'SpeedReading',
        'metric': metric_info['fps'],
        'version': 'mod',
        'path': {
            'setinterval': {
                'external': 'http://ie.microsoft.com/testdrive/Performance/SpeedReading/',
                'internal': 'webbench/canvas2d/microsoft/testdrive/Performance/SpeedReading/'
            },
            'mod': {
                'external': '',
                'internal': 'webbench/canvas2d/microsoft/testdrive/Performance/SpeedReading-mod/'
            }
        },
        'timeout': 1200,
    }

    def __init__(self, driver, case):
        super(speedreading, self).__init__(driver, case)

    def cond0(self, driver):
        return driver.execute_script('return startButtonVisible')

    def act0(self, driver):
        driver.execute_script('StartButtonClicked()')

    def cond1(self, driver):
        return driver.execute_script('return tryAgainButtonVisible')

    def act1(self, driver):
        self.result = [driver.execute_script('fps = Math.floor(1000 / perf.averageDrawTime); return (fps > 57) ? 60 : fps;')]
