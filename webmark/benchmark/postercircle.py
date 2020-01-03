from benchmark.benchmark import *

class postercircle(CssBenchmark):
    CONFIG = {
        'category': category_info['css'],
        'name': 'Poster Circle',
        'metric': metric_info['fps'],
        'path': {
            'external': 'http://www.webkit.org/blog-files/3d-transforms/poster-circle.html',
            'internal': 'webbench/css/poster-circle/poster-circle.html'
        },
    }

    def __init__(self, driver, case):
        super(postercircle, self).__init__(driver, case)

    def cond0(self, driver):
        self.inject_css_fps(driver)
        return True

    def act0(self, driver):
        time.sleep(5)
        self.result = self.get_result_periodic(driver)

    def get_result_one(self, driver):
        return self.get_css_fps(driver)
