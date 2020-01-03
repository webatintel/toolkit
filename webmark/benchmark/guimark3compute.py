from benchmark.benchmark import *

class guimark3compute(Benchmark):
    CONFIG = {
        'category': category_info['canvas2d'],
        'name': 'GUIMark3 Compute',
        'metric': metric_info['fps'],
        'path': {
            'external': 'http://www.craftymind.com/factory/guimark3/compute/GM3_JS_Compute.html',
            'internal': 'webbench/canvas2d/guimark3/compute/GM3_JS_Compute.html'
        },
        'times_run': 5,
        'stat': 'max',
    }

    def cond0(self, driver):
        self.e = driver.find_element_by_id('testaction')
        if self.e:
            return True
        else:
            return False

    def act0(self, driver):
        self.e.click()

    def cond1(self, driver):
        self.e = driver.find_element_by_id('testlabel')
        if self.e.text.find('Test Results:') != -1:
            return True
        else:
            return False

    def act1(self, driver):
        pattern = re.compile('(\d+\.?\d*) fps')
        match = pattern.search(self.e.text)
        self.result.append(match.group(1))
