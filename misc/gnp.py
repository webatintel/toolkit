import os
import platform
import re
import subprocess
import sys

HOST_OS = platform.system().lower()
if HOST_OS == 'windows':
    lines = subprocess.Popen('dir %s' % __file__.replace('/', '\\'), shell=True, stdout=subprocess.PIPE).stdout.readlines()
    for line in lines:
        match = re.search(r'\[(.*)\]', line.decode('utf-8'))
        if match:
            script_dir = os.path.dirname(match.group(1)).replace('\\', '/')
            break
    else:
        script_dir = sys.path[0]
else:
    lines = subprocess.Popen('ls -l %s' % __file__, shell=True, stdout=subprocess.PIPE).stdout.readlines()
    for line in lines:
        match = re.search(r'.* -> (.*)', line.decode('utf-8'))
        if match:
            script_dir = os.path.dirname(match.group(1))
            break
    else:
        script_dir = sys.path[0]

sys.path.append(script_dir)
sys.path.append(script_dir + '/..')

from util.base import * # pylint: disable=unused-wildcard-import

class ChromiumRepo():
    FAKE_REV = 0

    COMMIT_STR = 'commit (.*)'

    INFO_INDEX_MIN_REV = 0
    INFO_INDEX_MAX_REV = 1
    INFO_INDEX_REV_INFO = 2

    # rev_info = {rev: info}
    REV_INFO_INDEX_HASH = 0
    REV_INFO_INDEX_ROLL_REPO = 1
    REV_INFO_INDEX_ROLL_HASH = 2
    REV_INFO_INDEX_ROLL_COUNT = 3

    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.info = [self.FAKE_REV, self.FAKE_REV, {}]

    def get_working_dir_rev(self):
        cmd = 'git log --shortstat -1'
        return self._get_head_rev(cmd)

    def get_local_repo_rev(self):
        cmd = 'git log --shortstat -1 origin/master'
        return self._get_head_rev(cmd)

    def get_hash_from_rev(self, rev):
        if rev not in self.info[self.INFO_INDEX_REV_INFO]:
            self.get_info(rev)
        return self.info[self.INFO_INDEX_REV_INFO][rev][self.REV_INFO_INDEX_HASH]

    # get info of [min_rev, max_rev]
    def get_info(self, min_rev, max_rev=FAKE_REV):
        if max_rev == self.FAKE_REV:
            max_rev = min_rev

        if min_rev > max_rev:
            return

        info = self.info
        info_min_rev = info[self.INFO_INDEX_MIN_REV]
        info_max_rev = info[self.INFO_INDEX_MAX_REV]
        if info_min_rev <= min_rev and info_max_rev >= max_rev:
            return

        if info[self.INFO_INDEX_MIN_REV] == self.FAKE_REV:
            self._get_info(min_rev, max_rev)
            info[self.INFO_INDEX_MIN_REV] = min_rev
            info[self.INFO_INDEX_MAX_REV] = max_rev
        else:
            if min_rev < info_min_rev:
                self._get_info(min_rev, info_min_rev - 1)
                info[self.INFO_INDEX_MIN_REV] = min_rev
            if max_rev > info_max_rev:
                self._get_info(info_max_rev + 1, max_rev)
                info[self.INFO_INDEX_MAX_REV] = max_rev

    def _get_info(self, min_rev, max_rev):
        info = self.info
        head_rev = self.get_local_repo_rev()
        if max_rev > head_rev:
            Util.error('Revision %s is not ready' % max_rev)
        cmd = 'git log --shortstat origin/master~%s..origin/master~%s ' % (head_rev - min_rev + 1, head_rev - max_rev)
        result = Util.execute(cmd, show_cmd=False, return_out=True)
        lines = result[1].split('\n')

        rev_info = info[self.INFO_INDEX_REV_INFO]
        self._parse_lines(lines, rev_info)

    def _parse_lines(self, lines, rev_info):
        tmp_hash = ''
        tmp_author = ''
        tmp_date = ''
        tmp_subject = ''
        tmp_rev = 0
        tmp_insertion = -1
        tmp_deletion = -1
        tmp_is_roll = False
        for index in range(0, len(lines)):
            line = lines[index]
            if re.match(self.COMMIT_STR, line):
                tmp_hash = ''
                tmp_author = ''
                tmp_date = ''
                tmp_subject = ''
                tmp_rev = 0
                tmp_insertion = -1
                tmp_deletion = -1
                tmp_is_roll = False
            (tmp_rev, tmp_hash, tmp_author, tmp_date, tmp_subject, tmp_insertion, tmp_deletion, tmp_is_roll) = self._parse_line(lines, index, tmp_rev, tmp_hash, tmp_author, tmp_date, tmp_subject, tmp_insertion, tmp_deletion, tmp_is_roll)
            if tmp_deletion >= 0:
                rev_info[tmp_rev] = [tmp_hash, '', '', 0]
                if tmp_is_roll:
                    match = re.match(r'Roll (.*) ([a-zA-Z0-9]+)..([a-zA-Z0-9]+) \((\d+) commits\)', tmp_subject)
                    rev_info[tmp_rev][self.REV_INFO_INDEX_ROLL_REPO] = match.group(1)
                    rev_info[tmp_rev][self.REV_INFO_INDEX_ROLL_HASH] = match.group(3)
                    rev_info[tmp_rev][self.REV_INFO_INDEX_ROLL_COUNT] = int(match.group(4))

    def _parse_line(self, lines, index, tmp_rev, tmp_hash, tmp_author, tmp_date, tmp_subject, tmp_insertion, tmp_deletion, tmp_is_roll):
        line = lines[index]
        strip_line = line.strip()
        # hash
        match = re.match(self.COMMIT_STR, line)
        if match:
            tmp_hash = match.group(1)

        # author
        match = re.match('Author:', lines[index])
        if match:
            match = re.search('<(.*@.*)@.*>', line)
            if match:
                tmp_author = match.group(1)
            else:
                match = re.search(r'(\S+@\S+)', line)
                if match:
                    tmp_author = match.group(1)
                    tmp_author = tmp_author.lstrip('<')
                    tmp_author = tmp_author.rstrip('>')
                else:
                    tmp_author = line.rstrip('\n').replace('Author:', '').strip()
                    Util.warning('The author %s is in abnormal format' % tmp_author)

        # date & subject
        match = re.match('Date:(.*)', line)
        if match:
            tmp_date = match.group(1).strip()
            index += 2
            tmp_subject = lines[index].strip()
            match = re.match(r'Roll (.*) ([a-zA-Z0-9]+)..([a-zA-Z0-9]+) \((\d+) commits\)', tmp_subject)
            if match and match.group(1) != 'src-internal':
                tmp_is_roll = True

        # rev
        # < r291561, use below format
        # example: git-svn-id: svn://svn.chromium.org/chrome/trunk/src@291560 0039d316-1c4b-4281-b951-d872f2087c98
        match = re.match('git-svn-id: svn://svn.chromium.org/chrome/trunk/src@(.*) .*', strip_line)
        if match:
            tmp_rev = int(match.group(1))

        # >= r291561, use below format
        # example: Cr-Commit-Position: refs/heads/master@{#349370}
        match = re.match('Cr-Commit-Position: refs/heads/master@{#(.*)}', strip_line)
        if match:
            tmp_rev = int(match.group(1))

        if re.match(r'(\d+) files? changed', strip_line):
            match = re.search(r'(\d+) insertion(s)*\(\+\)', strip_line)
            if match:
                tmp_insertion = int(match.group(1))
            else:
                tmp_insertion = 0

            match = re.search(r'(\d+) deletion(s)*\(-\)', strip_line)
            if match:
                tmp_deletion = int(match.group(1))
            else:
                tmp_deletion = 0

        return (tmp_rev, tmp_hash, tmp_author, tmp_date, tmp_subject, tmp_insertion, tmp_deletion, tmp_is_roll)

    def _get_head_rev(self, cmd):
        result = Util.execute(cmd, show_cmd=False, return_out=True)
        lines = result[1].split('\n')
        rev_info = {}
        self._parse_lines(lines, rev_info=rev_info)
        for key in rev_info:
            return key

