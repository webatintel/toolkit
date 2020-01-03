from benchmark.benchmark import *

class octane(Benchmark):
    CONFIG = {
        'category': category_info['js'],
        'name': 'Octane',
        'version': '2.0',
        'metric': metric_info['score'],
        'path': {
            '2.0': {
                'external': 'http://octane-benchmark.googlecode.com/svn/latest/index.html',
                'internal': 'webbench/js/octane/2.0/index.html',
            },
            '1.0': {
                'external': 'http://octane-benchmark.googlecode.com/svn/tags/v1/index.html',
                'internal': 'webbench/js/octane/1.0/index.html',
            }
        },
        'timeout': 1200,
    }

    def __init__(self, driver, case):
        super(octane, self).__init__(driver, case)

    def cond0(self, driver):
        self.e = driver.find_element_by_id('run-octane')
        if self.e:
            return True
        else:
            return False

    def act0(self, driver):
        self.e.click()

    def cond1(self, driver):
        self.e = driver.find_element_by_id('main-banner')
        if self.e.text.find('Score:') != -1:
            return True
        else:
            return False

    def act1(self, driver):
        result = []
        pattern = re.compile('Octane Score: (\d+)')
        match = pattern.search(self.e.text)
        result.append(match.group(1))

        subs = driver.find_elements_by_class_name('p-result')
        for sub in subs:
            result.append(sub.get_attribute('innerText'))
        self.result = result
