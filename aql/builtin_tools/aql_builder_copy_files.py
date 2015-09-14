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
import shutil

from aql.nodes import FileBuilder

# ==============================================================================


class CopyFilesBuilder (FileBuilder):

    NAME_ATTRS = ['target']

    def __init__(self, options, target):
        self.target = self.get_target_dir(target)
        self.split = self.split_batch

    # -----------------------------------------------------------

    def build_batch(self, source_entities, targets):
        target = self.target

        for src_entity in source_entities:
            src = src_entity.get()

            dst = os.path.join(target, os.path.basename(src))
            shutil.copyfile(src, dst)
            shutil.copymode(src, dst)

            targets[src_entity].add_targets(dst)

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return "Copy files"

    # -----------------------------------------------------------

    def get_target_entities(self, source_entities):
        src = source_entities[0].get()
        return os.path.join(self.target, os.path.basename(src)),


# ==============================================================================

class CopyFileAsBuilder (FileBuilder):

    NAME_ATTRS = ['target']

    def __init__(self, options, target):
        self.target = self.get_target_path(target)

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        source = source_entities[0].get()
        target = self.target

        shutil.copyfile(source, target)
        shutil.copymode(source, target)

        targets.add_targets(target)

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return "Copy file"

    # -----------------------------------------------------------

    def get_target_entities(self, source_entities):
        return self.target
