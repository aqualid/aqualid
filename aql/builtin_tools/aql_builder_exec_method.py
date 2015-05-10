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

from aql.nodes import Builder


# ==============================================================================

def _get_method_full_name(m):
    full_name = []
    mod = getattr(m, '__module__', None)
    if mod:
        full_name.append(mod)

    name = getattr(m, '__qualname__', None)
    if name:
        full_name.append(name)
    else:
        cls = getattr(m, 'im_class', None)
        if cls is not None:
            cls_name = getattr(cls, '__name__', None)
            if cls_name:
                full_name.append(cls_name)

        name = getattr(m, '__name__', None)
        if name:
            full_name.append(name)

    return '.'.join(full_name)

# ==============================================================================


class ExecuteMethodBuilder (Builder):

    NAME_ATTRS = ('method_name',)
    SIGNATURE_ATTRS = ('args', 'kw')

    def __init__(self,
                 options,
                 method,
                 args,
                 kw,
                 single,
                 make_files,
                 clear_targets):

        self.method_name = _get_method_full_name(method)
        self.method = method
        self.args = args if args else []
        self.kw = kw if kw else {}

        if not clear_targets:
            self.clear = lambda target_entities, side_effect_entities: None

        if single:
            self.split = self.split_single

        if make_files:
            self.make_entity = self.make_file_entity

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        return self.method(self, source_entities, targets,
                           *self.args, **self.kw)

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        name = self.method_name

        if not brief:
            args = ''
            if self.args:
                args = ','.join(self.args)

            if self.kw:
                if args:
                    args += ','
                args += ','.join("%s=%s" % (k, v) for k, v in self.kw.items())

            if args:
                return "%s(%s)" % (name, args)

        return name
