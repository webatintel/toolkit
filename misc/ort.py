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
    lines = subprocess.Popen("ls -l %s" % __file__, shell=True, stdout=subprocess.PIPE).stdout.readlines()
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
        parser.add_argument("--build-web", dest="build_web", help="build web", action="store_true")
        parser.add_argument("--build-wgpu", dest="build_wgpu", help="build wgpu", action="store_true")
        parser.add_argument("--build-wasm64", dest="build_wasm64", help="build wasm64", action="store_true")
        parser.add_argument(
            "--build-small", dest="build_small", help="build if only WebGPU EP is changed", action="store_true"
        )
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
        parser.add_argument("--split-model", dest="split_model", help="split model for a external data file")

        parser.epilog = """
examples:
{0} {1} --build
""".format(
            Util.PYTHON, parser.prog
        )

        super().__init__(parser)

        Util.chdir(self.root_dir, verbose=True)
        if Util.HOST_OS == Util.WINDOWS:
            self.build_cmd = "build.bat"
            os_dir = "Windows"
        else:
            self.build_cmd = "./build.sh"
            os_dir = "Linux"

        self.build_type = self.args.build_type
        self.build_dir = f"build/{os_dir}"

        self._handle_ops()

    def split_model(self):
        import onnx

        model_path = self.args.split_model
        model_name = os.path.basename(model_path).replace('.onnx', '')
        Util.chdir(os.path.dirname(model_path), verbose=True)
        onnx_model = onnx.load(f'{model_name}.onnx')
        onnx.save_model(
            onnx_model,
            f'{model_name}-ext.onnx',
            save_as_external_data=True,
            all_tensors_to_one_file=True,
            location=f'{model_name}-ext.data',
            size_threshold=1024,
            convert_attribute=False,
        )

    def sync(self):
        pass

    def build_web(self):
        timer = Timer()

        if not self.args.build_skip_wasm and not self.args.build_small:
            # --enable_wasm_debug_info may cause unit test crash
            cmd = f"{self.build_cmd} --config {self.build_type} --build_wasm --enable_wasm_simd --enable_wasm_threads --parallel --skip_tests --skip_submodule_sync --use_jsep --target onnxruntime_webassembly"
            if self.args.build_type == "Debug":
                cmd += " --enable_wasm_debug_info"
            else:
                cmd += " --disable_wasm_exception_catching --disable_rtti"

            if self.args.build_wasm64:
                cmd += " --enable_wasm_memory64"
            Util.execute(cmd, show_cmd=True, show_duration=True)

        if not self.args.build_skip_ci:
            Util.chdir(f"{self.root_dir}/js", verbose=True)
            Util.execute("npm ci", show_cmd=True)

            Util.chdir(f"{self.root_dir}/js/common", verbose=True)
            Util.execute("npm ci", show_cmd=True)

            Util.chdir(f"{self.root_dir}/js/web", verbose=True)
            Util.execute("npm ci", show_cmd=True)

        if not self.args.build_skip_pull_wasm and not self.args.build_small:
            Util.chdir(f"{self.root_dir}/js/web", verbose=True)
            Util.execute("npm run pull:wasm", show_cmd=True, exit_on_error=False)

        file_name = "ort-wasm-simd-threaded"
        Util.copy_file(
            f"{self.root_dir}/{self.build_dir}/{self.build_type}",
            f"{file_name}.jsep.mjs",
            f"{self.root_dir}/js/web/dist",
            f"{file_name}.jsep.mjs",
            need_bk=False,
            show_cmd=True,
        )
        Util.copy_file(
            f"{self.root_dir}/{self.build_dir}/{self.build_type}",
            f"{file_name}.jsep.wasm",
            f"{self.root_dir}/js/web/dist",
            f"{file_name}.jsep.wasm",
            need_bk=False,
            show_cmd=True,
        )

        Util.chdir(f"{self.root_dir}/js/web", verbose=True)
        Util.execute("npm run build", show_cmd=True)

        Util.info(f"{timer.stop()} was spent to build")

    def build_wgpu(self):
        timer = Timer()
        cmd = f"{self.build_cmd} --config {self.build_type} --parallel --skip_tests --skip_submodule_sync --use_webgpu"
        Util.execute(cmd, show_cmd=True, show_duration=True)
        Util.info(f"{timer.stop()} was spent to build")

    def lint(self):
        Util.chdir(f"{self.root_dir}/js", verbose=True)
        Util.execute("npm run lint", show_cmd=True)

    def _handle_ops(self):
        args = self.args
        if args.sync:
            self.sync()
        if args.build_web:
            self.build_web()
        if args.build_wgpu:
            self.build_wgpu()
        if args.build_small:
            self.build()
        if args.lint:
            self.lint()
        if args.split_model:
            self.split_model()


if __name__ == "__main__":
    Ort()
