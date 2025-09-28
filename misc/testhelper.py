from util.base import *


class TestExpectation:
    EXPECTATION_FILES = {
        'angle_end2end_tests': ['src/tests/angle_end2end_tests_expectations.txt'],
        'info_collection_tests': ['content/test/gpu/gpu_tests/test_expectations/info_collection_expectations.txt'],
        'trace_test': ['content/test/gpu/gpu_tests/test_expectations/trace_test_expectations.txt'],
        'webgl_cts_tests': ['content/test/gpu/gpu_tests/test_expectations/webgl_conformance_expectations.txt'],
        'webgl2_cts_tests': ['content/test/gpu/gpu_tests/test_expectations/webgl2_conformance_expectations.txt'],
        'webgpu_cts_tests': [
            'third_party/dawn/webgpu-cts/expectations.txt',
            'third_party/dawn/webgpu-cts/slow_tests.txt',
        ],
    }

    # These expected failures are not in expectation files, which will be maintained locally and appended to expectation files or updated in test results.
    LOCAL_EXPECTATIONS = {
        'src/tests/angle_end2end_tests_expectations.txt': [
            'hsdes/18019513118 WIN INTEL D3D11 : SimpleStateChangeTest.DrawWithTextureTexSubImageThenDrawAgain/ES2_D3D11 = SKIP',
            'hsdes/18019513118 WIN INTEL D3D11 : SimpleStateChangeTest.UpdateTextureInUse/ES2_D3D11 = SKIP',
            # Windows RDP failures because Microsoft basic render is got.
            '0000 WIN D3D11 : EGLDisplaySelectionTestDeviceId.DeviceId/* = SKIP',
            '0000 WIN D3D11 : EGLDisplaySelectionTestDeviceId.DeviceIdConcurrently/* = SKIP',
            # Windows failures related to lock screen.
            '0000 WIN : GPUTestConfigTest.GPUTestConfigConditions_D3D11/ES2_D3D9 = SKIP',
            '0000 WIN : ProgramBinariesAcrossPlatforms.CreateAndReloadBinary/ES2_D3D11_to_ES2_D3D9 = SKIP',
            '0000 WIN : ProgramBinariesAcrossPlatforms.CreateAndReloadBinary/ES2_D3D9_to_ES2_D3D11 = SKIP',
            # Test regression
            '441612846 WIN : PixelLocalStorageTest.DrawCommandValidation/ES3_D3D11_DisableRasterizerOrderViews_EmulatePixelLocalStorage  = SKIP',
            '441612846 WIN : PixelLocalStorageTest.DrawCommandValidation/ES3_D3D11_EmulatePixelLocalStorage = SKIP',
        ],
        'content/test/gpu/gpu_tests/test_expectations/trace_test_expectations.txt': [
            # https://github.com/webatintel/webconformance/issues/24
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_MP4_FourColors_Rot_180 [ Failure ]',
            # Windows failures related to RDP or lock screen.
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Underlay [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Underlay_Fullsize [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_MP4 [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_MP4_BGRA [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_MP4_FourColors_Aspect_4x3 [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_MP4_FourColors_Rot_270 [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_MP4_FourColors_Rot_90 [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_MP4_Fullsize [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_MP4_NV12 [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_MP4_Rounded_Corner [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_MP4_VP_SCALING [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_MP4_YUY2 [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_SW_Decode [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_VP9 [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_VP9_BGRA [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_VP9_Fullsize [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_VP9_NV12 [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_VP9_VP_SCALING [ Failure ]',
            '[ win intel ] OverlayModeTraceTest_DirectComposition_Video_VP9_YUY2 [ Failure ]',
            '[ win intel ] VideoPathTraceTest_DirectComposition_Underlay [ Failure ]',
            '[ win intel ] VideoPathTraceTest_DirectComposition_Video_MP4 [ Failure ]',
            '[ win intel ] VideoPathTraceTest_DirectComposition_Video_MP4_FourColors_Aspect_4x3 [ Failure ]',
            '[ win intel ] VideoPathTraceTest_DirectComposition_Video_MP4_FourColors_Rot_180 [ Failure ]',
            '[ win intel ] VideoPathTraceTest_DirectComposition_Video_MP4_FourColors_Rot_270 [ Failure ]',
            '[ win intel ] VideoPathTraceTest_DirectComposition_Video_MP4_FourColors_Rot_90 [ Failure ]',
            '[ win intel ] VideoPathTraceTest_DirectComposition_Video_MP4_NV12 [ Failure ]',
            '[ win intel ] VideoPathTraceTest_DirectComposition_Video_MP4_Rounded_Corner [ Failure ]',
            '[ win intel ] VideoPathTraceTest_DirectComposition_Video_MP4_VP_SCALING [ Failure ]',
            '[ win intel ] VideoPathTraceTest_DirectComposition_Video_MP4_YUY2 [ Failure ]',
            '[ win intel ] VideoPathTraceTest_DirectComposition_Video_SW_Decode [ Failure ]',
            '[ win intel ] VideoPathTraceTest_DirectComposition_Video_VP9 [ Failure ]',
            '[ win intel ] VideoPathTraceTest_DirectComposition_Video_VP9_NV12 [ Failure ]',
            '[ win intel ] VideoPathTraceTest_DirectComposition_Video_VP9_VP_SCALING [ Failure ]',
            '[ win intel ] VideoPathTraceTest_DirectComposition_Video_VP9_YUY2 [ Failure ]',
        ],
        'content/test/gpu/gpu_tests/test_expectations/webgl2_conformance_expectations.txt': [
            # 'crbug.com/1131224 [ angle-d3d11 desktop no-asan oop-c passthrough release win11 intel ] conformance2/rendering/framebuffer-mismatched-attachment-targets.html [ Failure ]',
        ],
        'third_party/dawn/webgpu-cts/expectations.txt': [
            'crbug.com/1301808 [ intel ubuntu ] webgpu:web_platform,canvas,configure:viewFormats:canvasType="onscreen";format="rgba16float";* [ Failure ]',
            'crbug.com/1301808 [ intel ubuntu ] webgpu:web_platform,canvas,configure:viewFormats:canvasType="offscreen";format="rgba16float";* [ Failure ]',
            # Tracking at https://github.com/webatintel/webconformance/issues/26
            'crbug.com/0000 [ intel webgpu-adapter-default ] webgpu:web_platform,external_texture,video:importExternalTexture,compute:videoName="four-colors-h264-bt601-rotate-270.mp4";* [ Failure ]',
            'crbug.com/0000 [ intel webgpu-adapter-default ] webgpu:web_platform,external_texture,video:importExternalTexture,compute:videoName="four-colors-h264-bt601-rotate-90.mp4";* [ Failure ]',
            # disabled this due to conflict with a existing rule
            'crbug.com/0000 [ intel webgpu-adapter-default ] webgpu:web_platform,external_texture,video:importExternalTexture,sample:* [ Failure ]',
            'crbug.com/0000 [ intel webgpu-adapter-default ] webgpu:web_platform,external_texture,video:importExternalTexture,sampleWithVideoFrameWithVisibleRectParam:* [ Failure ]',
            # https://github.com/webatintel/webconformance/issues/27
            'crbug.com/0000 [ intel webgpu-adapter-default ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="stencil8" [ Failure ]',
            'crbug.com/0000 [ intel webgpu-adapter-default ] webgpu:api,operation,resource_init,texture_zero:uninitialized_texture_is_zero:dimension="2d";readMethod="CopyToTexture";format="stencil8" [ Failure ]',
            # https://github.com/webatintel/webconformance/issues/28
            'crbug.com/0000 [ intel webgpu-adapter-default ] webgpu:api,operation,command_buffer,image_copy:rowsPerImage_and_bytesPerRow_depth_stencil:format="stencil8";* [ Failure ]',
            'crbug.com/0000 [ intel webgpu-adapter-default ] webgpu:api,operation,command_buffer,image_copy:offsets_and_sizes_copy_depth_stencil:format="stencil8";* [ Failure ]',
            'crbug.com/0000 [ intel webgpu-adapter-default ] webgpu:api,operation,resource_init,texture_zero:uninitialized_texture_is_zero:dimension="2d";readMethod="CopyToBuffer";format="stencil8" [ Failure ]',
            'crbug.com/0000 [ intel webgpu-adapter-default ] webgpu:api,operation,resource_init,texture_zero:uninitialized_texture_is_zero:dimension="2d";readMethod="StencilTest";format="stencil8" [ Failure ]',
            # https://github.com/webatintel/webconformance/issues/29
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,expression,binary,f16_remainder:* [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,expression,call,builtin,pow:f16:inputSource="const";vectorize=3 [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,expression,call,builtin,step:f16:inputSource="const";vectorize=4 [ Failure ]',
            # https://github.com/webatintel/webconformance/issues/30
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,expression,binary,i32_arithmetic:addition_vector_scalar_compound:inputSource="const";* [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,expression,binary,i32_arithmetic:multiplication_scalar_vector:inputSource="const";* [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,expression,binary,i32_arithmetic:subtraction_vector_scalar_compound:inputSource="const";* [ Failure ]',
            # https://github.com/webatintel/webconformance/issues/31
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_layout:write_layout:case="mat2x3f_size";aspace="workgroup" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_layout:write_layout:case="mat2x4f_size";aspace="workgroup" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_layout:write_layout:case="mat3x2f_size";aspace="workgroup" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_layout:write_layout:case="mat3x3f_size";aspace="workgroup" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_layout:write_layout:case="mat3x3h_size";aspace="workgroup" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_layout:write_layout:case="mat3x4f_size";aspace="workgroup" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_layout:write_layout:case="mat3x4h_align8";aspace="workgroup" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_layout:write_layout:case="mat3x4h_size";aspace="workgroup" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_layout:write_layout:case="mat4x2f_size";aspace="workgroup" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_layout:write_layout:case="mat4x3f_size";aspace="workgroup" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_layout:write_layout:case="mat4x3h_align8";aspace="workgroup" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_layout:write_layout:case="mat4x3h_size";aspace="workgroup" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_layout:write_layout:case="mat4x4f_size";aspace="workgroup" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_layout:write_layout:case="mat4x4h_align8";aspace="workgroup" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_layout:write_layout:case="mat4x4h_size";aspace="workgroup" [ Failure ]',
            # D3D12 debug layer bug (https://issues.chromium.org/issues/425560775)
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="CopyB2T";checkMethod="FullCopyT2B";format="bc1-rgba-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="CopyB2T";checkMethod="FullCopyT2B";format="bc1-rgba-unorm-srgb";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="CopyB2T";checkMethod="FullCopyT2B";format="bc2-rgba-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="CopyB2T";checkMethod="FullCopyT2B";format="bc2-rgba-unorm-srgb";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="CopyB2T";checkMethod="FullCopyT2B";format="bc3-rgba-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="CopyB2T";checkMethod="FullCopyT2B";format="bc3-rgba-unorm-srgb";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="CopyB2T";checkMethod="FullCopyT2B";format="bc4-r-snorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="CopyB2T";checkMethod="FullCopyT2B";format="bc4-r-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="CopyB2T";checkMethod="FullCopyT2B";format="bc5-rg-snorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="CopyB2T";checkMethod="FullCopyT2B";format="bc5-rg-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="CopyB2T";checkMethod="FullCopyT2B";format="bc6h-rgb-float";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="CopyB2T";checkMethod="FullCopyT2B";format="bc6h-rgb-ufloat";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="CopyB2T";checkMethod="FullCopyT2B";format="bc7-rgba-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="CopyB2T";checkMethod="FullCopyT2B";format="bc7-rgba-unorm-srgb";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="FullCopyT2B";format="bc1-rgba-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="FullCopyT2B";format="bc1-rgba-unorm-srgb";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="FullCopyT2B";format="bc2-rgba-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="FullCopyT2B";format="bc2-rgba-unorm-srgb";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="FullCopyT2B";format="bc3-rgba-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="FullCopyT2B";format="bc3-rgba-unorm-srgb";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="FullCopyT2B";format="bc4-r-snorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="FullCopyT2B";format="bc4-r-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="FullCopyT2B";format="bc5-rg-snorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="FullCopyT2B";format="bc5-rg-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="FullCopyT2B";format="bc6h-rgb-float";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="FullCopyT2B";format="bc6h-rgb-ufloat";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="FullCopyT2B";format="bc7-rgba-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="FullCopyT2B";format="bc7-rgba-unorm-srgb";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="PartialCopyT2B";format="bc1-rgba-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="PartialCopyT2B";format="bc1-rgba-unorm-srgb";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="PartialCopyT2B";format="bc2-rgba-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="PartialCopyT2B";format="bc2-rgba-unorm-srgb";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="PartialCopyT2B";format="bc3-rgba-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="PartialCopyT2B";format="bc3-rgba-unorm-srgb";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="PartialCopyT2B";format="bc4-r-snorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="PartialCopyT2B";format="bc4-r-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="PartialCopyT2B";format="bc5-rg-snorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="PartialCopyT2B";format="bc5-rg-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="PartialCopyT2B";format="bc6h-rgb-float";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="PartialCopyT2B";format="bc6h-rgb-ufloat";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="PartialCopyT2B";format="bc7-rgba-unorm";dimension="3d" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:api,operation,command_buffer,image_copy:mip_levels:initMethod="WriteTexture";checkMethod="PartialCopyT2B";format="bc7-rgba-unorm-srgb";dimension="3d" [ Failure ]',
            # BMG: https://hsdes.intel.com/appstore/article-one/#/article/18038845701
            'crbug.com/0000 [ intel-0xe20b win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth24plus-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0xe20b win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth32float-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0xe20b win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0xe20b win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:arrayed_2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0xe20b win ] webgpu:shader,execution,memory_model,weak:2_plus_2_write:memType="atomic_workgroup" [ Failure ]',
            'crbug.com/0000 [ intel-0xe20b win ] webgpu:shader,execution,memory_model,weak:load_buffer:memType="atomic_workgroup" [ Failure ]',
            'crbug.com/0000 [ intel-0xe20b win ] webgpu:shader,execution,memory_model,weak:read:memType="atomic_workgroup" [ Failure ]',

            'crbug.com/0000 [ intel-0xe20c win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth24plus-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0xe20c win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth32float-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0xe20c win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0xe20c win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:arrayed_2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0xe20c win ] webgpu:shader,execution,memory_model,weak:2_plus_2_write:memType="atomic_workgroup" [ Failure ]',
            'crbug.com/0000 [ intel-0xe20c win ] webgpu:shader,execution,memory_model,weak:load_buffer:memType="atomic_workgroup" [ Failure ]',
            'crbug.com/0000 [ intel-0xe20c win ] webgpu:shader,execution,memory_model,weak:read:memType="atomic_workgroup" [ Failure ]',

            'crbug.com/0000 [ intel-0xe221 win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth24plus-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0xe221 win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth32float-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0xe221 win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0xe221 win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:arrayed_2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0xe221 win ] webgpu:shader,execution,memory_model,weak:2_plus_2_write:memType="atomic_workgroup" [ Failure ]',
            'crbug.com/0000 [ intel-0xe221 win ] webgpu:shader,execution,memory_model,weak:load_buffer:memType="atomic_workgroup" [ Failure ]',
            'crbug.com/0000 [ intel-0xe221 win ] webgpu:shader,execution,memory_model,weak:read:memType="atomic_workgroup" [ Failure ]',

            # LNL: https://hsdes.intel.com/appstore/article-one/#/article/18038845701
            'crbug.com/0000 [ intel-0x64a0 win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth24plus-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0x64a0 win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth32float-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0x64a0 win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0x64a0 win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:arrayed_2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0x64a0 win ] webgpu:shader,execution,memory_model,weak:2_plus_2_write:memType="atomic_workgroup" [ Failure ]',
            'crbug.com/0000 [ intel-0x64a0 win ] webgpu:shader,execution,memory_model,weak:load_buffer:memType="atomic_workgroup" [ Failure ]',
            'crbug.com/0000 [ intel-0x64a0 win ] webgpu:shader,execution,memory_model,weak:read:memType="atomic_workgroup" [ Failure ]',

            # PTL: https://hsdes.intel.com/appstore/article-one/#/article/18038845701
            'crbug.com/0000 [ intel-0xb0b0 win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth24plus-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0xb0b0 win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth32float-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0xb0b0 win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0xb0b0 win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:arrayed_2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0xb0b0 win ] webgpu:shader,execution,memory_model,weak:load_buffer:memType="atomic_workgroup" [ Failure ]',
            'crbug.com/0000 [ intel-0xb0b0 win ] webgpu:shader,execution,memory_model,weak:read:memType="atomic_workgroup" [ Failure ]',

            'crbug.com/0000 [ intel-0xb082 win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth24plus-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0xb082 win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth32float-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0xb082 win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0xb082 win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:arrayed_2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0xb082 win ] webgpu:shader,execution,memory_model,weak:2_plus_2_write:memType="atomic_workgroup" [ Failure ]',
            'crbug.com/0000 [ intel-0xb082 win ] webgpu:shader,execution,memory_model,weak:load_buffer:memType="atomic_workgroup" [ Failure ]',
            'crbug.com/0000 [ intel-0xb082 win ] webgpu:shader,execution,memory_model,weak:read:memType="atomic_workgroup" [ Failure ]',

            'crbug.com/0000 [ intel-0xb083 win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth24plus-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0xb083 win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth32float-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0xb083 win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0xb083 win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:arrayed_2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0xb083 win ] webgpu:shader,execution,memory_model,weak:2_plus_2_write:memType="atomic_workgroup" [ Failure ]',
            'crbug.com/0000 [ intel-0xb083 win ] webgpu:shader,execution,memory_model,weak:load_buffer:memType="atomic_workgroup" [ Failure ]',
            'crbug.com/0000 [ intel-0xb083 win ] webgpu:shader,execution,memory_model,weak:read:memType="atomic_workgroup" [ Failure ]',

            'crbug.com/0000 [ intel-0xb08f win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth24plus-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0xb08f win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth32float-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0xb08f win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0xb08f win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:arrayed_2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0xb08f win ] webgpu:shader,execution,memory_model,weak:2_plus_2_write:memType="atomic_workgroup" [ Failure ]',
            'crbug.com/0000 [ intel-0xb08f win ] webgpu:shader,execution,memory_model,weak:load_buffer:memType="atomic_workgroup" [ Failure ]',
            'crbug.com/0000 [ intel-0xb08f win ] webgpu:shader,execution,memory_model,weak:read:memType="atomic_workgroup" [ Failure ]',

            # WCL: https://hsdes.intel.com/appstore/article-one/#/article/18038845701
            'crbug.com/0000 [ intel-0xfd80 win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth24plus-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0xfd80 win ] webgpu:api,operation,command_buffer,copyTextureToTexture:copy_depth_stencil:format="depth32float-stencil8" [ Failure ]',
            'crbug.com/0000 [ intel-0xfd80 win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0xfd80 win ] webgpu:shader,execution,expression,call,builtin,textureSampleCompare:arrayed_2d_coords:* [ Failure ]',
            'crbug.com/0000 [ intel-0xfd80 win ] webgpu:shader,execution,memory_model,weak:load_buffer:memType="atomic_workgroup" [ Failure ]',
            'crbug.com/0000 [ intel-0xfd80 win ] webgpu:shader,execution,memory_model,weak:read:memType="atomic_workgroup" [ Failure ]',
            # Untriaged failures
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_model,barrier:workgroup_barrier_load_store:* [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_model,barrier:workgroup_barrier_load_store:accessValueType="f16";memType="non_atomic_storage";accessPair="rw" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_model,barrier:workgroup_barrier_load_store:accessValueType="u32";memType="non_atomic_storage";accessPair="rw" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_model,barrier:workgroup_barrier_store_load:accessValueType="f16";memType="non_atomic_storage";accessPair="wr" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,memory_model,barrier:workgroup_barrier_store_load:accessValueType="u32";memType="non_atomic_storage";accessPair="wr" [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,shader_io,fragment_builtins:inputs,front_facing:* [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,shader_io,fragment_builtins:inputs,interStage,centroid:* [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,shader_io,fragment_builtins:inputs,sample_mask:* [ Failure ]',
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,zero_init:compute,zero_init:addressSpace="private";* [ Failure ]',
            # Chrome drop flaky on ARL
            'crbug.com/0000 [ intel win ] webgpu:shader,execution,expression,unary,u32_conversion:f16:inputSource="const";vectorize=2 [ Failure ]',
        ],
        # There is no expectation file for dawn_end2end_tests. The expectations will be used to suppress the dawn e2e failures in test report.
        # Example: '[ Util.HOST_OS ] ComputeStorageBufferBarrierTests.UniformToStorageAddPingPong/D3D11_Intel_R_Arc_TM_A770_Graphics'
        'dawn_end2end_tests': [],
        'angle_white_box_tests': [
            # Windows failures related to RDP or lock screen.
            '[ win32 ] D3DTextureClearTest.ClearBGRA8/ES2_D3D9',
            '[ win32 ] D3DTextureClearTest.ClearR16/ES2_D3D9',
            '[ win32 ] D3DTextureClearTest.ClearR8/ES2_D3D9',
            '[ win32 ] D3DTextureClearTest.ClearRG16/ES2_D3D9',
            '[ win32 ] D3DTextureClearTest.ClearRG8/ES2_D3D9',
            '[ win32 ] D3DTextureClearTest.ClearRGB10A2/ES2_D3D9',
            '[ win32 ] D3DTextureClearTest.ClearRGBA8/ES2_D3D9',
            '[ win32 ] D3DTextureClearTest.ClearRGBAF16/ES2_D3D9',
            '[ win32 ] D3DTextureTest.BindTexImage/ES2_D3D9',
            '[ win32 ] D3DTextureTest.CheckSampleMismatch/ES2_D3D9',
            '[ win32 ] D3DTextureTest.Clear/ES2_D3D9',
            '[ win32 ] D3DTextureTest.DepthStencil/ES2_D3D9',
            '[ win32 ] D3DTextureTest.GlColorspaceNotAllowedForTypedD3DTexture/ES2_D3D9',
            '[ win32 ] D3DTextureTest.NonReadablePBuffer/ES2_D3D9',
            '[ win32 ] D3DTextureTest.NonRenderableTextureImage/ES2_D3D9',
            '[ win32 ] D3DTextureTest.RGBEmulationTextureImage/ES2_D3D9',
            '[ win32 ] D3DTextureTest.TestD3D11SupportedFormatsSurface/ES2_D3D9',
            '[ win32 ] D3DTextureTest.TestD3D11SupportedFormatsTexture/ES2_D3D9',
            '[ win32 ] D3DTextureTest.TestD3D11TypelessTexture/ES2_D3D9',
            '[ win32 ] D3DTextureTest.TextureArray/ES2_D3D9',
            '[ win32 ] D3DTextureTest.TypelessD3DTextureNotSupported/ES2_D3D9',
            '[ win32 ] D3DTextureTest.UnnecessaryWidthHeightAttributes/ES2_D3D9',
            '[ win32 ] D3DTextureYUVTest.NV12TextureImageReadPixel/ES2_D3D9',
            '[ win32 ] D3DTextureYUVTest.NV12TextureImageRender/ES2_D3D9',
            '[ win32 ] D3DTextureYUVTest.NV12TextureImageSampler/ES2_D3D9',
            '[ win32 ] D3DTextureYUVTest.P010TextureImageReadPixel/ES2_D3D9',
            '[ win32 ] D3DTextureYUVTest.P010TextureImageRender/ES2_D3D9',
            '[ win32 ] D3DTextureYUVTest.P010TextureImageSampler/ES2_D3D9',
            '[ win32 ] D3DTextureYUVTest.P016TextureImageReadPixel/ES2_D3D9',
            '[ win32 ] D3DTextureYUVTest.P016TextureImageRender/ES2_D3D9',
            '[ win32 ] D3DTextureYUVTest.P016TextureImageSampler/ES2_D3D9',
            '[ win32 ] EGLDirectCompositionTest.RenderSolidColor/ES2_D3D11_NoFixture',
            '[ win32 ] ErrorMessagesTest.ErrorMessages/ES2_D3D9',
        ],
    }

    # Match intel* tags, such as intel, intel-gen-9 and intel-0x9bc5.
    intel_pattern = re.compile(r'intel\S*')


    @staticmethod
    def _update_gpu_tag(line):
        # Ignore commented lines
        if line.startswith('#'):
            return line

        # Search the tags field we need to update
        match = re.search(r' (\[ .+? \]) ', line)
        if not match:
            return line

        tags = match.group(1)
        new_tags = tags

        # Replace 'win10' with 'win'
        new_tags = new_tags.replace('win10', 'win')
        # Replace 'ubuntu' with 'linux'
        new_tags = new_tags.replace('ubuntu', 'linux')
        # Replace 'intel*' with 'intel'
        if TestExpectation.intel_pattern.search(new_tags):
            new_tags = TestExpectation.intel_pattern.sub('intel', new_tags)

        # No updates in the tags
        if new_tags == tags:
            return line

        # Comment the line and append the updated line
        new_line = '# ' + line + line.replace(tags, new_tags)

        return new_line

    @staticmethod
    def update_target(target):
        if target in ['webgl2_conformance_d3d11_passthrough_tests', 'webgl2_conformance_gl_passthrough_tests']:
            return 'webgl2_cts_tests'
        elif target in ['webgl_conformance_d3d11_passthrough_tests', 'webgl_conformance_gl_passthrough_tests']:
            return 'webgl_cts_tests'
        elif target in ['webgpu_cts_with_validation_tests']:
            return 'webgpu_cts_tests'
        else:
            return target

    @staticmethod
    def update(target, root_dir):
        # Update target alias
        target = TestExpectation.update_target(target)

        if not os.path.exists(root_dir):
            Util.warning(f'{root_dir} does not exist')
            return

        expectation_files = TestExpectation.EXPECTATION_FILES.get(target)
        if not expectation_files:
            return

        for expectation_file in expectation_files:
            file_path = f'{root_dir}/{expectation_file}'
            if not os.path.exists(file_path):
                Util.warning(f'{file_path} does not exist')
                return

            line_comment = '#'
            if target in ['angle_end2end_tests']:
                line_comment = '//'

            update_comment = f'{line_comment} LOCAL UPDATE FOR INTEL GPUS'
            conflicts_allowed_str = f'{line_comment} conflicts_allowed: true'
            has_update_comment = False
            tag_header_scope = True
            conflicts_allowed = False
            for line in fileinput.input(file_path, inplace=True):
                # Skip if the expectation file has been updated.
                if has_update_comment:
                    sys.stdout.write(line)
                    continue

                if fileinput.isfirstline():
                    if re.search(update_comment, line):
                        has_update_comment = True
                    else:
                        line = f'{update_comment}\n' + line

                if target in ['info_collection_tests', 'trace_test', 'webgl_cts_tests', 'webgl2_cts_tests', 'webgpu_cts_tests']:
                    if tag_header_scope and re.search('END TAG HEADER', line):
                        tag_header_scope = False
                    else:
                        if tag_header_scope and target == 'webgpu_cts_tests':
                            if line.find('intel-0x3e9b intel-0x4680 intel-0x46a8 intel-0x5912 intel-0x9bc5') != -1:
                                line += f'#             intel-0x64a0 intel-0xe221 intel-0xe20b intel-0xe20c intel-0xb0b0\n'
                                line += f'#             intel-0xb082 intel-0xb083 intel-0xb08f intel-0xfd80\n'
                        else:
                            if re.search(conflicts_allowed_str, line):
                                conflicts_allowed = True
                            line = TestExpectation._update_gpu_tag(line)
                sys.stdout.write(line)
            fileinput.close()

            # Append local expectations
            if has_update_comment:
                return
            append_expectations = TestExpectation.LOCAL_EXPECTATIONS.get(expectation_file)
            if not append_expectations and conflicts_allowed:
                return
            f = open(file_path, 'a')
            f.write(f'\n{line_comment} Locally maintained expectation items\n')
            if not conflicts_allowed:
                f.write(f'{conflicts_allowed_str}\n')
            if append_expectations:
                expectations_str = ''
                for expectation in append_expectations:
                    expectations_str += f'{expectation}\n'
                f.write(expectations_str)
            f.close()


class TestResult:
    def __init__(self, result_file=None, real_type=None):
        self.pass_fail = []
        self.fail_pass = []
        self.fail_fail = []
        self.pass_pass = []

        if not result_file or not real_type:
            return

        try:
            json_result = json.load(open(result_file))

            if real_type in ['gtest_angle', 'telemetry_gpu_integration_test', 'webgpu_blink_web_tests']:
                for key, val in json_result['tests'].items():
                    self._parse_result(key, val, key)

            elif real_type == 'gtest_chrome':
                for key, val in json_result['per_iteration_data'][0].items():
                    if val[0]['status'] == 'SUCCESS':
                        self.pass_pass.append(key)
                    elif val[0]['status'] == 'FAILURE':
                        self.pass_fail.append(key)

            elif real_type == 'angle':
                errors_count = json_result['errors']
                failures_count = json_result['failures']
                pass_fail_count = errors_count + failures_count
                total_count = json_result['tests']
                pass_pass_count = total_count - pass_fail_count
                self.pass_pass = [0] * pass_pass_count
                if pass_fail_count:
                    self.pass_fail.append('%s in %s' % (pass_fail_count, result_file))

            elif real_type == 'dawn':
                for test_suite in json_result['testsuites']:
                    suite_name = test_suite['name']
                    for test in test_suite['testsuite']:
                        test_name = '%s.%s' % (suite_name, test['name'])
                        if 'failures' in test:
                            self.pass_fail.append(test_name)
                        else:
                            self.pass_pass.append(test_name)
        except Exception as e:
            self.pass_fail.append('All in %s' % result_file)

    def _parse_result(self, key, val, path):
        def _is_pass(val):
            return str(val).endswith('PASS')

        if 'expected' in val and 'actual' in val:
            expected_pass = _is_pass(val['expected'])
            actual_pass = _is_pass(val['actual'])
            if not expected_pass and not actual_pass:
                self.fail_fail.append(path)
            elif not expected_pass and actual_pass:
                self.fail_pass.append(path)
            elif expected_pass and not actual_pass:
                self.pass_fail.append(path)
            elif expected_pass and actual_pass:
                self.pass_pass.append(path)
        else:
            for new_key, new_val in val.items():
                self._parse_result(new_key, new_val, '%s/%s' % (path, new_key))
