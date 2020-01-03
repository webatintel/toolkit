from benchmark.benchmark import *

class kraken(Benchmark):
    CONFIG = {
        'category': category_info['js'],
        'name': 'Kraken',
        'version': '1.1',
        'metric': metric_info['ms'],
        'path': {
            'external': 'http://krakenbenchmark.mozilla.org/',
            'internal': 'webbench/js/kraken/'
        },
    }

    def __init__(self, driver, case):
        super(kraken, self).__init__(driver, case)

    def cond0(self, driver):
        self.e = driver.find_element_by_link_text('Begin')
        if self.e:
            return True
        else:
            return False

    def act0(self, driver):
        self.e.click()

    def cond1(self, driver):
        if re.search('results', driver.current_url):
            return True
        else:
            return False

    def act1(self, driver):
        txt = self.driver.find_element_by_id('console').text
        pos = txt.find('Total:') + len('Total:')
        txt = txt[pos:].strip()
        pos = txt.find('ms')

        self.result.append(txt[:pos])
