#!/usr/bin/env python
#
# Copyright (C) 2017 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import argparse
import os
import re
import subprocess

from utils import android_path

PROJECT_PATH = (
    ('llvm', android_path('llvm')),
    ('cfe', android_path('llvm/tools/clang')),
    ('clang-tools-extra', android_path('llvm/tools/clang/tools/extra')),
    ('compiler-rt', android_path('llvm/projects/compiler-rt')),
    ('libcxx', android_path('llvm/projects/libcxx')),
    ('libcxxabi', android_path('llvm/projects/libcxxabi')),
    ('openmp', android_path('llvm/projects/openmp')),
)


def parse_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('revision', help='Revision number of llvm source.',
                      type=int)
  return parser.parse_args()


def merge_projects(revision):
    project_sha_dict = {}
    for (project, path) in PROJECT_PATH:
        sha = get_commit_hash(revision, path)
        if sha is None:
            return
        project_sha_dict[project] = sha
        print("Project %s git hash: %s" % (project, sha))

    for (project, path) in PROJECT_PATH:
        sha = project_sha_dict[project]
        subprocess.check_call(['git', 'merge', sha, '-m',
            'Merge %s for LLVM update to %d' % (sha, revision)], cwd=path)


def get_commit_hash(revision, path):
    # Get sha and commit message body for each log.
    p = subprocess.Popen('git log aosp/upstream-mirror --format="%h%x1f%B%x1e"',
                         shell=True, stdout=subprocess.PIPE, cwd=path)
    (log, _) = p.communicate()
    if p.returncode != 0:
        print('git log for path: %s failed!' % path)
        return

    # Log will be in reversed order.
    log = log.strip('\n\x1e').split('\x1e')

    # Binary search log data.
    low, high = 0, len(log) - 1
    while low < high:
        pos = (low + high) // 2
        (sha, cur_revision)  = parse_log(log[pos])
        if cur_revision == revision:
            return sha
        elif cur_revision < revision:
            high = pos
        else:
            low = pos + 1
    (sha, _) = parse_log(log[high])
    return sha


def parse_log(raw_log):
    log = raw_log.strip().split('\x1f')
    # Extract revision number from log data.
    revision_string = log[1].strip().split('\n')[-1]
    revision = int(re.search(r'trunk@(\d+)', revision_string).group(1))
    return (log[0], revision)


def main():
    args = parse_args()
    merge_projects(args.revision)


if __name__ == '__main__':
    main()