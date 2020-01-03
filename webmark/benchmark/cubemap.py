from benchmark.benchmark import *

class cubemap(Benchmark):
    CONFIG = {
        'category': category_info['webgl'],
        'name': 'Dynamic Cubemap',
        'metric': metric_info['fps'],
        'path': {
            'external': 'http://webglsamples.googlecode.com/hg/dynamic-cubemap/dynamic-cubemap.html',
            'internal': 'webbench/webgl/webglsamples/dynamic-cubemap/dynamic-cubemap.html'
        },
    }

    def __init__(self, driver, case):
        super(cubemap, self).__init__(driver, case)

    def cond0(self, driver):
        self.e = driver.find_element_by_id('fps')
        if self.e:
            return True
        else:
            return False

    def act0(self, driver):
        self.result = self.get_result_periodic(driver)

    def get_result_one(self, driver):
        return self.e.get_attribute('innerText')
