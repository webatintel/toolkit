from util.base import *

class ExpectationHelper:
    EXPECTATION_FILES = {
        'trace_test': ['content/test/gpu/gpu_tests/test_expectations/trace_test_expectations.txt'],
        'webgpu_cts_tests': [
            'third_party/dawn/webgpu-cts/expectations.txt',
            'third_party/dawn/webgpu-cts/slow_tests.txt'
        ],
    }

    # These expected failures are not in expectation files, which will be maintained locally and appended to expectation files.
    LOCAL_EXPECTATIONS = {
        'third_party/dawn/webgpu-cts/expectations.txt': [
            'crbug.com/dawn/0000 [ intel win10 ] webgpu:shader,execution,expression,call,builtin,unpack4x8unorm:unpack:inputSource="storage_r" [ Failure ]',
            'crbug.com/dawn/0000 [ intel win10 ] webgpu:shader,execution,expression,call,builtin,unpack4x8unorm:unpack:inputSource="storage_rw" [ Failure ]',
            'crbug.com/dawn/0000 [ intel win10 ] webgpu:shader,execution,expression,call,builtin,unpack4x8unorm:unpack:inputSource="uniform" [ Failure ]'
        ],
    }

    @staticmethod
    def update_expectation(expectation_file, root_dir):
        file_path = f'{root_dir}/{expectation_file}'
        if not os.path.exists(file_path):
            Util.warning(f'{file_path} does not exist')
            return

        # Match intel tag in the gpu tags, such as '[ webgpu-adapter-default intel ]',
        # '[ intel-gen-9 win10 ]' and '[ intel-0x9bc5 ]'.
        intel_tag_pattern = re.compile(r'intel\S*')

        # Hold the lines with the 'intel' tag for duplication check.
        # Because there may be some expectations with same case, but different device ids,
        # after the update, there will be duplicate record, which is not allowed.
        intel_lines = []

        tag_header_scope = True
        update_comment = f'# LOCAL UPDATE FOR INTEL GPUS'
        has_update_comment = False
        for line in fileinput.input(file_path, inplace=True):
            # Skip if the expectation file has been updated.
            if has_update_comment:
                sys.stdout.write(line)
                continue

            if tag_header_scope:
                if re.search(update_comment, line):
                    has_update_comment = True
                elif re.search('BEGIN TAG HEADER', line):
                    line = f'{update_comment}\n' + line
                elif re.search('END TAG HEADER', line):
                    tag_header_scope = False
            else:
                if not line.startswith('#'):
                    # Get first matching tags, which may be gpu tags or may not.
                    gpu_tags = ''
                    gpu_tags_match = re.search(r'\[.*?\]', line)
                    if gpu_tags_match:
                        gpu_tags = gpu_tags_match.group()

                    if intel_tag_pattern.search(gpu_tags):
                        # Replace 'intel*' with 'intel' in the gpu tags
                        updated_gpu_tags = intel_tag_pattern.sub('intel', gpu_tags)

                        updated_line = line if updated_gpu_tags == gpu_tags else line.replace(gpu_tags, updated_gpu_tags)

                        # If the updated line already exists, just comment the line,
                        # otherwise comment the line and append the updated line.
                        # For the line already with 'intel' tag, keep as is if there is no duplicate line.
                        if updated_line in intel_lines:
                            line = '# ' + line
                        else:
                            if updated_gpu_tags != gpu_tags:
                                line =  '# ' + line + updated_line
                            intel_lines.append(updated_line)
            sys.stdout.write(line)
        fileinput.close()

        # Append local expectations
        if has_update_comment:
            return
        append_expectations = ExpectationHelper.LOCAL_EXPECTATIONS.get(expectation_file)
        if append_expectations is not None:
            expectations_str = ''
            for expectation in append_expectations:
                if expectation not in intel_lines:
                    expectations_str = expectations_str + f'{expectation}\n'
            if expectations_str != '':
                f = open(file_path, 'a')
                f.write('\n# Locally maintained expectation items\n')
                f.write(expectations_str)
                f.close()


    @staticmethod
    def update_target(target, root_dir):
        if not os.path.exists(root_dir):
            Util.warning(f'{root_dir} does not exist')
            return
        expectation_files = ExpectationHelper.EXPECTATION_FILES.get(target)
        if expectation_files is None:
            return
        for expectation_file in expectation_files:
            ExpectationHelper.update_expectation(expectation_file, root_dir)
