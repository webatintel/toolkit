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

class Repo():
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

    def __init__(self, src_dir, program):
        self.src_dir = src_dir
        self.info = [Repo.FAKE_REV, Repo.FAKE_REV, {}]
        self.program = program

    def get_working_dir_rev(self):
        cmd = 'git log --shortstat -1'
        return self._get_head_rev(cmd)

    def get_local_repo_rev(self):
        cmd = 'git log --shortstat -1 origin/master'
        return self._get_head_rev(cmd)

    def get_hash_from_rev(self, rev):
        if rev not in self.info[Repo.INFO_INDEX_REV_INFO]:
            self.get_info(rev)
        return self.info[Repo.INFO_INDEX_REV_INFO][rev][Repo.REV_INFO_INDEX_HASH]

    # get info of [min_rev, max_rev]
    def get_info(self, min_rev, max_rev=FAKE_REV):
        if max_rev == Repo.FAKE_REV:
            max_rev = min_rev

        if min_rev > max_rev:
            return

        info = self.info
        info_min_rev = info[Repo.INFO_INDEX_MIN_REV]
        info_max_rev = info[Repo.INFO_INDEX_MAX_REV]
        if info_min_rev <= min_rev and info_max_rev >= max_rev:
            return

        Util.chdir(self.src_dir)
        if info[Repo.INFO_INDEX_MIN_REV] == Repo.FAKE_REV:
            self._get_info(min_rev, max_rev)
            info[Repo.INFO_INDEX_MIN_REV] = min_rev
            info[Repo.INFO_INDEX_MAX_REV] = max_rev
        else:
            if min_rev < info_min_rev:
                self._get_info(min_rev, info_min_rev - 1)
                info[Repo.INFO_INDEX_MIN_REV] = min_rev
            if max_rev > info_max_rev:
                self._get_info(info_max_rev + 1, max_rev)
                info[Repo.INFO_INDEX_MAX_REV] = max_rev

    def _get_info(self, min_rev, max_rev):
        info = self.info
        head_rev = self.get_local_repo_rev()
        if max_rev > head_rev:
            Util.error('Revision %s is not ready' % max_rev)
        cmd = 'git log --shortstat origin/master~%s..origin/master~%s ' % (head_rev - min_rev + 1, head_rev - max_rev)
        result = self.program.execute(cmd, show_cmd=False, return_out=True)
        lines = result[1].split('\n')

        rev_info = info[Repo.INFO_INDEX_REV_INFO]
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
                    rev_info[tmp_rev][Repo.REV_INFO_INDEX_ROLL_REPO] = match.group(1)
                    rev_info[tmp_rev][Repo.REV_INFO_INDEX_ROLL_HASH] = match.group(3)
                    rev_info[tmp_rev][Repo.REV_INFO_INDEX_ROLL_COUNT] = int(match.group(4))

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
        Util.chdir(self.src_dir)
        result = self.program.execute(cmd, show_cmd=False, return_out=True)
        lines = result[1].split('\n')
        rev_info = {}
        self._parse_lines(lines, rev_info=rev_info)
        for key in rev_info:
            return key