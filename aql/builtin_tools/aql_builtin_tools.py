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


from .aql_tool import Tool
from .aql_builder_exec_cmd import ExecuteCommandBuilder
from .aql_builder_copy_files import CopyFilesBuilder, CopyFileAsBuilder
from .aql_builder_find_files import FindFilesBuilder
from .aql_builder_exec_method import ExecuteMethodBuilder
from .aql_builder_tar import TarFilesBuilder
from .aql_builder_write_file import WriteFileBuilder
from .aql_builder_zip import ZipFilesBuilder
from .aql_builder_dist import DistBuilder
from .aql_builder_install import InstallDistBuilder


__all__ = (
    "BuiltinTool",
    'ExecuteCommandBuilder',
    'CopyFilesBuilder',
    'CopyFileAsBuilder',
    'FindFilesBuilder',
    'ExecuteMethodBuilder',
    'TarFilesBuilder',
    'WriteFileBuilder',
    'ZipFilesBuilder',
    'DistBuilder',
)

# ==============================================================================


class BuiltinTool(Tool):

    def execute_command(self, options,
                        target=None, target_flag=None, cwd=None):

        return ExecuteCommandBuilder(options, target=target,
                                     target_flag=target_flag, cwd=cwd)

    ExecuteCommand = execute_command
    Command = ExecuteCommand

    # ----------------------------------------------------------

    def execute_method(self, options,
                       method, args=None, kw=None, single=True,
                       make_files=True, clear_targets=True):

        return ExecuteMethodBuilder(options, method=method, args=args, kw=kw,
                                    single=single, make_files=make_files,
                                    clear_targets=clear_targets)

    ExecuteMethod = execute_method
    Method = ExecuteMethod

    # ----------------------------------------------------------

    def find_files(self, options, mask=None,
                   exclude_mask=None, exclude_subdir_mask=None):
        return FindFilesBuilder(options,
                                mask,
                                exclude_mask,
                                exclude_subdir_mask)

    FindFiles = find_files

    # ----------------------------------------------------------

    def copy_files(self, options, target, basedir=None):
        return CopyFilesBuilder(options, target, basedir=basedir)

    CopyFiles = copy_files

    # ----------------------------------------------------------

    def copy_file_as(self, options, target):
        return CopyFileAsBuilder(options, target)

    CopyFileAs = copy_file_as

    # ----------------------------------------------------------

    def write_file(self, options, target, binary=False, encoding=None):
        return WriteFileBuilder(options, target,
                                binary=binary, encoding=encoding)

    WriteFile = write_file

    # ----------------------------------------------------------

    def create_dist(self, options, target, command, args=None):
        return DistBuilder(options, target=target, command=command, args=args)

    CreateDist = create_dist

    # ----------------------------------------------------------

    def install_dist(self, options, user=True):
        return InstallDistBuilder(options, user=user)

    InstallDist = install_dist

    # ----------------------------------------------------------

    def create_zip(self, options, target, rename=None, basedir=None, ext=None):
        return ZipFilesBuilder(options, target=target, rename=rename,
                               basedir=basedir, ext=ext)

    CreateZip = create_zip

    # ----------------------------------------------------------

    def create_tar(self, options,
                   target, mode=None, rename=None, basedir=None, ext=None):

        return TarFilesBuilder(options, target=target, mode=mode,
                               rename=rename, basedir=basedir, ext=ext)

    CreateTar = create_tar