class Gnp(Program):
    BUILD_TARGET_DICT = {
        'angle_e2e': 'angle_end2end_tests',
        'angle_perf': 'angle_perftests',
        'angle_unit': 'angle_unittests',

        'webgl': 'telemetry_gpu_integration_test',
        'webgpu': 'webgpu_blink_web_tests',

        'dawn_e2e': 'dawn_end2end_tests',
    }
    BACKUP_TARGET_DICT = {
        'angle_e2e': '//src/tests:angle_end2end_tests',
        'angle_perf': '//src/tests:angle_perftests',
        'angle_unit': '//src/tests:angle_unittests',

        'chrome': '//chrome:chrome',
        'chromedriver': '//chrome/test/chromedriver:chromedriver',
        'webgl': '//chrome/test:telemetry_gpu_integration_test',
        'webgpu': '//:webgpu_blink_web_tests',

        'dawn_e2e': '//src/tests:dawn_end2end_tests',
    }
    def __init__(self, parser):
        parser.add_argument('--project', dest='project', help='project')
        parser.add_argument('--dcheck', dest='dcheck', help='dcheck', action='store_true')
        parser.add_argument('--is-debug', dest='is_debug', help='is debug', action='store_true')
        parser.add_argument('--no-component-build', dest='no_component_build', help='no component build', action='store_true')
        parser.add_argument('--no-warning-as-error', dest='no_warning_as_error', help='not treat warning as error', action='store_true')
        parser.add_argument('--special-out-dir', dest='special_out_dir', help='special out dir', action='store_true')
        parser.add_argument('--rev', dest='rev', help='revision')
        parser.add_argument('--rev-stride', dest='rev_stride', help='rev stride', type=int, default=1)
        parser.add_argument('--symbol-level', dest='symbol_level', help='symbol level', type=int, default=0)
        parser.add_argument('--batch', dest='batch', help='batch', action='store_true')
        parser.add_argument('--download', dest='download', help='download', action='store_true')
        parser.add_argument('--no-exit-on-error', dest='no_exit_on_error', help='no exit on error', action='store_true')

        parser.add_argument('--sync', dest='sync', help='sync', action='store_true')
        parser.add_argument('--sync-reset', dest='sync_reset', help='do a reset before syncing', action='store_true')
        parser.add_argument('--sync-src-only', dest='sync_src_only', help='sync src only', action='store_true')
        parser.add_argument('--runhooks', dest='runhooks', help='runhooks', action='store_true')
        parser.add_argument('--makefile', dest='makefile', help='generate makefile', action='store_true')
        parser.add_argument('--build', dest='build', help='build', action='store_true')
        parser.add_argument('--build-max-fail', dest='build_max_fail', help='build keeps going until N jobs fail', type=int, default=1)
        parser.add_argument('--build-target', dest='build_target', help='build target')
        parser.add_argument('--build-verbose', dest='build_verbose', help='output verbose info. Find log at out/Release/.ninja_log', action='store_true')
        parser.add_argument('--backup', dest='backup', help='backup', action='store_true')
        parser.add_argument('--backup-symbol', dest='backup_symbol', help='backup symbol', action='store_true')
        parser.add_argument('--backup-target', dest='backup_target', help='backup target')
        parser.add_argument('--run', dest='run', help='run', action='store_true')
        parser.add_argument('--run-target', dest='run_target', help='run target')
        parser.add_argument('--run-args', dest='run_args', help='run args')
        parser.add_argument('--run-disabled', dest='run_disabled', help='run disabled cases', action='store_true')
        parser.add_argument('--run-filter', dest='run_filter', help='run filter', default='all')
        parser.add_argument('--run-rev', dest='run_rev', help='run rev', default='out')
        parser.add_argument('--run-mesa-rev', dest='run_mesa_rev', help='mesa revision', default='system')

        parser.epilog = '''
python %(prog)s --sync --runhooks --makefile --build --backup --build --run --download
python %(prog)s --backup --root-dir d:\workspace\chrome
'''
        python_ver = Util.get_python_ver()
        if python_ver[0] == 3:
            super().__init__(parser)
        else:
            super(Gnp, self).__init__(parser)
        args = self.args

        Util.prepend_path(Util.PROJECT_DEPOT_TOOLS)

        if args.project:
            project = args.project
        else:
            project = os.path.basename(self.root_dir)
            if 'chrome' in project or 'chromium' in project:
                project = 'chromium'
        if project == 'chromium':
            self.root_dir = self.root_dir + '/src'
            Util.chdir(self.root_dir)
            self.repo = ChromiumRepo(self.root_dir)
        self.project = project

        if args.is_debug:
            build_type = 'debug'
        else:
            build_type = 'release'

        if self.args.special_out_dir:
            out_dir = Util.cal_relative_out_dir(self.target_arch, self.target_os, args.symbol_level, args.no_component_build, args.dcheck)
        else:
            out_dir = 'out'
        self.out_dir = '%s/%s' % (out_dir, build_type)

        if self.project == 'angle':
            default_target = 'angle_e2e'
        elif self.project == 'chromium':
            default_target = 'chrome'
        elif self.project == 'dawn':
            default_target = 'dawn_e2e'
        else:
            default_target = ''
        self.default_target = default_target

        if args.no_exit_on_error:
            self.exit_on_error = False
        else:
            self.exit_on_error = True

        if args.rev:
            if re.search('-', args.rev):
                tmp_revs = args.rev.split('-')
                min_rev = tmp_revs[0]
                max_rev = tmp_revs[1]
                if args.run:
                    Util.error('Cannot run with multiple revisions')
            else:
                min_rev = args.rev
                max_rev = args.rev

            if '.' in min_rev and '.' not in max_rev or '.' not in min_rev and '.' in max_rev:
                Util.error('min_rev and max_rev should be in same format')

            if '.' in min_rev:
                integer_rev = int(float(min_rev)) + 1
                self.integer_rev = integer_rev
                self.repo.get_info(integer_rev)
                roll_count = self.repo.info[ChromiumRepo.INFO_INDEX_REV_INFO][integer_rev][ChromiumRepo.REV_INFO_INDEX_ROLL_COUNT]
                if roll_count <= 1:
                    Util.error('Rev %s cannot be built as a roll')

                tmp_min = int(min_rev.split('.')[1])
                tmp_max = int(max_rev.split('.')[1])
                for i in range(tmp_min, min(tmp_max + 1, roll_count)):
                    self.rev = '%s.%s' % (min_rev.split('.')[0], i)
                    self.decimal_rev = i
                    self._handle_ops()
            else:
                min_rev = int(min_rev)
                max_rev = int(max_rev)
                tmp_rev = min_rev
                while tmp_rev <= max_rev:
                    if (tmp_rev % args.rev_stride == 0):
                        self.rev = str(tmp_rev)
                        self.integer_rev = int(self.rev)
                        self.decimal_rev = 0
                        self._handle_ops()
                        tmp_rev += args.rev_stride
                    else:
                        tmp_rev += 1
        else:
            self.rev = ''
            self.integer_rev = 0
            self.decimal_rev = 0
            self._handle_ops()

    def sync(self):
        if self.project == 'chromium':
            if self.rev:
                Util.info('Begin to sync rev %s' % self.rev)

            if self.args.sync_reset:
                self._execute('git reset --hard HEAD && git clean -f -d', exit_on_error=self.exit_on_error)

            if self.integer_rev:
                self.repo.get_info(self.integer_rev)
            self._chromium_sync_integer_rev()
            if not self.integer_rev:
                self.integer_rev = self.repo.get_working_dir_rev()
                self.repo.get_info(self.integer_rev)
            if self.decimal_rev:
                self._chromium_sync_decimal_rev()
        else:
            self._execute('git pull', exit_on_error=self.exit_on_error)
            self._execute_gclient(cmd_type='sync')

    def runhooks(self):
        self._execute_gclient(cmd_type='runhooks')

    def makefile(self):
        args = self.args

        if args.is_debug:
            gn_args = 'is_debug=true'
        else:
            gn_args = 'is_debug=false'

        if self.project != 'aquarium':
            if args.dcheck:
                gn_args += ' dcheck_always_on=true'
            else:
                gn_args += ' dcheck_always_on=false'

            if self.args.no_component_build:
                gn_args += ' is_component_build=false'
            else:
                gn_args += ' is_component_build=true'

            if args.no_warning_as_error:
                gn_args += ' treat_warnings_as_errors=false'
            else:
                gn_args += ' treat_warnings_as_errors=true'

            gn_args += ' symbol_level=%s' % self.args.symbol_level
            gn_args += ' is_clang=true'

        if self.project == 'chromium':
            if self.args.symbol_level == 0:
                gn_args += ' blink_symbol_level=0'

            # for windows, it has to use "" instead of ''
            if self.target_os == Util.WINDOWS:
                gn_args += ' ffmpeg_branding=\\\"Chrome\\\"'
            else:
                gn_args += ' ffmpeg_branding=\\\"Chrome\\\"'

            if self.target_arch == 'x86_64':
                target_arch_tmp = 'x64'
            else:
                target_arch_tmp = self.target_arch

            gn_args += ' enable_nacl=false proprietary_codecs=true'

            if self.target_os in [Util.LINUX, Util.ANDROID, Util.CHROMEOS]:
                gn_args += ' target_os=\\\"%s\\\" target_cpu=\\\"%s\\\"' % (self.target_os, target_arch_tmp)
            if self.target_os == Util.DARWIN:
                gn_args += ' cc_wrapper="ccache"'

        quotation = Util.get_quotation()
        cmd = 'gn --args=%s%s%s gen %s' % (quotation, gn_args, quotation, self.out_dir)
        Util.ensure_dir(self.out_dir)
        Util.info('GN ARGS: {}'.format(gn_args))
        self._execute(cmd, exit_on_error=self.exit_on_error)

    def build(self):
        build_target = self.args.build_target
        if self.args.build_target:
            targets = build_target.split(',')
        else:
            targets = [self.default_target]

        for key, value in self.BUILD_TARGET_DICT.items():
            if key in targets:
                targets[targets.index(key)] = value

        if self.project == 'chromium':
            if self.rev:
                rev = self.rev
            else:
                rev = self.repo.get_working_dir_rev()
            Util.info('Begin to build rev %s' % rev)
            Util.chdir(self.root_dir + '/build/util')
            self._execute('python lastchange.py -o LASTCHANGE', exit_on_error=self.exit_on_error)
            Util.chdir(self.root_dir)

        cmd = 'ninja -k%s -j%s -C %s %s' % (str(self.args.build_max_fail), str(Util.CPU_COUNT), self.out_dir, ' '.join(targets))
        if self.args.build_verbose:
            cmd += ' -v'
        self._execute(cmd, show_duration=True)

    def backup(self):
        if self.project == 'chromium':
            if self.rev:
                rev = self.rev
            else:
                rev = self.repo.get_working_dir_rev()
            backup_dir = Util.cal_backup_dir(rev)
        else:
            backup_dir = Util.cal_backup_dir()
        backup_path = '%s/backup/%s' % (self.root_dir, backup_dir)
        Util.ensure_dir('%s/backup' % self.root_dir)

        Util.info('Begin to backup %s' % backup_dir)
        if os.path.exists(backup_path):
            Util.info('Backup folder "%s" alreadys exists' % backup_path)
            os.rename(backup_path, '%s-%s' % (backup_path, Util.get_datetime()))

        backup_target = self.args.backup_target
        if self.args.backup_target:
            targets = self.args.backup_target.split(',')
        else:
            targets = [self.default_target]

        for key, value in self.BACKUP_TARGET_DICT.items():
            if key in targets:
                targets[targets.index(key)] = value

        tmp_files = []
        for target in targets:
            target_files = self._execute('gn desc %s %s runtime_deps' % (self.out_dir, target), return_out=True, exit_on_error=self.exit_on_error)[1].rstrip('\n').split('\n')
            tmp_files = Util.union_list(tmp_files, target_files)

        exclude_files = ['gen/']
        src_files = []
        for tmp_file in tmp_files:
            tmp_file = tmp_file.rstrip('\r')
            if not self.args.backup_symbol and tmp_file.endswith('.pdb'):
                continue

            if tmp_file.startswith('./'):
                tmp_file = tmp_file[2:]

            if self.target_os == Util.CHROMEOS and not tmp_file.startswith('../../'):
                continue

            for exclude_file in exclude_files:
                if tmp_file.startswith(exclude_file):
                    break
            else:
                src_files.append(tmp_file)

        for src_file in src_files:
            src_file = '%s/%s' % (self.out_dir, src_file)
            dst_dir = '%s/%s' % (backup_path, src_file)
            Util.ensure_dir(os.path.dirname(dst_dir))
            if os.path.isdir(src_file):
                dst_dir = os.path.dirname(os.path.dirname(dst_dir))
            cmd = 'cp -rf %s %s' % (src_file, dst_dir)
            self._execute(cmd, exit_on_error=self.exit_on_error)
            #Util.execute(cmd=cmd, show_cmd=True, exit_on_error=self.exit_on_error)

            # permission denied
            #shutil.copyfile(file, dst_dir)

    def backup_webgl(self):
        # generate telemetry_gpu_integration_test
        if self.rev:
            rev = self.rev
        else:
            rev = self.repo.get_working_dir_rev()
        rev_str = str(rev)

        if not os.path.exists('%s/%s-orig.zip' % (self.backup_dir, rev_str)):
            cmd = 'vpython tools/mb/mb.py zip %s telemetry_gpu_integration_test %s/%s-orig.zip' % (self.out_dir, self.backup_dir, rev_str)
            result = self._execute(cmd, exit_on_error=self.exit_on_error)
            if result[0]:
                Util.error('Failed to generate telemetry_gpu_integration_test')

        Util.chdir(self.backup_dir)
        if not os.path.exists(rev_str):
            zipfile.ZipFile('%s-orig.zip' % rev_str).extractall(rev_str)
            Util.del_filetype_in_dir(rev_str, 'pdb')
            shutil.make_archive(rev_str, 'zip', rev_str)

    def run(self):
        Util.clear_proxy()

        if Util.HOST_OS == Util.LINUX:
            Util.set_mesa(Util.PROJECT_MESA_BACKUP_DIR, self.args.run_mesa_rev)

        if self.args.run_rev == 'out':
            run_dir = self.out_dir
        else:
            rev_dir, _ = Util.get_backup_dir('backup', self.args.run_rev)
            run_dir = 'backup/%s/out/release' % rev_dir

        Util.chdir(run_dir, verbose=True)
        run_target = self.args.run_target
        if run_target:
            targets = run_target.split(',')
        else:
            targets = [self.default_target]

        for key, value in self.BUILD_TARGET_DICT.items():
            if key in targets:
                targets[targets.index(key)] = value

        for target in targets:
            self._run(target)

    def download(self):
        if not self.project == 'chromium':
            return

        rev = self.rev
        if not rev:
            Util.error('Please designate revision')

        download_dir = '%s/%s-%s/tmp' % (ScriptRepo.IGNORE_CHROMIUM_DOWNLOAD_DIR, self.target_arch, self.target_os)
        Util.ensure_dir(download_dir)
        Util.chdir(download_dir)

        if self.target_os == Util.DARWIN:
            target_arch_tmp = ''
        elif self.target_arch == 'x86_64':
            target_arch_tmp = '_x64'
        else:
            target_arch_tmp = ''

        if self.target_os == Util.WINDOWS:
            target_os_tmp = 'Win'
            target_os_tmp2 = 'win'
        elif self.target_os == Util.DARWIN:
            target_os_tmp = 'Mac'
            target_os_tmp2 = 'mac'
        else:
            target_os_tmp = self.target_os.capitalize()
            target_os_tmp2 = self.target_os

        rev_zip = '%s.zip' % rev
        if os.path.exists(rev_zip) and os.stat(rev_zip).st_size == 0:
            Util.ensure_nofile(rev_zip)
        if os.path.exists('../%s' % rev_zip):
            Util.info('%s has been downloaded' % rev_zip)
        else:
            # linux64: Linux_x64/<rev>/chrome-linux.zip
            # win64: Win_x64/<rev>/chrome-win32.zip
            # mac64: Mac/<rev>/chrome-mac.zip
            if Util.HOST_OS == Util.WINDOWS:
                wget = Util.use_backslash('%s/wget64.exe' % ScriptRepo.TOOL_DIR)
            else:
                wget = 'wget'

            if self.target_os == Util.ANDROID:
                # https://commondatastorage.googleapis.com/chromium-browser-snapshots/index.html?prefix=Android/
                # https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Android%2F607944%2Fchrome-android.zip?generation=1542192867201693&alt=media
                archive_url = '"https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Android%2F' + rev + '%2Fchrome-android.zip?generation=1542192867201693&alt=media"'
            else:
                archive_url = 'http://commondatastorage.googleapis.com/chromium-browser-snapshots/%s%s/%s/chrome-%s.zip' % (target_os_tmp, target_arch_tmp, rev, target_os_tmp2)
            self._execute('%s %s --show-progress -O %s' % (wget, archive_url, rev_zip), exit_on_error=self.exit_on_error)
            if (os.path.getsize(rev_zip) == 0):
                Util.warning('Could not find revision %s' % rev)
                self._execute('rm %s' % rev_zip, exit_on_error=self.exit_on_error)
            else:
                self._execute('mv %s ../' % rev_zip, exit_on_error=self.exit_on_error)

    def batch(self):
        self.sync()
        self.runhooks()
        self.makefile()
        self.build()
        self.backup()
        self.run()

    def _execute_gclient(self, cmd_type, job_count=0, extra_cmd='', verbose=False):
        self._set_boto()
        cmd = 'gclient ' + cmd_type
        if extra_cmd:
            cmd += ' ' + extra_cmd
        if cmd_type == 'sync':
            cmd += ' -n -D --force -R'

        if not job_count:
            job_count = Util.CPU_COUNT
        cmd += ' -j%s' % job_count

        if verbose:
            cmd += ' -v'

        if not Util.has_depot_tools_in_path() and os.path.exists(Util.PROJECT_DEPOT_TOOLS):
            Util.prepend_path(Util.PROJECT_DEPOT_TOOLS)

        result = self._execute(cmd=cmd, exit_on_error=self.exit_on_error)

        if not Util.has_depot_tools_in_path() and os.path.exists(Util.PROJECT_DEPOT_TOOLS):
            Util.remove_path(Util.PROJECT_DEPOT_TOOLS)

        return result

    def _chromium_sync_integer_rev(self):
        if self.integer_rev:
            roll_repo = self.repo.info[ChromiumRepo.INFO_INDEX_REV_INFO][self.integer_rev][ChromiumRepo.REV_INFO_INDEX_ROLL_REPO]
            if self.decimal_rev and not roll_repo:
                Util.error('Rev %s is not a roll' % self.integer_rev)

        tmp_hash = ''
        if self.integer_rev:
            working_dir_rev = self.repo.get_working_dir_rev()
            if working_dir_rev == self.integer_rev:
                return
            tmp_hash = self.repo.get_hash_from_rev(self.integer_rev)

        if tmp_hash:
            extra_cmd = '--revision src@' + tmp_hash
        else:
            self._execute('git pull', exit_on_error=self.exit_on_error)
            extra_cmd = ''

        if not self.args.sync_src_only:
            self._execute_gclient(cmd_type='sync', extra_cmd=extra_cmd)

    def _chromium_sync_decimal_rev(self):
        roll_repo = self.repo.info[ChromiumRepo.INFO_INDEX_REV_INFO][self.integer_rev][ChromiumRepo.REV_INFO_INDEX_ROLL_REPO]
        roll_count = self.repo.info[ChromiumRepo.INFO_INDEX_REV_INFO][self.integer_rev][ChromiumRepo.REV_INFO_INDEX_ROLL_COUNT]
        if roll_repo:
            if self.decimal_rev:
                if self.decimal_rev >= roll_count:
                    Util.error('The decimal part of rev cannot be greater or equal to %s' % roll_count)
            else:
                self.decimal_rev = roll_count
        else:
            if self.decimal_rev:
                Util.error('Rev %s is not a roll' % self.integer_rev)
            else:
                return

        roll_hash = self.repo.info[ChromiumRepo.INFO_INDEX_REV_INFO][self.integer_rev][ChromiumRepo.REV_INFO_INDEX_ROLL_HASH]
        roll_count_diff = roll_count - self.decimal_rev
        if roll_count_diff < 0:
            Util.error('The decimal part of rev should be less than %s' % roll_count)
        Util.chdir('%s/%s' % (self.root_dir, roll_repo))
        cmd = 'git reset --hard %s~%s' % (roll_hash, roll_count_diff)
        self._execute(cmd, exit_on_error=self.exit_on_error)
        cmd = 'git rev-parse --abbrev-ref HEAD'
        branch = self._execute(cmd, return_out=True, show_cmd=False, exit_on_error=self.exit_on_error)[1].strip()
        if not branch == 'master':
            Util.error('Repo %s is not on master' % roll_repo)

    def _run(self, target):
        if target == 'telemetry_gpu_integration_test':
            cmd = 'vpython ../../content/test/gpu/run_gpu_integration_test.py'
        elif target == 'webgpu_blink_web_tests':
            cmd = 'vpython ../../third_party/blink/tools/run_web_tests.py'
        else:
            cmd = '%s%s' % (target, Util.EXEC_SUFFIX)
        if Util.HOST_OS == Util.WINDOWS:
            cmd = Util.use_backslash(cmd)
        if self.args.run_disabled:
            cmd += ' --gtest_also_run_disabled_tests'
        if not self.args.run_filter == 'all':
            cmd += ' --gtest_filter=*%s*' % self.args.run_filter

        if self.args.run_args:
            cmd += ' %s' % self.args.run_args

        if Util.HOST_OS == Util.LINUX:
            cmd = './' + cmd
        self._execute(cmd, exit_on_error=self.exit_on_error)

    def _handle_ops(self):
        args = self.args
        if args.sync:
            self.sync()
        if args.runhooks:
            self.runhooks()
        if args.makefile:
            self.makefile()
        if args.build:
            self.build()
        if args.backup:
            self.backup()
        if args.run:
            self.run()
        if args.batch:
            self.batch()
        if args.download:
            self.download()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GN Script')
    Gnp(parser)