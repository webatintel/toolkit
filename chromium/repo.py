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

from util.common import * # pylint: disable=unused-wildcard-import

class Repo():
    REV_MAX = 9999999
    COMMIT_STR = 'commit (.*)'

    INFO_INDEX_REV_MIN = 0
    INFO_INDEX_REV_MAX = 1
    INFO_INDEX_COMMIT_INFO = 2
    INFO_INDEX_HASH_INFO = 3
    INFO_INDEX_ROLL_INFO = 4

    # commit_info = {rev: info}
    COMMIT_INFO_INDEX_HASH = 0
    COMMIT_INFO_INDEX_AUTHOR = 1
    COMMIT_INFO_INDEX_DATE = 2
    COMMIT_INFO_INDEX_SUBJECT = 3
    COMMIT_INFO_INDEX_INSERTION = 4
    COMMIT_INFO_INDEX_DELETION = 5
    COMMIT_INFO_INDEX_END = COMMIT_INFO_INDEX_DELETION  # last index

    # hash_info = {hash: info}
    HASH_INFO_INDEX_REV = 0

    # roll_info = {rev: info}
    ROLL_INFO_INDEX_REPO = 0
    ROLL_INFO_INDEX_HASH_BEGIN = 1
    ROLL_INFO_INDEX_HASH_END = 2
    ROLL_INFO_INDEX_COUNT = 3
    ROLL_INFO_INDEX_DIRECTION = 4

    def __init__(self, src_dir, program):
        self.src_dir = src_dir
        self.info = [0, 0, {}, {}, {}]
        self.program = program

    def get_head_rev(self):
        Util.chdir(self.src_dir)
        cmd = 'git log --shortstat -1 origin/master'
        result = self.program.execute(cmd, show_cmd=False, return_out=True)
        lines = result[1].split('\n')
        commit_info = {}
        self._parse_lines(lines, commit_info)
        for key in commit_info:
            return key

    def get_hash_from_rev(self, rev):
        info = self.info
        if rev not in info[Repo.INFO_INDEX_COMMIT_INFO]:
            self.get_info(rev)
        return info[Repo.INFO_INDEX_COMMIT_INFO][rev][Repo.COMMIT_INFO_INDEX_HASH]

    # get src_info of [rev_min, rev_max]
    def get_info(self, rev_min, rev_max=0):
        if rev_max == 0:
            rev_max = rev_min

        if rev_min > rev_max:
            return

        info = self.info
        Util.chdir(self.src_dir)
        info_rev_min = info[Repo.INFO_INDEX_REV_MIN]
        info_rev_max = info[Repo.INFO_INDEX_REV_MAX]
        if info[Repo.INFO_INDEX_REV_MIN] == 0:
            self._get_info(rev_min, rev_max)
        elif rev_min < info_rev_min:
            self._get_info(rev_min, info_rev_min - 1)
        elif rev_min > info_rev_max:
            self._get_info(info_rev_max + 1, rev_max)

    def _get_info(self, rev_min, rev_max):
        info = self.info
        head_rev = self.get_head_rev()
        if rev_max > head_rev:
            Util.error('Revision %s is not ready' % rev_max)
        cmd = 'git log --shortstat origin/master~%s..origin/master~%s ' % (head_rev - rev_min + 1, head_rev - rev_max)
        result = self.program.execute(cmd, show_cmd=False, return_out=True)
        lines = result[1].split('\n')

        commit_info = info[Repo.INFO_INDEX_COMMIT_INFO]
        hash_info = info[Repo.INFO_INDEX_HASH_INFO]
        roll_info = info[Repo.INFO_INDEX_ROLL_INFO]
        self._parse_lines(lines, commit_info, hash_info, roll_info)

    def _parse_lines(self, lines, commit_info={}, hash_info={}, roll_info={}):
        rev_min = Repo.REV_MAX
        rev_max = 0

        hash_tmp = ''
        author_tmp = ''
        date_tmp = ''
        subject_tmp = ''
        rev_tmp = 0
        insertion_tmp = -1
        deletion_tmp = -1
        is_roll_tmp = False
        for index in range(0, len(lines)):
            line = lines[index]
            if re.match(self.COMMIT_STR, line):
                hash_tmp = ''
                author_tmp = ''
                date_tmp = ''
                subject_tmp = ''
                rev_tmp = 0
                insertion_tmp = -1
                deletion_tmp = -1
                is_roll_tmp = False
            (hash_tmp, author_tmp, date_tmp, subject_tmp, rev_tmp, insertion_tmp, deletion_tmp, is_roll_tmp) = self._parse_line(lines, index, hash_tmp, author_tmp, date_tmp, subject_tmp, rev_tmp, insertion_tmp, deletion_tmp, is_roll_tmp)
            if deletion_tmp >= 0:
                commit_info[rev_tmp] = [hash_tmp, author_tmp, date_tmp, subject_tmp]
                hash_info[hash_tmp] = [rev_tmp, 'chromium', 0, 0]
                if is_roll_tmp:
                    match = re.match(r'Roll (.*) ([a-zA-Z0-9]+)..([a-zA-Z0-9]+) \((\d+) commits\)', subject_tmp)
                    roll_info[rev_tmp] = [match.group(1), match.group(2), match.group(3), int(match.group(4))]

                if rev_tmp < rev_min:
                    rev_min = rev_tmp
                if rev_tmp > rev_max:
                    rev_max = rev_tmp

        # not all rev is existed. e.g., 129386
        for rev_tmp in range(rev_min, rev_max + 1):
            if rev_tmp not in commit_info:
                commit_info[rev_tmp] = [''] * (Repo.COMMIT_INFO_INDEX_END + 1)

    def _parse_line(self, lines, index, hash_tmp, author_tmp, date_tmp, subject_tmp, rev_tmp, insertion_tmp, deletion_tmp, is_roll_tmp):
        line = lines[index]
        strip_line = line.strip()
        # hash
        match = re.match(self.COMMIT_STR, line)
        if match:
            hash_tmp = match.group(1)

        # author
        match = re.match('Author:', lines[index])
        if match:
            match = re.search('<(.*@.*)@.*>', line)
            if match:
                author_tmp = match.group(1)
            else:
                match = re.search(r'(\S+@\S+)', line)
                if match:
                    author_tmp = match.group(1)
                    author_tmp = author_tmp.lstrip('<')
                    author_tmp = author_tmp.rstrip('>')
                else:
                    author_tmp = line.rstrip('\n').replace('Author:', '').strip()
                    Util.warning('The author %s is in abnormal format' % author_tmp)

        # date & subject
        match = re.match('Date:(.*)', line)
        if match:
            date_tmp = match.group(1).strip()
            index += 2
            subject_tmp = lines[index].strip()
            match = re.match('Roll.*', subject_tmp)
            if match:
                is_roll_tmp = True

        # rev
        # < r291561, use below format
        # example: git-svn-id: svn://svn.chromium.org/chrome/trunk/src@291560 0039d316-1c4b-4281-b951-d872f2087c98
        match = re.match('git-svn-id: svn://svn.chromium.org/chrome/trunk/src@(.*) .*', strip_line)
        if match:
            rev_tmp = int(match.group(1))

        # >= r291561, use below format
        # example: Cr-Commit-Position: refs/heads/master@{#349370}
        match = re.match('Cr-Commit-Position: refs/heads/master@{#(.*)}', strip_line)
        if match:
            rev_tmp = int(match.group(1))

        if re.match(r'(\d+) files? changed', strip_line):
            match = re.search(r'(\d+) insertion(s)*\(\+\)', strip_line)
            if match:
                insertion_tmp = int(match.group(1))
            else:
                insertion_tmp = 0

            match = re.search(r'(\d+) deletion(s)*\(-\)', strip_line)
            if match:
                deletion_tmp = int(match.group(1))
            else:
                deletion_tmp = 0

        return (hash_tmp, author_tmp, date_tmp, subject_tmp, rev_tmp, insertion_tmp, deletion_tmp, is_roll_tmp)