from benchmark.benchmark import *

class browsermark(Benchmark):
    CONFIG = {
        'category': category_info['comprehensive'],
        'name': 'BrowserMark',
        'version': '2.1',
        'metric': metric_info['score'],
        'path': {
            '2.1': {
                'external': 'http://browsermark.rightware.com',
                'internal': 'webbench/comprehensive/browsermark',
            },
            '2.0': {
                'external': 'http://username:password@browsermark-corporate.rightware.com',
                'internal': 'webbench/comprehensive/browsermark',
            }
        },
        'timeout': 1800,
        'test_all': [
            '2D Rendering', '3D Rendering', 'Crunch', 'Resize',
            'Advance Search', 'Create Source', 'Dynamic Create', 'Search',
            'Graphics Canvas', 'Graphics SVG', 'Graphics WebGL',
            'Array Blur', 'Array Weighted', 'String Chat',
            'CSS', 'DOM', 'Graphics', 'Javascript',
        ],
        'test': 'all',
    }

    def __init__(self, driver, case):
        super(browsermark, self).__init__(driver, case)

        if hasattr(case, 'test'):
            test = getattr(case, 'test')
            if test not in self.CONFIG['test_all']:
                error('test is not supported')

            self.test = getattr(case, 'test')
        else:
            self.test = self.CONFIG['test']

        if self.version == '2.0' and self.path_type == 'external':
            if not case.username or not case.password:
                error('Username and password are needed to run this case')
            self.path = self.path.replace('username', case.username)
            self.path = self.path.replace('password', case.password)

    def cond0(self, driver):
        if self.version == '2.0' and self.path_type == 'external' and driver.find_elements_by_id('continent'):
            return True
        elif self.path_type == 'internal' and driver.find_elements_by_class_name('launchIcon'):
            return True

        return False

    def act0(self, driver):
        if self.version == '2.0' and self.path_type == 'external':
            # nearest server can not be selected if not scrolled to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            e = driver.find_element_by_css_selector('a[data-id="Asia-Pacific"]')
            # error would occur when directly use e.click(), and this is a workaround.
            ActionChains(driver).move_to_element(e).click().perform()

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            e = driver.find_element_by_css_selector('div[class="start_test enabled"] span:first-of-type')
            ActionChains(driver).move_to_element(e).click().perform()

        elif self.path_type == 'internal':
            e = driver.find_elements_by_class_name('selectVersionButton')
            if self.version == '2.0':
                e[1].click()
            elif self.version == '2.1':
                e[0].click()
            else:
                error('version is not supported')

            time.sleep(2)
            if self.test != 'all':
                select = Select(driver.find_element_by_class_name('selectTest'))
                if self.test in ['CSS', 'DOM', 'Graphics', 'Javascript']:
                    prefix = '—— '
                else:
                    prefix = '——— '
                select.select_by_visible_text(prefix + self.test)
            driver.find_element_by_class_name('launchIcon').click()

    def cond1(self, driver):
        if re.search('results', driver.current_url):
            return True
        return False

    def act1(self, driver):
        result = []
        if self.version == '2.0' and self.path_type == 'external':
            scores = driver.find_elements_by_class_name('console-log')
            pattern = re.compile('.*: (\d+)')
            for score in scores:
                match = re.search(pattern, score.get_attribute('innerText'))
                if match:
                    result.append(match.group(1))
        elif self.path_type == 'internal':
            if self.test != 'all':
                result.append(driver.find_element_by_class_name('score').get_attribute('innerText'))
            else:
                score = driver.find_element_by_class_name('score').get_attribute('innerText')
                scores_group = [x.get_attribute('innerText') for x in driver.find_elements_by_class_name('group_result_score')]
                scores_test = [x.get_attribute('innerText') for x in driver.find_elements_by_class_name('test_result_score')]
                # overall score
                result.append(score)
                # CSS
                result.append(scores_group[0])
                for i in range(0, 4):
                    result.append(scores_test[i])
                # DOM
                result.append(scores_group[1])
                for i in range(4, 8):
                    result.append(scores_test[i])

                if self.version == '2.1':
                    # GRAPHICS
                    result.append(scores_group[2])
                    for i in range(8, 11):
                        result.append(scores_test[i])
                    # JAVASCRIPT
                    result.append(scores_group[3])
                    for i in range(11, 15):
                        result.append(scores_test[i])
                    # SCALABLE SOLUTIONS
                    result.append(scores_group[4])
                    for i in range(15, 19):
                        result.append(scores_test[i])
        self.result = result
