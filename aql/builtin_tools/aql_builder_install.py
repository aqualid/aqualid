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
import sys

from aql.nodes import FileBuilder

# ==============================================================================


class InstallDistBuilder (FileBuilder):

    NAME_ATTRS = ('user',)

    def __init__(self, options, user):

        self.user = user

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return "distutils install"

    # -----------------------------------------------------------

    def build(self, source_entities, targets):

        script = source_entities[0].get()

        cmd = [sys.executable, script, "install"]
        if self.user:
            cmd.append("--user")

        script_dir = os.path.dirname(script)
        out = self.exec_cmd(cmd, script_dir)

        # TODO: Add parsing of setup.py output
        # "copying <filepath> -> <detination dir>"

        return out
