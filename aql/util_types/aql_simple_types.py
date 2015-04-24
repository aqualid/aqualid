#
# Copyright (c) 2011-2015 The developers of Aqualid project
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

import re
import sys
import locale
import operator

__all__ = (
    'u_str', 'to_unicode', 'is_unicode', 'is_string', 'to_string',
    'cast_str', 'encode_str', 'decode_bytes', 'String', 'IgnoreCaseString',
    'LowerCaseString', 'UpperCaseString', 'Version',
    'SIMPLE_TYPES_SET', 'SIMPLE_TYPES', 'is_simple_value', 'is_simple_type'
)

# ==============================================================================


try:
    u_str = unicode
except NameError:
    u_str = str

# ==============================================================================

_TRY_ENCODINGS = []
for enc in [
    sys.stdout.encoding,
    locale.getpreferredencoding(False),
    sys.getfilesystemencoding(),
    sys.getdefaultencoding(),
    'utf-8',
]:
    if enc:
        enc = enc.lower()
        if enc not in _TRY_ENCODINGS:
            _TRY_ENCODINGS.append(enc)

# -----------------------------------------------------------


def encode_str(value, encoding=None, _try_encodings=_TRY_ENCODINGS):
    if encoding:
        return value.encode(encoding)

    error = None
    for encoding in _try_encodings:
        try:
            return value.encode(encoding)
        except UnicodeEncodeError as ex:
            if error is None:
                error = ex

    raise error

# ==============================================================================


def decode_bytes(obj, encoding=None, _try_encodings=_TRY_ENCODINGS):
    if encoding:
        return u_str(obj, encoding)

    error = None
    for encoding in _try_encodings:
        try:
            return u_str(obj, encoding)
        except UnicodeDecodeError as ex:
            if error is None:
                error = ex

    raise error

# ==============================================================================


def to_unicode(obj, encoding=None):
    if isinstance(obj, (bytearray, bytes)):
        return decode_bytes(obj, encoding)

    return u_str(obj)

# ==============================================================================

if u_str is not str:
    def is_unicode(value, _ustr=u_str, _isinstance=isinstance):
        return _isinstance(value, _ustr)

    def is_string(value, _ustr=u_str, _str=str, _isinstance=isinstance):
        return _isinstance(value, (_ustr, _str))

    def to_string(value, _ustr=u_str, _str=str, _isinstance=isinstance):
        if _isinstance(value, (_ustr, _str)):
            return value
        return _str(value)

    # -----------------------------------------------------------

    def cast_str(obj, encoding=None, _ustr=u_str):
        if isinstance(obj, _ustr):
            return encode_str(obj, encoding)

        return str(obj)

else:
    to_string = to_unicode
    cast_str = str

    def is_string(value, _str=str, _isinstance=isinstance):
        return _isinstance(value, _str)

    is_unicode = is_string

# ==============================================================================


class String (str):

    def __new__(cls, value=None):

        if type(value) is cls:
            return value

        if value is None:
            value = ''

        return super(String, cls).__new__(cls, value)

# ==============================================================================
# ==============================================================================


class IgnoreCaseString (String):

    def __hash__(self):
        return hash(self.lower())

    def _cmp(self, other, op):
        return op(self.lower(), str(other).lower())

    def __eq__(self, other):
        return self._cmp(other, operator.eq)

    def __ne__(self, other):
        return self._cmp(other, operator.ne)

    def __lt__(self, other):
        return self._cmp(other, operator.lt)

    def __le__(self, other):
        return self._cmp(other, operator.le)

    def __gt__(self, other):
        return self._cmp(other, operator.gt)

    def __ge__(self, other):
        return self._cmp(other, operator.ge)

# ==============================================================================
# ==============================================================================


class LowerCaseString (str):

    def __new__(cls, value=None):

        if type(value) is cls:
            return value

        if value is None:
            value = ''
        else:
            value = str(value)

        return super(LowerCaseString, cls).__new__(cls, value.lower())

# ==============================================================================
# ==============================================================================


class UpperCaseString (str):

    def __new__(cls, value=None):

        if type(value) is cls:
            return value

        if value is None:
            value = ''
        else:
            value = str(value)

        return super(UpperCaseString, cls).__new__(cls, value.upper())

# ==============================================================================
# ==============================================================================


class Version (str):

    __ver_re = re.compile(r'[0-9]+[a-zA-Z]*(\.[0-9]+[a-zA-Z]*)*')

    def __new__(cls, version=None, _ver_re=__ver_re):

        if type(version) is cls:
            return version

        if version is None:
            ver_str = ''
        else:
            ver_str = str(version)

        match = _ver_re.search(ver_str)
        if match:
            ver_str = match.group()
            ver_list = re.findall(r'[0-9]+|[a-zA-Z]+', ver_str)
        else:
            ver_str = ''
            ver_list = []

        self = super(Version, cls).__new__(cls, ver_str)
        conv_ver_list = []

        for v in ver_list:
            if v.isdigit():
                v = int(v)
            conv_ver_list.append(v)

        self.__version = tuple(conv_ver_list)

        return self

    # -----------------------------------------------------------

    @staticmethod
    def __convert(other):
        return other if isinstance(other, Version) else Version(other)

    # -----------------------------------------------------------

    def _cmp(self, other, cmp_op):
        self_ver = self.__version
        other_ver = self.__convert(other).__version

        len_self = len(self_ver)
        len_other = len(other_ver)

        min_len = min(len_self, len_other)
        if min_len == 0:
            return cmp_op(len_self, len_other)

        self_ver = self_ver[:min_len]
        other_ver = other_ver[:min_len]

        return cmp_op(self_ver, other_ver)

    # -----------------------------------------------------------

    def __hash__(self):
        return hash(self.__version)

    def __eq__(self, other):
        return self._cmp(other, operator.eq)

    def __ne__(self, other):
        return self._cmp(other, operator.ne)

    def __lt__(self, other):
        return self._cmp(other, operator.lt)

    def __le__(self, other):
        return self._cmp(other, operator.le)

    def __gt__(self, other):
        return self._cmp(other, operator.gt)

    def __ge__(self, other):
        return self._cmp(other, operator.ge)

# ==============================================================================

SIMPLE_TYPES_SET = frozenset(
    (u_str, str, int, float, complex, bool, bytes, bytearray))
SIMPLE_TYPES = tuple(SIMPLE_TYPES_SET)


def is_simple_value(value, _simple_types=SIMPLE_TYPES):
    return isinstance(value, _simple_types)


def is_simple_type(value_type, _simple_types=SIMPLE_TYPES):
    return issubclass(value_type, _simple_types)
