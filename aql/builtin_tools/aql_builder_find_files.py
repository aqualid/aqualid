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


from aql.utils import find_files
from aql.nodes import FileBuilder


# ==============================================================================
class FindFilesBuilder (FileBuilder):

    NAME_ATTRS = ['mask']
    SIGNATURE_ATTRS = ['exclude_mask', 'exclude_subdir_mask']

    def __init__(self, options, mask,
                 exclude_mask=None,
                 exclude_subdir_mask=None):

        self.mask = mask
        self.exclude_mask = exclude_mask
        self.exclude_subdir_mask = exclude_subdir_mask

    # ----------------------------------------------------------

    def build(self, source_entities, targets):

        paths = [src.get() for src in source_entities]

        args = {'paths': paths}
        if self.mask is not None:
            args['mask'] = self.mask

        if self.exclude_mask is not None:
            args['exclude_mask'] = self.exclude_mask

        if self.exclude_subdir_mask is not None:
            args['exclude_subdir_mask'] = self.exclude_subdir_mask

        files = find_files(**args)

        targets.add_target_files(files)

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        trace = "Find files"
        if self.mask:
            trace += "(%s)" % self.mask

        return trace

    # ----------------------------------------------------------

    def clear(self, target_entities, side_effect_entities):
        pass
