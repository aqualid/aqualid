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


from aql.util_types import is_unicode, encode_str, decode_bytes
from aql.utils import open_file
from aql.nodes import Builder

# ==============================================================================


class WriteFileBuilder (Builder):

    NAME_ATTRS = ['target']

    def __init__(self, options, target, binary=False, encoding=None):
        self.binary = binary
        self.encoding = encoding
        self.target = self.get_target_path(target)

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        target = self.target

        with open_file(target,
                       write=True,
                       binary=self.binary,
                       encoding=self.encoding) as f:
            f.truncate()
            for src in source_entities:
                src = src.get()
                if self.binary:
                    if is_unicode(src):
                        src = encode_str(src, self.encoding)
                else:
                    if isinstance(src, (bytearray, bytes)):
                        src = decode_bytes(src, self.encoding)

                f.write(src)

        targets.add_target_files(target)

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return "Writing content"

    # -----------------------------------------------------------

    def get_target_entities(self, source_entities):
        return self.target
