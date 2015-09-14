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


import itertools

from aql.util_types import to_sequence
from aql.nodes import Builder


# ==============================================================================
class ExecuteCommandBuilder (Builder):

    NAME_ATTRS = ('targets', 'cwd')

    def __init__(self, options, target=None, target_flag=None, cwd=None):

        self.targets = tuple(map(self.get_target_path, to_sequence(target)))

        self.target_flag = target_flag

        if cwd:
            cwd = self.get_target_dir(cwd)

        self.cwd = cwd

    # -----------------------------------------------------------

    def _get_cmd_targets(self):

        targets = self.targets

        prefix = self.target_flag
        if not prefix:
            return tuple(targets)

        prefix = prefix.lstrip()

        if not prefix:
            return tuple(targets)

        rprefix = prefix.rstrip()

        if prefix != rprefix:
            return tuple(itertools.chain(*((rprefix, target)
                                           for target in targets)))

        return tuple("%s%s" % (prefix, target) for target in targets)

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        cmd = tuple(src.get() for src in source_entities)

        cmd_targets = self._get_cmd_targets()
        if cmd_targets:
            cmd += cmd_targets

        out = self.exec_cmd(cmd, cwd=self.cwd)

        targets.add_target_files(self.targets)

        return out

    # -----------------------------------------------------------

    def get_target_entities(self, source_entities):
        return self.targets

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        try:
            return source_entities[0]
        except Exception:
            return self.__class__.__name__

    # -----------------------------------------------------------

    def get_trace_sources(self, source_entities, brief):
        return source_entities[1:]
