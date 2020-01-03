from benchmark.benchmark import *

class fishietank(Benchmark):
    CONFIG = {
        'category': category_info['canvas2d'],
        'name': 'FishIETank',
        'version': 'setinterval',
        'metric': metric_info['fps'],
        'path': {
            'setinterval': {
                'external': 'http://ie.microsoft.com/testdrive/Performance/FishIETank/Default.html',
                'internal': 'webbench/canvas2d/microsoft/testdrive/Performance/FishIETank/Default.html'
            },
            'mobileraf': {
                'external': '',
                'internal': 'webbench/canvas2d/fishtank-raf/test.php'
            },
            'desktopmod': {
                'external': '',
                'internal': 'webbench/canvas2d/microsoft/testdrive/Performance/FishIETank/DefaultMod.html'
            }

        },
        'counts_fish': {
            'setinterval': [1, 10, 20, 50, 100, 250, 500, 1000],
            'mobileraf': [1, 10, 20, 50, 100, 250, 500, 1000],
            'desktopmod': [1, 10, 20, 50, 100, 250, 6000, 7000, 8000, 9000, 10000],
        },
        'count_fish': 250,
        'orientation': 'portrait',
    }

    def __init__(self, driver, case):
        super(fishietank, self).__init__(driver, case)
        self.counts_fish = self.CONFIG['counts_fish'][self.version]
        count_fish_default = self.CONFIG['count_fish']
        if hasattr(case, 'count_fish'):
            if case.count_fish in self.counts_fish:
                self.count_fish = case.count_fish
            else:
                warning('count_fish in FishIETank is not correct, will use %s instead' % str(count_fish_default))
                self.count_fish = count_fish_default
        else:
            self.count_fish = count_fish_default

    def cond0(self, driver):
        self.e = driver.find_elements_by_class_name('control')
        if self.e:
            return True
        else:
            return False

    def act0(self, driver):
        index = (self.counts_fish.index(self.count_fish) + 1) * 2
        self.e[index].click()
        time.sleep(5)
        self.result = self.get_result_periodic(driver)

    def get_result_one(self, driver):
        pattern = re.compile('(\d+\.?\d*) FPS')
        match = pattern.search(driver.find_element_by_id('fpsCanvas').get_attribute('title'))
        return match.group(1)
