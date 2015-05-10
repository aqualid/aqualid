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


import io
import os
import tarfile

from aql.util_types import is_unicode, encode_str
from aql.entity import FileEntityBase
from aql.nodes import FileBuilder

# ==============================================================================

class TarFilesBuilder (FileBuilder):

    NAME_ATTRS = ['target']
    SIGNATURE_ATTRS = ['rename', 'basedir']

    def __init__(self, options, target, mode, rename, basedir, ext):

        if not mode:
            mode = "w:bz2"

        if not ext:
            if mode == "w:bz2":
                ext = ".tar.bz2"
            elif mode == "w:gz":
                ext = ".tar.gz"
            elif mode == "w":
                ext = ".tar"

        self.target = self.get_target_path(target, ext)
        self.mode = mode
        self.rename = rename if rename else tuple()
        self.basedir = os.path.normcase(
            os.path.normpath(basedir)) if basedir else None

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

    def __add_file(self, arch, filepath):
        arcname = self.__get_arcname(filepath)
        arch.add(filepath, arcname)

    # -----------------------------------------------------------

    @staticmethod
    def __add_entity(arch, entity):
        arcname = entity.name
        data = entity.get()
        if is_unicode(data):
            data = encode_str(data)

        tinfo = tarfile.TarInfo(arcname)
        tinfo.size = len(data)
        arch.addfile(tinfo, io.BytesIO(data))

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        target = self.target

        arch = tarfile.open(name=self.target, mode=self.mode)
        try:
            for entity in source_entities:
                if isinstance(entity, FileEntityBase):
                    self.__add_file(arch, entity.get())
                else:
                    self.__add_entity(arch, entity)

        finally:
            arch.close()

        targets.add(target)

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return "Create Tar"

    # -----------------------------------------------------------

    def get_target_entities(self, source_entities):
        return self.target

