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

from aql.util_types import is_string, to_sequence
from aql.nodes import FileBuilder


# ==============================================================================


class ErrorDistCommandInvalid(Exception):

    def __init__(self, command):
        msg = "distutils command '%s' is not supported" % (command,)
        super(ErrorDistCommandInvalid, self).__init__(msg)

# ==============================================================================


class DistBuilder (FileBuilder):

    NAME_ATTRS = ('target', 'command', 'formats')
    SIGNATURE_ATTRS = ('script_args', )

    def __init__(self, options, command, args, target):

        target = self.get_target_dir(target)

        script_args = [command]

        if command.startswith('bdist'):
            temp_dir = self.get_build_path()
            script_args += ['--bdist-base', temp_dir]

        elif command != 'sdist':
            raise ErrorDistCommandInvalid(command)

        args = self._get_args(args)
        script_args += args

        formats = self._get_formats(args, command)

        script_args += ['--dist-dir', target]

        self.command = command
        self.target = target
        self.script_args = script_args
        self.formats = formats

    # -----------------------------------------------------------

    @staticmethod
    def _get_args(args):
        if args:
            return args.split() if is_string(args) else to_sequence(args)

        return tuple()

    # -----------------------------------------------------------

    @staticmethod
    def _get_formats(args, command):

        if not command.startswith('bdist'):
            return None

        formats = set()
        for arg in args:
            if arg.startswith('--formats='):
                v = arg[len('--formats='):].split(',')
                formats.update(v)

            elif arg.startswith('--plat-name='):
                v = arg[len('--plat-name='):]
                formats.add(v)

        return formats

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return "distutils %s" % ' '.join(self.script_args)

    # -----------------------------------------------------------

    def build(self, source_entities, targets):

        script = source_entities[0].get()

        cmd = [sys.executable, script]
        cmd += self.script_args

        script_dir = os.path.dirname(script)
        out = self.exec_cmd(cmd, script_dir)

        # TODO: Add parsing of setup.py output
        # "copying <filepath> -> <detination dir>"

        return out

