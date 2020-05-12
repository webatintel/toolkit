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

class Mesa():
    def __init__(self):
        self._parse_args()
        args = self.program.args
        self.build_type = args.build_type
        self.branch = args.branch
        build_force = args.build_force
        if args.branch != 'master':
            build_force = True
        self.build_force = build_force
        self.drm_dir = 'drm-master'
        self.mesa_dir = 'mesa-%s' % self.branch
        if args.build_module == 'all':
            self.modules = ['drm', 'mesa']
        else:
            self.modules = [args.build_module]
        self.hashes = []
        self.rev = args.rev

        self.run_cmd = args.run
        self.type = args.type

        self.args = args

        self._handle_ops()

    def init(self):
        if not os.path.exists(self.drm_dir):
            self.program.execute('git clone https://gitlab.freedesktop.org/mesa/drm %s' % self.drm_dir)

        if not os.path.exists(self.mesa_dir):
            if self.args.repo == 'chromeos':
                self.program.execute('git clone -b %s https://chromium.googlesource.com/chromiumos/third_party/mesa %s' % (self.branch, self.mesa_dir))
            else:
                self.program.execute('git clone -b %s https://gitlab.freedesktop.org/mesa/mesa %s' % (self.branch, self.mesa_dir))

    def sync(self):
        for dir in [self.drm_dir, self.mesa_dir]:
            Util.chdir('%s/%s' % (self.program.root_dir, dir))
            self.program.execute('git pull --rebase')

    def build(self):
        self._init_hash()

        if Util.HOST_OS == 'linux' and Util.HOST_OS_ID == 'ubuntu':
            Util.ensure_pkg('meson libomxil-bellagio-dev libpciaccess-dev x11proto-dri3-dev x11proto-present-dev xutils-dev python-mako x11proto-gl-dev x11proto-dri2-dev libxcb-dri3-dev libxcb-present-dev libxshmfence-dev libx11-xcb-dev libxcb-glx0-dev libxcb-dri2-0-dev libxxf86vm-dev python3-mako')

        if re.search('-', str(self.rev)):
            tmp_revs = self.rev.split('-')
            min_rev = self._unify_to_rev(tmp_revs[0])
            max_rev = self._unify_to_rev(tmp_revs[1])
        elif self.rev == 'latest':
            min_rev = len(self.hashes)
            max_rev = min_rev
        else:
            tmp_rev = self._unify_to_rev(self.rev)
            min_rev = tmp_rev
            max_rev = tmp_rev

        Util.info('Begin to build rev from %s to %s' % (min_rev, max_rev))
        i = min_rev
        while i <= max_rev:
            if i > len(self.hashes):
                Util.info('Rev %s exceeds the max git revision' % i)
                break
            if i % self.args.rev_stride:
                i += 1
                continue
            self._build_one(i, self._rev_to_hash(i))
            i += 1

    def revtohash(self):
        tmp_rev = self.args.revtohash
        Util.info('The hash for rev %s is %s' % (tmp_rev, self._rev_to_hash(tmp_rev)))

    def hashtorev(self):
        tmp_hash = self.args.hashtorev
        Util.info('The rev of hash %s is %s' % (tmp_hash, _hash_to_rev(tmp_hash)))

    def run(self):
        if self.rev == 'system':
            Util.info('Use system Mesa')
        else:
            backup_dir = '%s/backup' % self.program.root_dir
            (rev_dir, rev) = Util.get_rev_dir(backup_dir, 'mesa', self.rev)
            mesa_dir = '%s/%s' % (backup_dir, rev_dir)
            Util.set_env('LD_LIBRARY_PATH', '%s/lib' % mesa_dir)
            Util.set_env('LIBGL_DRIVERS_PATH', '%s/lib/dri' % mesa_dir)
            if self.type == 'iris':
                Util.set_env('MESA_LOADER_DRIVER_OVERRIDE', 'iris')
            else:
                Util.set_env('MESA_LOADER_DRIVER_OVERRIDE', '')

            Util.set_env('VK_ICD_FILENAMES', '%s/share/vulkan/icd.d/intel_icd.x86_64.json' % (mesa_dir))
            Util.info('Use mesa at %s' % mesa_dir)
        self.program.execute(self.run_cmd)

    def _init_hash(self):
        if not self.hashes:
            Util.chdir('%s/%s' % (self.program.root_dir, self.mesa_dir))
            result = self.program.execute('git log --pretty=format:"%H" --reverse', return_out=True, show_cmd=False)
            self.hashes = result[1].split('\n')

    def _rev_to_hash(self, rev):
        self._init_hash()
        return self.hashes[rev - 1]

    def _hash_to_rev(self, hash):
        self._init_hash()
        for i, tmp_hash in reversed(list(enumerate(self.hashes))):
            if tmp_hash == hash:
                return i + 1
        Util.error('Could not find rev for hash %s' % hash)

    def _build_one(self, rev, hash):
        date = Util.get_working_dir_commit_info('%s/%s' % (self.program.root_dir, self.mesa_dir))[0]
        single_backup_dir = '%s/backup/%s-%s-%s-%s-%s' % (self.program.root_dir, self.mesa_dir, self.build_type, date, rev, hash)
        building_dir = single_backup_dir.replace('backup', 'backup/building')

        if (os.path.exists(building_dir) or os.path.exists('%s' % single_backup_dir)) and os.path.exists(single_backup_dir + '/lib/dri/i965_dri.so') and not self.build_force:
            Util.info('Rev %s has been built, so just skip it' % rev)
            return

        Util.info('Begin to build revision %s, hash %s' % (rev, hash))

        if self.args.clean or not self.build_force:
            self._clean(self.modules)
        elif self.branch != 'master':
            self._clean(['drm'])

        if 'drm' in self.modules:
            Util.chdir('%s/%s' % (self.program.root_dir, self.drm_dir))
            if self.args.build_system == 'autotools':
                build_cmd = './autogen.sh CFLAGS="-O2" CXXFLAGS="-O2" --prefix=%s --enable-libkms --enable-intel --disable-vmwgfx --disable-radeon --disable-amdgpu --disable-nouveau' % building_dir
                if self.build_type == 'debug':
                    build_cmd += ' --enable-debug'
                build_cmd += ' && make -j%s && make install' % Util.CPU_COUNT
            elif self.args.build_system == 'meson':
                Util.ensure_nodir('build')
                Util.ensure_dir('build')
                build_cmd = 'meson build/ -Dprefix=%s -Dlibkms=true -Dintel=true -Dvmwgfx=false -Dradeon=false -Damdgpu=false -Dnouveau=false' % building_dir
                if self.build_type == 'release':
                    build_cmd += ' -Dbuildtype=release'
                build_cmd += ' && ninja -j%s -C build/ install' % Util.CPU_COUNT

            result = self.program.execute(build_cmd)
            if result[0]:
                return False

        if 'mesa' in self.modules:
            Util.chdir('%s/%s' % (self.program.root_dir, self.mesa_dir))
            if not self.build_force:
                self.program.execute('git reset --hard %s' % hash)

            # update git hash
            result = self.program.execute('git log -n 1 --oneline', return_out=True, show_cmd=False)
            self.program.execute('echo "#define MESA_GIT_SHA1 \\\"git-%s\\\"" >src/mesa/main/git_sha1.h' % result[1].split()[0])
            if self.args.build_system == 'autotools':
                build_cmd = 'PKG_CONFIG_PATH=%s/lib/pkgconfig ./autogen.sh --enable-autotools CFLAGS="-O2" CXXFLAGS="-O2" --prefix=%s --with-dri-drivers="i915 i965" --with-dri-driverdir=%s/lib/dri --enable-gles1 --enable-gles2 --enable-shared-glapi --with-gallium-drivers= --with-egl-platforms=x11,drm --enable-texture-float --enable-gbm --enable-glx-tls --enable-dri3' % (building_dir, building_dir, building_dir)
                if not self.args.build_novulkan:
                    build_cmd += ' --with-vulkan-driver="intel"'
                if build_type == 'debug':
                    build_cmd += ' --enable-debug'
                build_cmd += ' && make -j%s && make install' % Util.CPU_COUNT
            elif self.args.build_system == 'meson':
                # missing options: -enable-texture-float --enable-glx-tls
                Util.ensure_nodir('build')
                Util.ensure_dir('build')
                build_cmd = 'PKG_CONFIG_PATH=%s/lib/pkgconfig meson build/ -Dprefix=%s -Dvulkan-drivers=intel -Ddri-drivers=i915,i965 -Ddri-drivers-path=%s/lib/dri -Dgles1=true -Dgles2=true -Dshared-glapi=true -Dplatforms=x11,drm -Dgbm=true -Ddri3=true -Dgallium-drivers=iris' % (building_dir, building_dir, building_dir)
                if not self.args.build_novulkan:
                    build_cmd += ' -Dvulkan-drivers=intel'
                if self.build_type == 'release':
                    build_cmd += ' -Dbuildtype=release'
                build_cmd += ' && ninja -j%s -C build/ install' % Util.CPU_COUNT

            result = self.program.execute(build_cmd)
            if result[0]:
                return False

        for line in fileinput.input('%s/share/vulkan/icd.d/intel_icd.x86_64.json' % building_dir, inplace=1):
            match = re.search('"library_path": "(.*)"', line)
            if match:
                line = line.replace(match.group(1), '../../../lib/x86_64-linux-gnu/libvulkan_intel.so')
            sys.stdout.write(line)
        fileinput.close()

        self.program.execute('mv %s %s' % (building_dir, single_backup_dir))
        return True

    def _clean(self, modules):
        if 'drm' in modules:
            Util.chdir('%s/%s' % (self.program.root_dir, self.drm_dir))
            self.program.execute('make distclean', exit_on_error=False)

        if 'mesa' in modules:
            Util.chdir('%s/%s' % (self.program.root_dir, self.mesa_dir))
            self.program.execute('make distclean', exit_on_error=False)

    def _unify_to_rev(self, str):
        if len(str) == 40:
            return _hash_to_rev(str)

        try:
            rev = int(str)
        except:
            Util.error('Input %s is not correct' % str)
        return rev

    def _parse_args(self):
        parser = argparse.ArgumentParser(description='description',
                                        formatter_class=argparse.RawTextHelpFormatter,
                                        epilog='''
examples:
python %(prog)s --sync --build
python %(prog)s --build --build-system autotools --rev-stride 50 --build-novulkan --rev 96700-96900
python %(prog)s --build --dir-install /workspace/install/mesa-master-release-9999999 --build-replace
python %(prog)s --build --dir-install /workspace/install/mesa-master-release-9999999 --build-replace --clean  # if build fails
python %(prog)s --hashtorev e58a10af640ba58b6001f5c5ad750b782547da76
python %(prog)s --revtohash 1
    ''')

        parser.add_argument('--repo', dest='repo', help='repo, can be freedesktop or chromeos', default='freedesktop')
        parser.add_argument('--init', dest='init', help='init', action='store_true')
        parser.add_argument('--sync', dest='sync', help='sync', action='store_true')
        parser.add_argument('--build', dest='build', help='build', action='store_true')
        parser.add_argument('--run', dest='run', help='run')
        parser.add_argument('--type', dest='type', help='type', default='i965')
        parser.add_argument('--branch', dest='branch', help='branch', default='master')
        parser.add_argument('--rev', dest='rev', help='rev, can be system, latest, or any specific revision', default='latest')
        parser.add_argument('--rev-stride', dest='rev_stride', help='rev stride', type=int, default=1)
        parser.add_argument('--clean', dest='clean', help='clean when build_force', action='store_true')
        parser.add_argument('--revtohash', dest='revtohash', help='get hash of commit rev starting from 1', type=int)
        parser.add_argument('--hashtorev', dest='hashtorev', help='get commit rev starting from 1 of hash')
        parser.add_argument('--build-type', dest='build_type', help='build type', default='release')
        parser.add_argument('--build-module', dest='build_module', help='build module', default='all')
        parser.add_argument('--build-force', dest='build_force', help='no reset of source code', action='store_true')
        parser.add_argument('--build-system', dest='build_system', help='build system', default='meson')
        parser.add_argument('--build-novulkan', dest='build_novulkan', help='build novulkan', action='store_true')

        self.program = Program(parser)

    def _handle_ops(self):
        args = self.program.args
        if args.init:
            self.init()
        if args.sync:
            self.sync()
        if args.build:
            self.build()
        if args.revtohash:
            self.revtohash()
        if args.hashtorev:
            self.hashtorev()
        if args.run:
            self.run()

if __name__ == '__main__':
    Mesa()

