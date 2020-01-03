from benchmark.benchmark import *

class jetstream(Benchmark):
    CONFIG = {
        'category': category_info['js'],
        'name': 'JetStream',
        'version': '1.1',
        'metric': metric_info['score'],
        'path': {
            '1.1': {
                'external': 'http://browserbench.org/JetStream/',
                'internal': 'webbench/js/jetstream/1.1/index.html'
            },
        'timeout': 1800,
        },
    }

    def __init__(self, driver, case):
        super(jetstream, self).__init__(driver, case)

    def cond0(self, driver):
        if driver.find_element_by_id('status'):
            return True
        return False

    def act0(self, driver):
        href = driver.find_element_by_id('status').find_element_by_xpath('./a')
        href.click()

    def cond1(self, driver):
        if driver.find_elements_by_class_name('score'):
            return True
        return False

    def act1(self, driver):
        text = self.driver.find_element_by_class_name('score').get_attribute('innerText').split()[0]
        self.result.append(text)
