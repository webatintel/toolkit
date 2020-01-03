from benchmark.benchmark import *

class webxprt(Benchmark):
    CONFIG = {
        'category': category_info['comprehensive'],
        'name': 'WebXPRT',
        'metric': metric_info['score'],
        'path': {
            'external': 'http://www.principledtechnologies.com/web/webxprtworkload/',
            'internal': ''
        },
        'version': '2013',
        'timeout': 1200,
        'path_type': 'external',
    }

    def __init__(self, driver, case):
        super(webxprt, self).__init__(driver, case)

    def cond0(self, driver):
        self.e = driver.find_elements_by_class_name('ui-btn-up-b')
        if self.e:
            return True
        else:
            return False

    def act0(self, driver):
        self.e[0].click()

    def cond1(self, driver):
        if re.search('results', driver.current_url):
            return True
        else:
            return False

    def act1(self, driver):
        text = driver.find_element_by_class_name('scoreDiv').text
        match = re.search('(\d+) \+', text)
        if match:
            self.result.append(match.group(1))
        else:
            self.result.append('0')
