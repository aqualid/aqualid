#
# Copyright (c) 2014-2015 The developers of Aqualid project
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
#  OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import os
import sys
import re
import fnmatch
import operator

from aql.util_types import is_string, to_sequence

from .aql_utils import ItemsGroups

__all__ = (
    'find_files', 'find_file_in_paths', 'abs_file_path', 'expand_file_path',
    'change_path', 'split_path',
    'find_program', 'find_programs', 'find_optional_program',
    'find_optional_programs',
    'relative_join', 'relative_join_list', 'exclude_files_from_dirs',
    'split_drive', 'group_paths_by_dir', 'Chdir',
)

# ==============================================================================


class ErrorNoPrograms(Exception):

    def __init__(self, prog):
        msg = "No programs were specified: %s(%s)" % (prog, type(prog))
        super(type(self), self).__init__(msg)

# ==============================================================================


def abs_file_path(file_path, path_sep=os.path.sep,
                  seps=(os.path.sep, os.path.altsep),
                  _abspath=os.path.abspath,
                  _normcase=os.path.normcase):
    if not file_path:
        file_path = '.'

    if file_path[-1] in seps:
        last_sep = path_sep
    else:
        last_sep = ''

    return _normcase(_abspath(file_path)) + last_sep

# ==============================================================================


def expand_file_path(path,
                     _normpath=os.path.normpath,
                     _expanduser=os.path.expanduser,
                     _expandvars=os.path.expandvars):

    return _normpath(_expanduser(_expandvars(path)))

# ==============================================================================


def exclude_files_from_dirs(files, dirs):
    result = []
    folders = tuple(os.path.normcase(
        os.path.abspath(folder)) + os.path.sep for folder in to_sequence(dirs))

    for file in to_sequence(files):
        file = os.path.normcase(os.path.abspath(file))
        if not file.startswith(folders):
            result.append(file)

    return result

# ==============================================================================


def _masks_to_match(masks, _null_match=lambda name: False):
    if not masks:
        return _null_match

    if is_string(masks):
        masks = masks.split('|')

    re_list = []
    for mask in to_sequence(masks):
        re_list.append(
            "(%s)" % fnmatch.translate(os.path.normcase(mask).strip()))

    re_str = '|'.join(re_list)

    return re.compile(re_str).match

# ==============================================================================


def find_files(paths=".",
               mask=("*", ),
               exclude_mask=tuple(),
               exclude_subdir_mask=('__*', '.*')):

    found_files = []

    paths = to_sequence(paths)

    match_mask = _masks_to_match(mask)
    match_exclude_mask = _masks_to_match(exclude_mask)
    match_exclude_subdir_mask = _masks_to_match(exclude_subdir_mask)

    for path in paths:
        for root, folders, files in os.walk(os.path.abspath(path)):
            for file_name in files:
                file_name_nocase = os.path.normcase(file_name)
                if (not match_exclude_mask(file_name_nocase)) and\
                   match_mask(file_name_nocase):

                    found_files.append(os.path.join(root, file_name))

            folders[:] = (folder for folder in folders
                          if not match_exclude_subdir_mask(folder))

    found_files.sort()
    return found_files

# ==============================================================================


def find_file_in_paths(paths, filename):

    for path in paths:
        file_path = os.path.join(path, filename)
        if os.access(file_path, os.R_OK):
            return os.path.normpath(file_path)

    return None

# ==============================================================================


def _get_env_path(env, hint_prog=None):

    paths = env.get('PATH', tuple())
    if is_string(paths):
        paths = paths.split(os.pathsep)

    paths = [os.path.expanduser(path) for path in paths]

    if hint_prog:
        hint_dir = os.path.dirname(hint_prog)
        paths.insert(0, hint_dir)

    return paths

# ==============================================================================


def _get_env_path_ext(env, hint_prog=None,
                      is_windows=(os.name == 'nt'),
                      is_cygwin=(sys.platform == 'cygwin')):

    if not is_windows and not is_cygwin:
        return tuple()

    if hint_prog:
        hint_ext = os.path.splitext(hint_prog)[1]
        return hint_ext,

    path_exts = env.get('PATHEXT', None)
    if path_exts is None:
        path_exts = os.environ.get('PATHEXT', None)

    if is_string(path_exts):
        path_sep = ';' if is_cygwin else os.pathsep
        path_exts = path_exts.split(path_sep)

    if not path_exts:
        path_exts = ['.exe', '.cmd', '.bat', '.com']

    if is_cygwin:
        if '' not in path_exts:
            path_exts = [''] + path_exts

    return path_exts

# ==============================================================================


def _add_program_exts(progs, exts):

    progs = to_sequence(progs)

    if not exts:
        return tuple(progs)

    result = []
    for prog in progs:
        prog_ext = os.path.splitext(prog)[1]

        if prog_ext or (prog_ext in exts):
            result.append(prog)
        else:
            result += (prog + ext for ext in exts)

    return result

# ==============================================================================


def _find_program(progs, paths):
    for path in paths:
        for prog in progs:
            prog_path = os.path.join(path, prog)
            if os.access(prog_path, os.X_OK):
                return os.path.normcase(prog_path)

    return None

# ==============================================================================


def find_program(prog, env, hint_prog=None):
    paths = _get_env_path(env, hint_prog)
    path_ext = _get_env_path_ext(env, hint_prog)

    progs = _add_program_exts(prog, path_ext)

    return _find_program(progs, paths)

