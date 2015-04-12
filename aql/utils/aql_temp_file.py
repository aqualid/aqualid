#
# Copyright (c) 2014-2015 The developers of Aqualid project
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
import tempfile
import errno
import shutil

__all__ = (
    'Tempfile', 'Tempdir',
)

# ==============================================================================


class Tempfile (str):

    def __new__(cls, prefix='tmp', suffix='', folder=None, mode='w+b'):
        handle = tempfile.NamedTemporaryFile(
            mode=mode, suffix=suffix, prefix=prefix, dir=folder, delete=False)

        self = super(Tempfile, cls).__new__(cls, handle.name)
        self.__handle = handle
        return self

    def __enter__(self):
        return self

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_value, traceback):
        self.remove()

    def write(self, data):
        self.__handle.write(data)

    def read(self, data):
        self.__handle.read(data)

    def seek(self, offset):
        self.__handle.seek(offset)

    def tell(self):
        return self.__handle.tell()

    def flush(self):
        if self.__handle is not None:
            self.__handle.flush()

    def close(self):
        if self.__handle is not None:
            self.__handle.close()
            self.__handle = None
        return self

    def remove(self):
        self.close()
        try:
            os.remove(self)
        except OSError as ex:
            if ex.errno != errno.ENOENT:
                raise

        return self

# ==============================================================================


class Tempdir(str):

    def __new__(cls, prefix='tmp', suffix='', folder=None, name=None):

        if folder is not None:
            if not os.path.isdir(folder):
                os.makedirs(folder)

        if name is None:
            path = tempfile.mkdtemp(prefix=prefix, suffix=suffix, dir=folder)
        else:
            if folder is not None:
                name = os.path.join(folder, name)

            path = os.path.abspath(name)

            if not os.path.isdir(path):
                os.makedirs(path)

        return super(Tempdir, cls).__new__(cls, path)

    def __enter__(self):
        return self

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type, exc_value, traceback):
        self.remove()

    def remove(self):
        shutil.rmtree(self, ignore_errors=False)
