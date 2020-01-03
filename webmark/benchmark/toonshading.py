from benchmark.benchmark import *

class toonshading(Benchmark):
    CONFIG = {
        'category': category_info['webgl'],
        'name': 'Toon Shading',
        'metric': metric_info['fps'],
        'path': {
            'external': 'http://webglsamples.googlecode.com/hg/toon-shading/toon-shading.html',
            'internal': 'webbench/webgl/webglsamples/toon-shading/toon-shading.html'
        },
    }

    def __init__(self, driver, case):
        super(toonshading, self).__init__(driver, case)

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
