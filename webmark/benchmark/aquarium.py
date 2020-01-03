from benchmark.benchmark import *

class aquarium(Benchmark):
    CONFIG = {
        'category': category_info['webgl'],
        'name': 'Aquarium',
        'metric': metric_info['fps'],
        'path': {
            'external': 'https://webglsamples.org/aquarium/aquarium.html',
            'internal': 'webgl/webglsamples/aquarium/aquarium.html',
        },
        'counts_fish': [1, 100, 500, 1000, 5000, 10000, 15000, 20000, 25000, 30000],
        'count_fish': 5000,
    }

    def __init__(self, driver, case):
        super(aquarium, self).__init__(driver, case)
        self.counts_fish = self.CONFIG['counts_fish']
        count_fish_default = self.CONFIG['count_fish']
        if hasattr(case, 'count_fish'):
            if case.count_fish in self.counts_fish:
                self.count_fish = case.count_fish
            else:
                warning('count_fish in Aquarium is not correct, will use %s instead' % str(count_fish_default))
                self.count_fish = count_fish_default
        else:
            self.count_fish = count_fish_default

    def cond0(self, driver):
        self.e = driver.find_element_by_id('fps')
        if self.e:
            return True
        else:
            return False

    def act0(self, driver):
        index = self.counts_fish.index(self.count_fish)
        element_id = 'setSetting' + str(index)
        driver.find_element_by_id(element_id).click()
        time.sleep(5)
        self.result = self.get_result_periodic(driver)

    def get_result_one(self, driver):
        return self.e.get_attribute('innerText')
