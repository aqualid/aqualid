#
# Copyright (c) 2015 The developers of Aqualid project
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
import zipfile

from aql.util_types import is_unicode, encode_str
from aql.entity import FileEntityBase
from aql.nodes import FileBuilder

# ==============================================================================


class ZipFilesBuilder (FileBuilder):

    NAME_ATTRS = ['target']
    SIGNATURE_ATTRS = ['rename', 'basedir']

    def __init__(self, options, target, rename=None, basedir=None, ext=None):

        if ext is None:
            ext = ".zip"

        self.target = self.get_target_path(target, ext=ext)
        self.rename = rename if rename else tuple()
        self.basedir = os.path.normcase(
            os.path.normpath(basedir)) if basedir else None

    # -----------------------------------------------------------

    def __open_arch(self, large=False):
        try:
            return zipfile.ZipFile(self.target,
                                   "w",
                                   zipfile.ZIP_DEFLATED,
                                   large)
        except RuntimeError:
            pass

        return zipfile.ZipFile(self.target, "w", zipfile.ZIP_STORED, large)

    # -----------------------------------------------------------

    def __get_arcname(self, file_path):
        for arc_name, path in self.rename:
            if file_path == path:
                return arc_name

        basedir = self.basedir
        if basedir:
            if file_path.startswith(basedir):
                return file_path[len(basedir):]

        return os.path.basename(file_path)

    # -----------------------------------------------------------

    def __add_files(self, arch, source_entities):
        for entity in source_entities:
            if isinstance(entity, FileEntityBase):
                filepath = entity.get()
                arcname = self.__get_arcname(filepath)
                arch.write(filepath, arcname)
            else:
                arcname = entity.name
                data = entity.get()
                if is_unicode(data):
                    data = encode_str(data)

                arch.writestr(arcname, data)

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        target = self.target

        arch = self.__open_arch()

        try:
            self.__add_files(arch, source_entities)
        except zipfile.LargeZipFile:
            arch.close()
            arch = None
            arch = self.__open_arch(large=True)

            self.__add_files(arch, source_entities)
        finally:
            if arch is not None:
                arch.close()

        targets.add_targets(target)

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return "Create Zip"

    # -----------------------------------------------------------

    def get_target_entities(self, source_entities):
        return self.target
