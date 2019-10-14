import os
import re
import subprocess
import sys
lines = subprocess.Popen('dir %s' % __file__, shell=True, stdout=subprocess.PIPE).stdout.readlines()
for line in lines:
    match = re.search('\[(.*)\]', line.decode('utf-8'))
    if match:
        script_dir = os.path.dirname(match.group(1)).replace('\\', '/')
        break
else:
    script_dir = sys.path[0]

sys.path.append(script_dir)
sys.path.append(script_dir + '/..')

from util.base import * # pylint: disable=unused-wildcard-import
from repo import *

class Base():
    def __init__(self, is_debug, no_component_build, no_warning_as_error, out_dir, program, rev, root_dir, symbol_level, target_arch, target_os):
        if is_debug:
            self.build_type = 'debug'
        else:
            self.build_type = 'release'
        self.build_type_cap = self.build_type.capitalize()
        self.no_component_build = no_component_build
        self.no_warning_as_error = no_warning_as_error
        if out_dir:
            self.out_dir = out_dir
        else:
            self.out_dir = self._get_relative_out_dir(target_arch, target_os, symbol_level, no_component_build)
        self.out_dir = '%s/%s' % (self.out_dir, self.build_type_cap)
        self.program = program
        self.rev = rev
        self.root_dir = root_dir
        self.build_dir = '%s/build' % root_dir
        self.src_dir = '%s/src' % root_dir
        self.symbol_level = symbol_level
        self.target_arch = target_arch
        self.target_os = target_os
        self.repo = Repo(self.src_dir, program)
        if self.rev:
            match = re.search('(\d+)\.(\d+)', self.rev)
            if match:
                self.integer_rev = int(match.group(1)) + 1
                self.decimal_rev = int(match.group(2))
                if not self.decimal_rev:
                    Util.error('The decimal part of rev cannot be 0')
            else:
                self.integer_rev = int(self.rev)
                self.decimal_rev = 0
        else:
            self.integer_rev = 0
            self.decimal_rev = 0

    def sync(self, sync_reset):
        if self.rev:
            Util.info('Begin to sync rev %s' % self.rev)
        Util.set_proxy()
        self._set_boto()
        Util.chdir(self.repo.src_dir)

        if sync_reset:
            self.program.execute('git reset --hard HEAD && git clean -f -d')

        if self.integer_rev:
            self.repo.get_info(self.integer_rev)
        self._sync_integer_rev()
        if not self.integer_rev:
            self.integer_rev = self.repo.get_working_dir_rev()
            self.repo.get_info(self.integer_rev)
        self._sync_decimal_rev()

    def runhooks(self):
        Util.set_proxy()
        self._set_boto()
        Util.chdir(self.repo.src_dir)
        self._gclient(cmd_type='runhooks')

    def makefile(self):
        Util.chdir(self.repo.src_dir)
        if self.target_arch == 'x86_64':
            target_arch_tmp = 'x64'
        else:
            target_arch_tmp = self.target_arch

        gn_args = 'enable_nacl=false proprietary_codecs=true'
        if self.target_os == 'linux':
            gn_args += ' is_clang=true'
        if self.target_os in ['linux', 'android', 'chromeos']:
            gn_args += ' target_os=\\\"%s\\\" target_cpu=\\\"%s\\\"' % (self.target_os, target_arch_tmp)
        if self.target_os == 'darwin':
            gn_args += ' cc_wrapper="ccache"'
        if self.no_component_build:
            gn_args += ' is_component_build=false'
        else:
            gn_args += ' is_component_build=true'
        if self.build_type == 'release':
            gn_args += ' is_debug=false strip_absolute_paths_from_debug_symbols=true'
        else:
            gn_args += ' is_debug=true'
        if self.no_warning_as_error:
            gn_args += ' treat_warnings_as_errors=false'
        else:
            gn_args += ' treat_warnings_as_errors=true'
        gn_args += ' symbol_level=%s' % self.symbol_level

        # for windows, it has to use "" instead of ''
        if self.target_os == 'windows':
            gn_args += ' ffmpeg_branding=\\\"Chrome\\\"'
            quotation = '\"'
        else:
            gn_args += ' ffmpeg_branding=\\\"Chrome\\\"'
            quotation = '\''

        cmd = 'gn --args=%s%s%s gen %s' % (quotation, gn_args, quotation, self.out_dir)
        Util.info('GN ARGS: {}'.format(gn_args))
        result = self.program.execute(cmd)
        if result[0]:
            Util.error('Failed to makefile')

    def build(self, build_max_fail, build_target, build_verbose):
        Util.chdir(self.src_dir)
        if not os.path.exists(self.out_dir):
            self.makefile()

        if self.rev:
            tmp_rev = self.rev
        else:
            tmp_rev = self.repo.get_working_dir_rev()
        Util.info('Begin to build rev %s' % tmp_rev)
        Util.chdir(self.src_dir + '/build/util')
        self.program.execute('python lastchange.py -o LASTCHANGE')

        if self.target_os == 'android' and build_target == 'default':
            build_target = 'chrome_public'
        elif self.target_os in ['linux', 'windows', 'darwin', 'chromeos'] and build_target == 'default':
            build_target = 'chrome'

        ninja_cmd = 'ninja -k' + str(build_max_fail) + ' -j' + str(Util.cpu_count) + ' -C ' + self.out_dir
        if self.target_os == 'android' and build_target == 'webview_shell':
            ninja_cmd += ' android_webview_apk libwebviewchromium'
        elif self.target_os == 'android' and build_target == 'content_shell':
            ninja_cmd += ' content_shell_apk'
        elif self.target_os == 'android' and build_target == 'chrome_shell':
            ninja_cmd += ' chrome_shell_apk'
        elif self.target_os == 'android' and build_target == 'chrome_public':
            ninja_cmd += ' chrome_public_apk'
        elif self.target_os == 'android' and build_target == 'webview':
            ninja_cmd += ' system_webview_apk'
        else:
            ninja_cmd += ' ' + build_target

        if self.target_os in ['linux', 'windows', 'darwin'] and build_target == 'chrome':
            ninja_cmd += ' chromedriver'

        if build_verbose:
            ninja_cmd += ' -v'

        Util.chdir(self.src_dir)
        self.program.execute(ninja_cmd, show_duration=True)

    def backup(self, backup_no_symbol):
        if self.rev:
            tmp_rev = self.rev
        else:
            tmp_rev = self.repo.get_working_dir_rev()
        Util.info('Begin to backup rev %s' % tmp_rev)
        backup_dir = '%s/%s' % (self.build_dir, tmp_rev)
        if os.path.exists(backup_dir):
            Util.error('Backup folder "%s" alreadys exists' % backup_dir)

        Util.chdir(self.src_dir)
        chrome_files = self.program.execute('gn desc //%s //chrome:chrome runtime_deps' % self.out_dir, return_out=True)[1].rstrip('\n').split('\n')
        chromedriver_files = self.program.execute('gn desc //%s //chrome/test/chromedriver:chromedriver runtime_deps' % self.out_dir, return_out=True)[1].rstrip('\n').split('\n')
        origin_files = Util.union_list(chrome_files, chromedriver_files)
        exclude_files = ['../', 'gen/', 'angledata/', 'pyproto/', './libVkLayer']
        files = []
        for file in origin_files:
            if backup_no_symbol and file.endswith('.pdb'):
                continue

            for exclude_file in exclude_files:
                if file.startswith(exclude_file):
                    break
            else:
                files.append(file)

        Util.chdir(self.out_dir)
        for file in files:
            if re.match(r'\./', file):
                file = file[2:]

            if re.match('initialexe/', file):
                file = file[len('initialexe/'):]

            dir_name = os.path.dirname(file)
            dst_dir = '%s/%s' % (backup_dir, dir_name)
            Util.ensure_dir(dst_dir)
            shutil.copy(file, dst_dir)

    def backup_webgl(self):
        # generate telemetry_gpu_integration_test
        cmd = 'vpython tools/mb/mb.py zip %s telemetry_gpu_integration_test %s/%s.zip' % (self.out_dir, self.build_dir, self.rev)
        result = self.program.execute(cmd)
        if result[0]:
            Util.error('Failed to generate telemetry_gpu_integration_test')

    def run(self, run_extra_args):
        if self.rev:
            cmd = '%s/build/%s' % (self.root_dir, self.rev)
        else:
            cmd = '%s/%s' % (self.src_dir, self.out_dir)

        cmd += '/chrome'
        if Util.host_os == 'windows':
            cmd += '.exe'
        if run_extra_args:
            cmd += ' %s' % run_extra_args
        self.program.execute(cmd)

    def download(self):
        rev = self.rev
        if not rev:
            Util.error('Please designate revision')

        download_dir = '%s/%s-%s/tmp' % (MainRepo.ignore_chromium_download_dir, self.target_arch, self.target_os)
        Util.ensure_dir(download_dir)
        Util.chdir(download_dir)

        if self.target_os == 'darwin':
            target_arch_tmp = ''
        elif self.target_arch == 'x86_64':
            target_arch_tmp = '_x64'
        else:
            target_arch_tmp = ''

        if self.target_os == 'windows':
            target_os_tmp = 'Win'
            target_os_tmp2 = 'win'
        elif self.target_os == 'darwin':
            target_os_tmp = 'Mac'
            target_os_tmp2 = 'mac'
        else:
            target_os_tmp = target_os.capitalize()
            target_os_tmp2 = target_os

        rev_zip = '%s.zip' % rev
        if os.path.exists(rev_zip) and os.stat(rev_zip).st_size == 0:
            Util.ensure_nofile(rev_zip)
        if os.path.exists('../%s' % rev_zip):
            Util.info('%s has been downloaded' % rev_zip)
        else:
            # linux64: Linux_x64/<rev>/chrome-linux.zip
            # win64: Win_x64/<rev>/chrome-win32.zip
            # mac64: Mac/<rev>/chrome-mac.zip
            if Util.host_os == 'windows':
                wget = Util.use_backslash('%s/wget64.exe' % MainRepo.tool_dir)
            else:
                wget = 'wget'

            if self.target_os == 'android':
                # https://commondatastorage.googleapis.com/chromium-browser-snapshots/index.html?prefix=Android/
                # https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Android%2F607944%2Fchrome-android.zip?generation=1542192867201693&alt=media
                archive_url = '"https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Android%2F' + rev + '%2Fchrome-android.zip?generation=1542192867201693&alt=media"'
            else:
                archive_url = 'http://commondatastorage.googleapis.com/chromium-browser-snapshots/%s%s/%s/chrome-%s.zip' % (target_os_tmp, target_arch_tmp, rev, target_os_tmp2)
            self.program.execute('%s %s --show-progress -O %s' % (wget, archive_url, rev_zip))
            if (os.path.getsize(rev_zip) == 0):
                Util.warning('Could not find revision %s' % rev)
                self.program.execute('rm %s' % rev_zip)
            else:
                self.program.execute('mv %s ../' % rev_zip)

    def _set_boto(self):
        boto_file = MainRepo.ignore_chromium_boto_file
        if not os.path.exists(boto_file):
            lines = [
                '[Boto]',
                'proxy = %s' % Util.proxy_address,
                'proxy_port = %s' % Util.proxy_port,
                'proxy_rdns = True',
            ]
            Util.write_file(boto_file, lines)

        Util.set_env('NO_AUTH_BOTO_CONFIG', boto_file)

    def _gclient(self, cmd_type, extra_cmd=''):
        cmd = 'gclient ' + cmd_type
        if extra_cmd:
            cmd += ' ' + extra_cmd
        if cmd_type == 'sync':
            cmd += ' -n -D -R --break_repo_locks --delete_unversioned_trees'
        cmd += ' -j' + str(Util.cpu_count)

        self.program.execute(cmd)

    def _sync_integer_rev(self):
        if self.integer_rev:
            roll_repo = self.repo.info[Repo.INFO_INDEX_REV_INFO][self.integer_rev][Repo.REV_INFO_INDEX_ROLL_REPO]
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
            self.program.execute('git pull')
            extra_cmd = ''

        self._gclient(cmd_type='sync', extra_cmd=extra_cmd)

    def _sync_decimal_rev(self):
        roll_repo = self.repo.info[Repo.INFO_INDEX_REV_INFO][self.integer_rev][Repo.REV_INFO_INDEX_ROLL_REPO]
        roll_count = self.repo.info[Repo.INFO_INDEX_REV_INFO][self.integer_rev][Repo.REV_INFO_INDEX_ROLL_COUNT]
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

        roll_hash = self.repo.info[Repo.INFO_INDEX_REV_INFO][self.integer_rev][Repo.REV_INFO_INDEX_ROLL_HASH]
        roll_count_diff = roll_count - self.decimal_rev
        if roll_count_diff < 0:
            Util.error('The decimal part of rev should be less than %s' % roll_count)
        Util.chdir('%s/%s' % (self.root_dir, roll_repo))
        cmd = 'git reset --hard %s~%s' % (roll_hash, roll_count_diff)
        self.program.execute(cmd)
        cmd = 'git rev-parse --abbrev-ref HEAD'
        branch = self.program.execute(cmd, return_out=True, show_cmd=False)[1].strip()
        if not branch == 'master':
            Util.error('Repo %s is not on master' % roll_repo)

    def _get_relative_out_dir(self, target_arch, target_os, symbol_level=0, no_component_build=False):
        relative_out_dir = 'out-%s-%s' % (target_arch, target_os)
        relative_out_dir += '-symbol%s' % symbol_level

        if no_component_build:
            relative_out_dir += '-nocomponent'
        else:
            relative_out_dir += '-component'

        return relative_out_dir