# ==============================================================================


def find_programs(progs, env, hint_prog=None):
    paths = _get_env_path(env, hint_prog)
    path_ext = _get_env_path_ext(env, hint_prog)

    result = []
    for prog in progs:
        progs = _add_program_exts(prog, path_ext)
        prog = _find_program(progs, paths)
        result.append(prog)

    return result

# ==============================================================================


def find_optional_program(prog, env, hint_prog=None):
    paths = _get_env_path(env, hint_prog)
    path_ext = _get_env_path_ext(env, hint_prog)
    progs = _add_program_exts(prog, path_ext)

    return _OptionalProgramFinder(progs, paths)

# ==============================================================================


def find_optional_programs(progs, env, hint_prog=None):
    paths = _get_env_path(env, hint_prog)
    path_ext = _get_env_path_ext(env, hint_prog)

    result = []
    for prog in progs:
        progs = _add_program_exts(prog, path_ext)
        prog = _OptionalProgramFinder(progs, paths)
        result.append(prog)

    return result

# ==============================================================================


class _OptionalProgramFinder(object):
    __slots__ = (
        'progs',
        'paths',
        'result',
    )

    def __init__(self, progs, paths):
        if not progs:
            raise ErrorNoPrograms(progs)

        self.progs = progs
        self.paths = paths
        self.result = None

    def __nonzero__(self):
        return bool(self.get())

    def __bool__(self):
        return bool(self.get())

    def __call__(self):
        return self.get()

    def __str__(self):
        return self.get()

    def get(self):
        progpath = self.result
        if progpath:
            return progpath

        prog_full_path = _find_program(self.progs, self.paths)
        if prog_full_path is not None:
            self.result = prog_full_path
            return prog_full_path

        self.result = self.progs[0]
        return self.result

# ==========================================================


def _norm_local_path(path):

    if not path:
        return '.'

    path_sep = os.path.sep

    if path[-1] in (path_sep, os.path.altsep):
        last_sep = path_sep
    else:
        last_sep = ''

    path = os.path.normcase(os.path.normpath(path))

    return path + last_sep

# ==============================================================================

try:
    _splitunc = os.path.splitunc
except AttributeError:
    def _splitunc(path):
        return str(), path


def split_drive(path):
    drive, path = os.path.splitdrive(path)
    if not drive:
        drive, path = _splitunc(path)

    return drive, path

# ==============================================================================


def _split_path(path):
    drive, path = split_drive(path)

    path = path.split(os.path.sep)
    path.insert(0, drive)

    return path

# ==============================================================================


def split_path(path):
    path = os.path.normcase(os.path.normpath(path))
    path = _split_path(path)

    path = [p for p in path if p]
    return path

# ==============================================================================


def _common_prefix_size(*paths):
    min_path = min(paths)
    max_path = max(paths)

    i = 0
    for i, path in enumerate(min_path[:-1]):
        if path != max_path[i]:
            return i
    return i + 1

# ==============================================================================


def _relative_join(base_path, base_path_seq, path, sep=os.path.sep):

    path = _split_path(_norm_local_path(path))

    prefix_index = _common_prefix_size(base_path_seq, path)
    if prefix_index == 0:
        drive = path[0]
        if drive:
            drive = drive.replace(':', '').split(sep)
            del path[0]
            path[0:0] = drive
    else:
        path = path[prefix_index:]

    path.insert(0, base_path)
    path = filter(None, path)

    return sep.join(path)

# ==============================================================================


def relative_join_list(base_path, paths):
    base_path = _norm_local_path(base_path)
    base_path_seq = _split_path(base_path)
    return [_relative_join(base_path, base_path_seq, path)
            for path in to_sequence(paths)]

# ==============================================================================


def relative_join(base_path, path):
    base_path = _norm_local_path(base_path)
    base_path_seq = _split_path(base_path)
    return _relative_join(base_path, base_path_seq, path)

# ==============================================================================


def change_path(path, dirname=None, name=None, ext=None, prefix=None):

    path_dirname, path_filename = os.path.split(path)
    path_name, path_ext = os.path.splitext(path_filename)

    if dirname is None:
        dirname = path_dirname
    if name is None:
        name = path_name
    if ext is None:
        ext = path_ext
    if prefix:
        name = prefix + name

    path = dirname
    if path:
        path += os.path.sep

    return path + name + ext

# ==============================================================================


def _simple_path_getter(path):
    return path

# ==============================================================================


def group_paths_by_dir(file_paths,
                       wish_groups=1,
                       max_group_size=-1,
                       path_getter=None):

    groups = ItemsGroups(len(file_paths), wish_groups, max_group_size)

    if path_getter is None:
        path_getter = _simple_path_getter

    files = []
    for file_path in file_paths:
        path = path_getter(file_path)

        dir_path, file_name = os.path.split(path)
        dir_path = os.path.normcase(dir_path)

        files.append((dir_path, file_path))

    files.sort(key=operator.itemgetter(0))

    last_dir = None

    for dir_path, file_path in files:

        if last_dir != dir_path:
            last_dir = dir_path
            groups.add_group()

        groups.add(file_path)

    return groups.get()

# ==============================================================================


class Chdir (object):
    __slots__ = ('previous_path', )

    def __init__(self, path):
        self.previous_path = os.getcwd()

        os.chdir(path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.previous_path)
        return False
