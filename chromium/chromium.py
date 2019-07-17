import os
import re
import subprocess
import sys
output = subprocess.Popen('ls -l %s' % __file__, shell=True, stdout=subprocess.PIPE).stdout.readline()
if re.search('->', output):
    output = output.split(' ')[-1].strip()
    match = re.match('/(.)/', output)
    if match:
        drive = match.group(1)
        output = output.replace('/%s/' % drive, '%s:/' % drive)
    chromium_dir = os.path.dirname(os.path.realpath(output))
else:
    chromium_dir = sys.path[0]
sys.path.append(chromium_dir)
sys.path.append(chromium_dir + '/..')

from util.util import * # pylint: disable=unused-wildcard-import
from repo import *

class Chromium():
    def __init__(self):
        parser = argparse.ArgumentParser(description='Script about Chromium',
                                        formatter_class=argparse.RawTextHelpFormatter,
                                        epilog='''
examples:
  python %(prog)s --sync --rev 674968
  python %(prog)s --sync --runhooks --makefile --build --backup --download
''')
        parser.add_argument('--rev', dest='rev', type=int, help='revision for sync')
        parser.add_argument('--hash', dest='hash', help='hash of revision for sync')
        parser.add_argument('--target-arch', dest='target_arch', help='target arch', choices=['x86', 'arm', 'x86_64', 'arm64'], default='default')
        parser.add_argument('--target-os', dest='target_os', help='target os, choices can be android, linux, chromeos, windows', default='default')
        parser.add_argument('--out-dir', dest='out_dir', help='out dir')

        parser.add_argument('--sync', dest='sync', help='sync to a specific rev if designated, otherwise, sync to upstream', action='store_true')
        parser.add_argument('--sync-reset', dest='sync_reset', help='do a reset before syncing', action='store_true')
        parser.add_argument('--runhooks', dest='runhooks', help='runhooks', action='store_true')
        parser.add_argument('--makefile', dest='makefile', help='generate makefile', action='store_true')
        parser.add_argument('--build', dest='build', help='build', action='store_true')
        parser.add_argument('--build-type', dest='build_type', help='build type', choices=['release', 'debug'], default='release')
        parser.add_argument('--build-nocomponent', dest='build_nocomponent', help='build with static library', action='store_true')
        parser.add_argument('--build-nojumbo', dest='build_nojumbo', help='build not using jumbo', action='store_true')
        parser.add_argument('--build-symbol', dest='build_symbol', help='symbol level', type=int, default=0)
        parser.add_argument('--build-target', dest='build_target', help='target to build, choices can be chrome, webview_shell, content_shell, chrome_shell, chromedriver, cpu_features, system_webview_apk, android_webview_telemetry_shell_apk, etc.', default='default')
        parser.add_argument('--build-verbose', dest='build_verbose', help='output verbose info. Find log at out/Release/.ninja_log', action='store_true')
        parser.add_argument('--build-asan', dest='build_asan', help='enable asan by adding asan=1 into GYP_DEFINES', action='store_true')
        parser.add_argument('--build-warning-as-error', dest='build_warning_as_error', help='treat warning as error', action='store_true', default=True)
        parser.add_argument('--build-max-fail', dest='build_max_fail', help='build keeps going until N jobs fail', type=int, default=1)
        parser.add_argument('--backup', dest='backup', help='backup', action='store_true')
        parser.add_argument('--backup-nosymbol', dest='backup_nosymbol', help='backup without symbol', action='store_true')
        parser.add_argument('--run', dest='run', help='run', action='store_true')
        parser.add_argument('--run-extra-args', dest='run_extra_args', help='run with extra args', default='')
        parser.add_argument('--download', dest='download', help='download', action='store_true')

        program = Program(parser)

        if len(sys.argv) <= 1:
            parser.print_help()
            quit()

        if program.args.target_os:
            target_os = program.args.target_os
            if target_os == 'default':
                target_os = Util.host_os

        build_target = program.args.build_target
        if target_os == 'android' and build_target == 'default':
            build_target = 'chrome_public'
        elif target_os in ['linux', 'windows', 'darwin', 'chromeos'] and build_target == 'default':
            build_target = 'chrome'
        elif build_target == 'chrome_public':
            target_os = 'android'

        target_arch = program.args.target_arch
        if target_arch == 'default':
            target_arch = 'x86_64'

        if program.args.out_dir:
            self.relative_out_dir = program.args.out_dir
        else:
            self.relative_out_dir = self._get_relative_out_dir(target_arch, target_os, program.args.build_nocomponent, program.args.build_symbol, program.args.build_nojumbo)

        self.src_dir = program.root_dir + '/src'
        self.out_dir = self.src_dir + '/' + self.relative_out_dir + '/' + program.args.build_type.capitalize()
        self.build_type = program.args.build_type
        self.build_type_cap = self.build_type.capitalize()
        self.repo = Repo(self.src_dir, program)
        self.target_arch = target_arch
        self.target_os = target_os
        self.build_target = build_target
        self.program = program

        self.sync()
        self.runhooks()
        self.makefile()
        self.build()
        self.backup()
        self.run()
        self.download()

    def sync(self, force=False):
        if not self.program.args.sync and not force:
            return

        Util.set_proxy()
        self._set_boto()
        Util.chdir(self.repo.src_dir)

        tmp_hash = ''
        if self.program.args.hash:
            tmp_hash = self.program.args.hash
        elif self.program.args.rev:
            tmp_hash = self.repo.get_hash_from_rev(self.program.args.rev)
        if tmp_hash:
            extra_cmd = '--revision src@' + tmp_hash
        else:
            extra_cmd = ''
            if self.program.args.sync_reset:
                self.program.execute('git reset --hard HEAD && git clean -f -d')
            self.program.execute('git pull --rebase')

        self._gclient(cmd_type='sync', extra_cmd=extra_cmd)

    def runhooks(self, force=False):
        if not self.program.args.runhooks and not force:
            return

        Util.set_proxy()
        self._set_boto()
        Util.chdir(self.repo.src_dir)
        self._gclient(cmd_type='runhooks')

    def makefile(self, force=False):
        if not self.program.args.makefile and not force:
            return

        Util.chdir(self.repo.src_dir)

        if self.target_arch == 'x86_64':
            target_arch_tmp = 'x64'
        else:
            target_arch_tmp = self.target_arch

        args_gn = 'enable_nacl=false proprietary_codecs=true'
        if self.target_os == 'linux':
            args_gn += ' is_clang=true'
        if self.target_os in ['linux', 'android', 'chromeos']:
            args_gn += ' target_os="%s" target_cpu="%s"' % (self.target_os, target_arch_tmp)
        if self.target_os == 'darwin':
            args_gn += ' cc_wrapper="ccache"'
        if self.program.args.build_nocomponent:
            args_gn += ' is_component_build=false'
        else:
            args_gn += ' is_component_build=true'
        if self.program.args.build_nojumbo:
            args_gn += ' use_jumbo_build=false'
        else:
            args_gn += ' use_jumbo_build=true'
        if self.program.args.build_type == 'release':
            args_gn += ' is_debug=false strip_absolute_paths_from_debug_symbols=true'
        else:
            args_gn += ' is_debug=true'
        if self.program.args.build_warning_as_error:
            args_gn += ' treat_warnings_as_errors=true'
        else:
            args_gn += ' treat_warnings_as_errors=false'
        args_gn += ' symbol_level=%s' % self.program.args.build_symbol

        # for windows, it has to use "" instead of ''
        if self.target_os == 'windows':
            args_gn += ' ffmpeg_branding=\\\"Chrome\\\"'
            quotation = '\"'
        else:
            args_gn += ' ffmpeg_branding="Chrome"'
            quotation = '\''

        cmd = 'gn --args=%s%s%s gen %s' % (quotation, args_gn, quotation, self.out_dir)
        Util.info('GN ARGS: {}'.format(args_gn))

        self.program.execute(cmd)

    def build(self, force=False):
        if not self.program.args.build and not force:
            return

        if not os.path.exists(self.out_dir):
            self.makefile(force=True)

        Util.info('Begin to build rev %s' % self.repo.get_working_dir_rev())
        Util.chdir(self.src_dir + '/build/util')
        self.program.execute('python lastchange.py -o LASTCHANGE')

        ninja_cmd = 'ninja -k' + str(self.program.args.build_max_fail) + ' -j' + str(Util.cpu_count) + ' -C ' + self.out_dir
        if self.target_os == 'android' and self.build_target == 'webview_shell':
            ninja_cmd += ' android_webview_apk libwebviewchromium'
        elif self.target_os == 'android' and self.build_target == 'content_shell':
            ninja_cmd += ' content_shell_apk'
        elif self.target_os == 'android' and self.build_target == 'chrome_shell':
            ninja_cmd += ' chrome_shell_apk'
        elif self.target_os == 'android' and self.build_target == 'chrome_public':
            ninja_cmd += ' chrome_public_apk'
        elif self.target_os == 'android' and self.build_target == 'webview':
            ninja_cmd += ' system_webview_apk'
        else:
            ninja_cmd += ' ' + self.build_target

        if self.target_os in ['linux', 'windows', 'darwin'] and self.build_target == 'chrome':
            ninja_cmd += ' chromedriver'

        if self.program.args.build_verbose:
            ninja_cmd += ' -v'

        self.program.execute(ninja_cmd, show_duration=True)

    def backup(self, force=False):
        if not self.program.args.backup:
            return

        rev = self.repo.get_working_dir_rev()
        Util.info('Begin to backup rev %s' % rev)
        backup_dir = '%s/%s' % (MainRepo.ignore_chromium_selfbuilt_dir, rev)
        if os.path.exists(backup_dir):
            Util.error('Backup folder "%s" alreadys exists' % backup_dir)

        Util.chdir(self.src_dir)
        chrome_files = self.program.execute('gn desc //%s/%s //chrome:chrome runtime_deps' % (self.relative_out_dir, self.build_type_cap), return_out=True)[1].rstrip('\n').split('\n')
        chromedriver_files = self.program.execute('gn desc //%s/%s //chrome/test/chromedriver:chromedriver runtime_deps' % (self.relative_out_dir, self.build_type_cap), return_out=True)[1].rstrip('\n').split('\n')
        origin_files = Util.union_list(chrome_files, chromedriver_files)
        exclude_files = ['../', 'gen/', 'angledata/', 'pyproto/', './libVkLayer']
        files = []
        for file in origin_files:
            if self.program.args.backup_nosymbol and file.endswith('.pdb'):
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

    def run(self):
        if not self.program.args.run:
            return

        if self.program.args.rev:
            Util.chdir('%s/%s' % (MainRepo.ignore_chromium_selfbuilt_dir, self.program.args.rev))
        else:
            Util.chdir(self.out_dir)

        cmd = 'chrome'
        if Util.host_os == 'windows':
            cmd += '.exe'
        cmd += ' %s' % self.program.args.run_extra_args
        self.program.execute(cmd)

    def download(self):
        if not self.program.args.download:
            return

        rev = self.program.args.rev
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
        if cmd_type == 'revert' or cmd_type == 'sync':
            cmd += ' -n'

        if cmd_type == 'sync' and self.program.args.sync_reset:
            cmd += ' -D -R --break_repo_locks --delete_unversioned_trees'
        cmd += ' -j' + str(Util.cpu_count)

        self.program.execute(cmd)

    def _get_relative_out_dir(self, target_arch, target_os, build_nocomponent=False, build_symbol=0, build_nojumbo=True):
        relative_out_dir = 'out-%s-%s' % (target_arch, target_os)
        relative_out_dir += '-symbol%s' % build_symbol

        if build_nocomponent:
            relative_out_dir += '-nocomponent'
        else:
            relative_out_dir += '-component'

        if build_nojumbo:
            relative_out_dir += '-nojumbo'
        else:
            relative_out_dir += '-jumbo'

        return relative_out_dir

if __name__ == '__main__':
    Chromium()
