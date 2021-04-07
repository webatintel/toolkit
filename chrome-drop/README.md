# Chrome Drop
Chrome Drop contains below binaries:
* WebGL CTS
* ANGLE end2end tests
* WebGPU CTS
* Dawn end2end tests

The naming convention of all the binaries follow the format [yyyymmdd-revision-hash].zip

# WebGL CTS
## Command

`python content/test/gpu/run_gpu_integration_test.py webgl_conformance --disable-log-uploads --browser=release --webgl-conformance-version=[webgl-conformance-version] --extra-browser-args="[extra-browser-args]"`

[webgl-conformance-version] can be "1.0.3" and "2.0.1".<br>
[extra_browser_args] can be used for extra browser arguments. Some meaningful args are: 1) --use-angle=[angle-backend], while [angle-backend] can be d3d9, d3d11 (default) and gl.<br>

Other useful arguments:<br>
--total-shards and --shard-index are used for shard execution.<br>
--write-full-results-to is used to persist testing result to disk so that you may analyze result later.<br>

## Example

`python content/test/gpu/run_gpu_integration_test.py webgl_conformance --disable-log-uploads --browser=release --webgl-conformance-version=1.0.3 --extra-browser-args="--use-angle=gl" --total-shards=10 --shard-index=0 --write-full-results-to=webgl.json`

## Debug

* Download binary from http://wp-27.sh.intel.com/backup/windows/chrome-drop-webgl/
* cd out/release
* Start browser with `chrome.exe --use-angle=[angle-backend]`
* Start http server using python `python -mSimpleHTTPServer` (python2) or `python -mhttp.server` (python3)
* Browse to http://127.0.0.1:8000/third_party/webgl/src/sdk/tests/webgl-conformance-tests.html?version=[webgl-conformance-version]
* Find the test case. Taking "conformance_textures_image_bitmap_from_video_tex-2d-alpha-alpha-unsigned_byte.html" as example, you need to find category "all/conformance/textures/image_bitmap_from_video" first, then find the case "tex-2d-alpha-alpha-unsigned_byte.html" under it.
* Run the case by clicking the "run" button (running in place) or link (running in another tab)
* The result will show there


# ANGLE end2end tests
## Command

`angle_end2end_tests.exe --bot-mode`

Other useful arguments:<br>
--gtest_output=json:[result.json] is used to record result in json file. <br>
--gtest_filter is used to filter the cases to run against.<br>
--test-launcher-total-shards and --test-launcher-shard-index are used for shard execution.<br>

## Example

`angle_end2end_tests.exe --gtest_filter=DrawElementsTest* --gtest_output=json:angle.json` # Run tests starting from DrawElementsTest
`angle_end2end_tests.exe --gtest_filter=-DrawBuffersWebGL2*:DrawElementsTest` # Run tests other than DrawBuffersWebGL2* and DrawElementsTest*

## Debug

* Download binary from http://wp-27.sh.intel.com/backup/windows/chrome-drop-angle/
* cd out/release
* angle_end2end_tests.exe --gtest_filter=[filter]

# WebGPU CTS
## Command

python2 is used, and package pywin32 is required.<br>

`python third_party\blink\tools\run_web_tests.py --target=Release --no-show-results --clobber-old-results --no-retry-failures --additional-driver-flag=--enable-unsafe-webgpu --ignore-default-expectations --additional-expectations=third_party\blink\web_tests\WebGPUExpectations --isolated-script-test-filter=wpt_internal/webgpu/* --additional-driver-flag=--disable-gpu-sandbox --write-full-results-to=blink_webgpu.json`

Other useful arguments:<br>
--total-shards and --shard-index are used for shard execution.<br>

## Example
`python third_party\blink\tools\run_web_tests.py --target=Release --no-show-results --clobber-old-results --no-retry-failures --additional-driver-flag=--enable-unsafe-webgpu --ignore-default-expectations --additional-expectations=third_party\blink\web_tests\WebGPUExpectations --isolated-script-test-filter=wpt_internal/webgpu/* --additional-driver-flag=--disable-gpu-sandbox --write-full-results-to=blink_webgpu.json --total-shards=10 --shard-index=0`

## Debug
TBD

# Dawn end2end tests
## Command
`dawn_end2end_tests.exe --exclusive-device-type-preference=discrete,integrated`

Other useful arguments:<br>
--gtest_output=json:[result.json] is used to record result in json file. <br>
--gtest_filter is used to filter the cases to run against. <br>

## Example
`dawn_end2end_tests.exe --exclusive-device-type-preference=discrete,integrated --gtest_output=json:dawn.json`

## Debug
* Download binary from http://wp-27.sh.intel.com/backup/windows/chrome-drop-dawn/
* cd out/release
* dawn_end2end_tests.exe --exclusive-device-type-preference=discrete,integrated --gtest_filter=[filter]