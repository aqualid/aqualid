#
# Copyright (c) 2012-2015 The developers of Aqualid project
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


from .aql_simple_types import is_string
from .aql_list_types import List

__all__ = ('Dict', 'value_dict_type', 'split_dict_type')

# ==============================================================================


class Dict (dict):

    @staticmethod
    def to_items(items):
        if not items or (items is NotImplemented):
            return tuple()

        try:
            items = items.items
        except AttributeError:
            return items

        return items()

    # -----------------------------------------------------------

    def __init__(self, items=None):
        super(Dict, self).__init__(self.to_items(items))

    # -----------------------------------------------------------

    def __iadd__(self, items):
        for key, value in self.to_items(items):
            try:
                self[key] += value
            except KeyError:
                self[key] = value

        return self

    # -----------------------------------------------------------

    def copy(self, key_type=None, value_type=None):

        other = Dict()

        for key, value in self.items():
            if key_type:
                key = key_type(key)
            if value_type:
                value = value_type(value)
            other[key] = value

        return other

# ==============================================================================


class _SplitDictBase(object):

    # -----------------------------------------------------------

    @classmethod
    def __to_items(cls, items_str):

        if not is_string(items_str):
            return items_str

        sep = cls._separator
        for s in cls._other_separators:
            items_str = items_str.replace(s, sep)

        items = []

        for v in filter(None, items_str.split(sep)):
            key, _, value = v.partition('=')
            items.append((key, value))

        return items

    # -----------------------------------------------------------

    @classmethod
    def __to_split_dict(cls, items):
        if isinstance(items, cls):
            return items

        return cls(cls.__to_items(items))

    # -----------------------------------------------------------

    def __init__(self, items=None):
        super(_SplitDictBase, self).__init__(self.__to_items(items))

    # -----------------------------------------------------------

    def __iadd__(self, items):
        return super(_SplitDictBase, self).__iadd__(self.__to_items(items))

    # -----------------------------------------------------------

    def update(self, other=None, **kwargs):

        other = self.__to_items(other)

        super(_SplitDictBase, self).update(other)

        items = self.__to_items(kwargs)

        super(_SplitDictBase, self).update(items)

    # -----------------------------------------------------------

    def __eq__(self, other):
        return super(_SplitDictBase, self).__eq__(self.__to_split_dict(other))

    def __ne__(self, other):
        return super(_SplitDictBase, self).__ne__(self.__to_split_dict(other))

    def __lt__(self, other):
        return super(_SplitDictBase, self).__lt__(self.__to_split_dict(other))

    def __le__(self, other):
        return super(_SplitDictBase, self).__le__(self.__to_split_dict(other))

    def __gt__(self, other):
        return super(_SplitDictBase, self).__gt__(self.__to_split_dict(other))

    def __ge__(self, other):
        return super(_SplitDictBase, self).__ge__(self.__to_split_dict(other))

    # -----------------------------------------------------------

    def __str__(self):
        return self._separator.join(sorted("%s=%s" % (key, value)
                                           for key, value in self.items()))

# ==============================================================================


def split_dict_type(dict_type, separators):
    attrs = dict(_separator=separators[0],
                 _other_separators=separators[1:])

    return type('SplitDict', (_SplitDictBase, dict_type), attrs)

# ==============================================================================


class _ValueDictBase(object):
    __VALUE_TYPES = {}

    # -----------------------------------------------------------

    @classmethod
    def get_key_type(cls):
        return cls._key_type

    @classmethod
    def get_value_type(cls):
        return cls._default_value_type

    # -----------------------------------------------------------

    @classmethod
    def _to_value(cls, key, value, val_types=__VALUE_TYPES):

        val_type = cls._default_value_type

        try:
            if val_type is None:
                val_type = val_types[key]
            if isinstance(value, val_type):
                return value
            value = val_type(value)
        except KeyError:
            pass

        cls.set_value_type(key, type(value))
        return value

    # -----------------------------------------------------------

    @classmethod
    def set_value_type(cls, key, value_type, value_types=__VALUE_TYPES):

        default_type = cls._default_value_type

        if default_type is None:

            if value_type is list:
                value_type = List

            if value_type is dict:
                value_type = Dict

            value_types[key] = value_type

    # -----------------------------------------------------------

    @classmethod
    def __to_items(cls, items):

        if isinstance(items, _ValueDictBase):
            return items

        key_type = cls._key_type
        to_value = cls._to_value

        items_tmp = []

        for key, value in Dict.to_items(items):
            key = key_type(key)
            value = to_value(key, value)
            items_tmp.append((key, value))

        return items_tmp

    # -----------------------------------------------------------

    @classmethod
    def __to_value_dict(cls, items):
        if isinstance(items, _ValueDictBase):
            return items

        return cls(items)

    # -----------------------------------------------------------

    def __init__(self, values=None):
        super(_ValueDictBase, self).__init__(self.__to_items(values))

    def __iadd__(self, values):
        return super(_ValueDictBase, self).__iadd__(self.__to_items(values))

    def get(self, key, default=None):
        return super(_ValueDictBase, self).get(self._key_type(key), default)

    def __getitem__(self, key):
        return super(_ValueDictBase, self).__getitem__(self._key_type(key))

    def __setitem__(self, key, value):
        key = self._key_type(key)
        value = self._to_value(key, value)
        return super(_ValueDictBase, self).__setitem__(key, value)

    def __delitem__(self, key):
        return super(_ValueDictBase, self).__delitem__(self._key_type(key))

    def pop(self, key, *args):
        return super(_ValueDictBase, self).pop(self._key_type(key), *args)

    # -----------------------------------------------------------

    def setdefault(self, key, default):
        key = self._key_type(key)
        default = self._to_value(key, default)

        return super(_ValueDictBase, self).setdefault(key, default)

    # -----------------------------------------------------------

    def update(self, other=None, **kwargs):

        other = self.__to_items(other)

        super(_ValueDictBase, self).update(other)

        items = self.__to_items(kwargs)

        super(_ValueDictBase, self).update(items)

    # -----------------------------------------------------------

    def __eq__(self, other):
        return super(_ValueDictBase, self).__eq__(self.__to_value_dict(other))

    def __ne__(self, other):
        return super(_ValueDictBase, self).__ne__(self.__to_value_dict(other))

    def __lt__(self, other):
        return super(_ValueDictBase, self).__lt__(self.__to_value_dict(other))

    def __le__(self, other):
        return super(_ValueDictBase, self).__le__(self.__to_value_dict(other))

    def __gt__(self, other):
        return super(_ValueDictBase, self).__gt__(self.__to_value_dict(other))

    def __ge__(self, other):
        return super(_ValueDictBase, self).__ge__(self.__to_value_dict(other))

    # -----------------------------------------------------------

    def __contains__(self, key):
        return super(_ValueDictBase, self).__contains__(self._key_type(key))

# ==============================================================================


def value_dict_type(dict_type, key_type, default_value_type=None):
    attrs = dict(_key_type=key_type,
                 _default_value_type=default_value_type)

    return type('ValueDict', (_ValueDictBase, dict_type), attrs)
