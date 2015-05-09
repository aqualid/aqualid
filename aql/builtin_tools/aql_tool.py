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


from aql.utils import find_program, find_programs,\
    find_optional_program, find_optional_programs

__all__ = ('Tool',)


class Tool(object):

    def __init__(self, options):
        pass

    # -----------------------------------------------------------

    @classmethod
    def setup(cls, options):
        pass

    # -----------------------------------------------------------

    @classmethod
    def options(cls):
        return None

    # -----------------------------------------------------------

    @classmethod
    def find_program(cls, options, prog, hint_prog=None):
        env = options.env.get()
        prog = find_program(prog, env, hint_prog)

        if prog is None:
            raise NotImplementedError()

        return prog

    # -----------------------------------------------------------

    @classmethod
    def find_programs(cls, options, progs, hint_prog=None):
        env = options.env.get()
        progs = find_programs(progs, env, hint_prog)

        for prog in progs:
            if prog is None:
                raise NotImplementedError()

        return progs

    # -----------------------------------------------------------

    @classmethod
    def find_optional_program(cls, options, prog, hint_prog=None):
        env = options.env.get()
        return find_optional_program(prog, env, hint_prog)

    # -----------------------------------------------------------

    @classmethod
    def find_optional_programs(cls, options, progs, hint_prog=None):
        env = options.env.get()
        return find_optional_programs(progs, env, hint_prog)
