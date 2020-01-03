from benchmark.benchmark import *

class guimark3bitmap(Benchmark):
    CONFIG = {
        'category': category_info['canvas2d'],
        'name': 'GUIMark3 bitmap',
        'version': 'nocache',
        'metric': metric_info['fps'],
        'path': {
            'nocache': {
                'external': 'http://www.craftymind.com/factory/guimark3/bitmap/GM3_JS_Bitmap.html',
                'internal': 'webbench/canvas2d/guimark3/bitmap/GM3_JS_Bitmap.html'
            },
            'cache': {
                'external': 'http://www.craftymind.com/factory/guimark3/bitmap/GM3_JS_Bitmap_cache.html',
                'internal': 'webbench/canvas2d/guimark3/bitmap/GM3_JS_Bitmap_cache.html'
            }
        },
        'times_run': 5,
    }

    def __init__(self, driver, case):
        super(guimark3bitmap, self).__init__(driver, case)

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
