"""
git clone --recursive https://github.com/Microsoft/onnxruntime
install cmake, node.js, python, ninja

[usage]
python ort.py --build

[reference]
https://onnxruntime.ai/docs/build/web.html
https://gist.github.com/fs-eire/a55b2c7e10a6864b9602c279b8b75dce
"""

import os
import re
import subprocess
import sys

HOST_OS = sys.platform
if HOST_OS == "win32":
    lines = subprocess.Popen(
        "dir %s" % __file__.replace("/", "\\"), shell=True, stdout=subprocess.PIPE
    ).stdout.readlines()
    for tmp_line in lines:
        match = re.search(r"\[(.*)\]", tmp_line.decode("utf-8"))
        if match:
            SCRIPT_DIR = os.path.dirname(match.group(1)).replace("\\", "/")
            break
    else:
        SCRIPT_DIR = sys.path[0]
else:
    lines = subprocess.Popen(
        "ls -l %s" % __file__, shell=True, stdout=subprocess.PIPE
    ).stdout.readlines()
    for tmp_line in lines:
        match = re.search(r".* -> (.*)", tmp_line.decode("utf-8"))
        if match:
            SCRIPT_DIR = os.path.dirname(match.group(1))
            break
    else:
        SCRIPT_DIR = sys.path[0]

sys.path.append(SCRIPT_DIR)
sys.path.append(SCRIPT_DIR + "/..")

from util.base import *


