# please fill the name, path, and the way to get the result

from benchmark.benchmark import *

class template(Benchmark):
    CONFIG = {
        'name': '',
        'path': {
            'internal': '',
        }
    }

    def __init__(self, driver, case):
        super(template, self).__init__(driver, case)

    def cond0(self, driver):
        if driver.find_element_by_id('result'):
            return True
        return False

    def act0(self, driver):
        text = driver.find_element_by_id('result').text
        if text == 'PASS':
            self.result.append(1)
        else:
            self.result.append(2)