class Ort(Program):
    def __init__(self):
        parser = argparse.ArgumentParser(description="ORT")

        parser.add_argument("--sync", dest="sync", help="sync", action="store_true")
        parser.add_argument("--build", dest="build", help="build", action="store_true")
        parser.add_argument(
            "--build-type",
            dest="build_type",
            help="build type, can be Debug, MinSizeRel, Release or RelWithDebInfo",
            default="MinSizeRel",
        )
        parser.add_argument(
            "--build-skip-wasm",
            dest="build_skip_wasm",
            help="build skip wasm",
            action="store_true",
        )
        parser.add_argument(
            "--build-skip-ci",
            dest="build_skip_ci",
            help="build skip ci",
            action="store_true",
        )
        parser.add_argument(
            "--build-skip-pull-wasm",
            dest="build_skip_pull_wasm",
            help="build skip pull wasm",
            action="store_true",
        )
        parser.add_argument("--lint", dest="lint", help="lint", action="store_true")
        parser.add_argument(
            "--enable-wasm-simd",
            dest="enable_wasm_simd",
            help="enable wasm simd",
            action="store_true",
        )
        parser.add_argument(
            "--enable-wasm-threads",
            dest="enable_wasm_threads",
            help="enable wasm threads",
            action="store_true",
        )
        parser.add_argument(
            "--enable-webgpu",
            dest="enable_webgpu",
            help="enable webgpu",
            action="store_true",
        )
        parser.add_argument(
            "--enable-webnn",
            dest="enable_webnn",
            help="enable webnn",
            action="store_true",
        )

        parser.epilog = """
examples:
{0} {1} --build
""".format(
            Util.PYTHON, parser.prog
        )

        super().__init__(parser)
        self._handle_ops()

    def sync(self):
        pass

    def build(self):
        timer = Timer()
        root_dir = self.root_dir

        Util.chdir(root_dir, verbose=True)
        if Util.HOST_OS == Util.WINDOWS:
            build_cmd = "build.bat"
            os_dir = "Windows"
        else:
            build_cmd = "./build.sh"
            os_dir = "Linux"

        build_type = self.args.build_type
        enable_wasm_simd = self.args.enable_wasm_simd
        enable_wasm_threads = self.args.enable_wasm_threads
        webgpu_build_dir = f"build-webgpu/{os_dir}"
        webnn_build_dir = f"build-webnn/{os_dir}"

        webnn_targets = [
            [],
            ["simd"],
            # ["threads"],
            # ["simd", "threads"],
        ]

        if not self.args.build_skip_wasm:
            cmd = f"{build_cmd} --config {build_type} --build_wasm --skip_tests --parallel --skip_submodule_sync --disable_wasm_exception_catching"

            if self.args.enable_webgpu:
                webgpu_cmd = f"{cmd} --use_jsep --target onnxruntime_webassembly --build_dir={webgpu_build_dir}"
                if enable_wasm_simd:
                    webgpu_cmd += " --enable_wasm_simd"
                if enable_wasm_threads:
                    webgpu_cmd += " --enable_wasm_threads"
                Util.execute(webgpu_cmd, show_cmd=True, show_duration=True)

            if self.args.enable_webnn:
                for webnn_target in webnn_targets:
                    webnn_cmd = f"{cmd} --use_webnn --build_dir={webnn_build_dir}"
                    if "simd" in webnn_target:
                        webnn_cmd += " --enable_wasm_simd"
                    if "threads" in webnn_target:
                        webnn_cmd += " --enable_wasm_threads"
                    Util.execute(webnn_cmd, show_cmd=True, show_duration=True)

        if not self.args.build_skip_ci:
            Util.chdir(f"{root_dir}/js", verbose=True)
            Util.execute("npm ci", show_cmd=True)

            Util.chdir(f"{root_dir}/js/common", verbose=True)
            Util.execute("npm ci", show_cmd=True)

            Util.chdir(f"{root_dir}/js/web", verbose=True)
            Util.execute("npm ci", show_cmd=True)

        if not self.args.build_skip_pull_wasm:
            Util.chdir(f"{root_dir}/js/web", verbose=True)
            Util.execute("npm run pull:wasm", show_cmd=True, exit_on_error=False)

        if self.args.enable_webgpu:
            webgpu_file_name = "ort-wasm"
            if enable_wasm_simd:
                webgpu_file_name += "-simd"
            if enable_wasm_threads:
                webgpu_file_name += "-threaded"
            Util.copy_file(
                f"{root_dir}/{webgpu_build_dir}/{build_type}",
                f"{webgpu_file_name}.js",
                f"{root_dir}/js/web/lib/wasm/binding",
                f"{webgpu_file_name}.jsep.js",
                need_bk=False,
                show_cmd=True,
            )
            Util.copy_file(
                f"{root_dir}/{webgpu_build_dir}/{build_type}",
                f"{webgpu_file_name}.wasm",
                f"{root_dir}/js/web/dist",
                f"{webgpu_file_name}.jsep.wasm",
                need_bk=False,
                show_cmd=True,
            )

        if self.args.enable_webnn:
            for webnn_target in webnn_targets:
                webnn_file_name = "ort-wasm"
                if "simd" in webnn_target:
                    webnn_file_name += "-simd"
                if "threads" in webnn_target:
                    webnn_file_name += "-threaded"
                Util.copy_file(
                    f"{root_dir}/{webnn_build_dir}/{build_type}",
                    f"{webnn_file_name}.js",
                    f"{root_dir}/js/web/lib/wasm/binding",
                    f"{webnn_file_name}.js",
                    need_bk=False,
                    show_cmd=True,
                )
                Util.copy_file(
                    f"{root_dir}/{webnn_build_dir}/{build_type}",
                    f"{webnn_file_name}.wasm",
                    f"{root_dir}/js/web/dist",
                    f"{webnn_file_name}.wasm",
                    need_bk=False,
                    show_cmd=True,
                )
                if webnn_file_name.endswith("threaded"):
                    Util.copy_file(
                        f"{root_dir}/{webnn_build_dir}/{build_type}",
                        f"{webnn_file_name}.worker.js",
                        f"{root_dir}/js/web/lib/wasm/binding",
                        f"{webnn_file_name}.worker.js",
                        need_bk=False,
                        show_cmd=True,
                    )

        Util.chdir(f"{root_dir}/js/web", verbose=True)
        Util.execute("npm run build", show_cmd=True)

        Util.info(f"{timer.stop()} was spent to build")

    def lint(self):
        Util.chdir(f"{self.root_dir}/js", verbose=True)
        Util.execute("npm run lint", show_cmd=True)

    def _handle_ops(self):
        args = self.args
        if args.sync:
            self.sync()
        if args.build:
            self.build()
        if args.lint:
            self.lint()


if __name__ == "__main__":
    Ort()
