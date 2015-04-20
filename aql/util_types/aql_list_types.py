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


from .aql_simple_types import u_str, is_string, cast_str

__all__ = ('to_sequence', 'is_sequence', 'UniqueList',
           'List', 'ValueListType', 'SplitListType')

# ==============================================================================


def to_sequence(value, _seq_types=(u_str, bytes, bytearray)):

    if not isinstance(value, _seq_types):
        try:
            iter(value)
            return value
        except TypeError:
            pass

        if value is None:
            return tuple()

    return value,

# ==============================================================================


def is_sequence(value, _seq_types=(u_str, bytes, bytearray)):

    if not isinstance(value, _seq_types):
        try:
            iter(value)
            return True
        except TypeError:
            pass

    return False

# ==============================================================================


class UniqueList (object):

    __slots__ = (
        '__values_list',
        '__values_set',
    )

    # -----------------------------------------------------------

    def __init__(self, values=None):

        self.__values_list = []
        self.__values_set = set()

        self.__add_values(values)

    # -----------------------------------------------------------

    def __add_value_front(self, value):

        values_set = self.__values_set
        values_list = self.__values_list

        if value in values_set:
            values_list.remove(value)
        else:
            values_set.add(value)

        values_list.insert(0, value)

    # -----------------------------------------------------------

    def __add_value(self, value):

        values_set = self.__values_set
        values_list = self.__values_list

        if value not in values_set:
            values_set.add(value)
            values_list.append(value)

    # -----------------------------------------------------------

    def __add_values(self, values):

        values_set_add = self.__values_set.add
        values_list_append = self.__values_list.append
        values_set_size = self.__values_set.__len__
        values_list_size = self.__values_list.__len__

        for value in to_sequence(values):
            values_set_add(value)
            if values_set_size() > values_list_size():
                values_list_append(value)

    # -----------------------------------------------------------

    def __add_values_front(self, values):

        values_set = self.__values_set
        values_list = self.__values_list

        values_set_add = values_set.add
        values_list_insert = values_list.insert
        values_set_size = values_set.__len__
        values_list_size = values_list.__len__
        values_list_index = values_list.index

        pos = 0

        for value in to_sequence(values):
            values_set_add(value)
            if values_set_size() == values_list_size():
                i = values_list_index(value)
                if i < pos:
                    continue

                del values_list[i]

            values_list_insert(pos, value)

            pos += 1

    # -----------------------------------------------------------

    def __remove_value(self, value):

        try:
            self.__values_set.remove(value)
            self.__values_list.remove(value)
        except (KeyError, ValueError):
            pass

    # -----------------------------------------------------------

    def __remove_values(self, values):

        values_set_remove = self.__values_set.remove
        values_list_remove = self.__values_list.remove

        for value in to_sequence(values):
            try:
                values_set_remove(value)
                values_list_remove(value)
            except (KeyError, ValueError):
                pass

    # -----------------------------------------------------------

    def __contains__(self, other):
        return other in self.__values_set

    # -----------------------------------------------------------

    def __len__(self):
        return len(self.__values_list)

    # -----------------------------------------------------------

    def __iter__(self):
        return iter(self.__values_list)

    # -----------------------------------------------------------

    def __reversed__(self):
        return reversed(self.__values_list)

    # -----------------------------------------------------------

    def __str__(self):
        return str(self.__values_list)

    # -----------------------------------------------------------

    def __eq__(self, other):
        if isinstance(other, UniqueList):
            return self.__values_set == other.__values_set

        return self.__values_set == set(to_sequence(other))

    # -----------------------------------------------------------

    def __ne__(self, other):
        if isinstance(other, UniqueList):
            return self.__values_set != other.__values_set

        return self.__values_set != set(to_sequence(other))

    # -----------------------------------------------------------

    def __lt__(self, other):
        if not isinstance(other, UniqueList):
            other = UniqueList(other)

        return self.__values_list < other.__values_list

    # -----------------------------------------------------------

    def __le__(self, other):
        if isinstance(other, UniqueList):
            other = UniqueList(other)

        return self.__values_list <= other.__values_list

    def __gt__(self, other):
        if isinstance(other, UniqueList):
            other = UniqueList(other)

        return self.__values_list > other.__values_list

    # -----------------------------------------------------------

    def __ge__(self, other):
        if isinstance(other, UniqueList):
            other = UniqueList(other)

        return self.__values_list >= other.__values_list

    # -----------------------------------------------------------

    def __getitem__(self, index):
        return self.__values_list[index]

    # -----------------------------------------------------------

    def __iadd__(self, values):
        self.__add_values(values)
        return self

    # -----------------------------------------------------------

    def __add__(self, values):
        other = UniqueList(self)
        other.__add_values(values)
        return other

    # -----------------------------------------------------------

    def __radd__(self, values):
        other = UniqueList(values)
        other.__add_values(self)
        return other

    # -----------------------------------------------------------

    def __isub__(self, values):
        self.__remove_values(values)
        return self

    # -----------------------------------------------------------

    def append(self, value):
        self.__add_value(value)

    # -----------------------------------------------------------

    def extend(self, values):
        self.__add_values(values)

    # -----------------------------------------------------------

    def reverse(self):
        self.__values_list.reverse()

    # -----------------------------------------------------------

    def append_front(self, value):
        self.__add_value_front(value)

    # -----------------------------------------------------------

    def extend_front(self, values):
        self.__add_values_front(values)

    # -----------------------------------------------------------

    def remove(self, value):
        self.__remove_value(value)

    # -----------------------------------------------------------

    def pop(self):
        value = self.__values_list.pop()
        self.__values_set.remove(value)

        return value

    # -----------------------------------------------------------

    def pop_front(self):
        value = self.__values_list.pop(0)
        self.__values_set.remove(value)

        return value

    # -----------------------------------------------------------

    def self_test(self):
        size = len(self)
        if size != len(self.__values_list):
            raise AssertionError(
                "size(%s) != len(self.__values_list)(%s)" %
                (size, len(self.__values_list)))

        if size != len(self.__values_set):
            raise AssertionError(
                "size(%s) != len(self.__values_set)(%s)" %
                (size, len(self.__values_set)))

        if self.__values_set != set(self.__values_list):
            raise AssertionError("self.__values_set != self.__values_list")

# ==============================================================================


class List (list):

    # -----------------------------------------------------------

    def __init__(self, values=None):
        super(List, self).__init__(to_sequence(values))

    # -----------------------------------------------------------

    def __iadd__(self, values):
        super(List, self).__iadd__(to_sequence(values))
        return self

    # -----------------------------------------------------------

    def __add__(self, values):
        other = List(self)
        other += List(self)

        return other

    # -----------------------------------------------------------

    def __radd__(self, values):
        other = List(values)
        other += self

        return other

    # -----------------------------------------------------------

    def __isub__(self, values):
        for value in to_sequence(values):
            while True:
                try:
                    self.remove(value)
                except ValueError:
                    break

        return self

    # -----------------------------------------------------------

    @staticmethod
    def __to_list(values):
        if isinstance(values, List):
            return values

        return List(values)

    # -----------------------------------------------------------

    def __eq__(self, other):
        return super(List, self).__eq__(self.__to_list(other))

    def __ne__(self, other):
        return super(List, self).__ne__(self.__to_list(other))

    def __lt__(self, other):
        return super(List, self).__lt__(self.__to_list(other))

    def __le__(self, other):
        return super(List, self).__le__(self.__to_list(other))

    def __gt__(self, other):
        return super(List, self).__gt__(self.__to_list(other))

    def __ge__(self, other):
        return super(List, self).__ge__(self.__to_list(other))

    # -----------------------------------------------------------

    def append_front(self, value):
        self.insert(0, value)

    # -----------------------------------------------------------

    def extend(self, values):
        super(List, self).extend(to_sequence(values))

    # -----------------------------------------------------------

    def extend_front(self, values):
        self[:0] = to_sequence(values)

    # -----------------------------------------------------------

    def pop_front(self):
        return self.pop(0)

# ==============================================================================


def SplitListType(list_type, separators):

    separator = separators[0]
    other_separators = separators[1:]

    class SplitList (list_type):

        # -----------------------------------------------------------

        # noinspection PyShadowingNames
        @staticmethod
        def __to_sequence(values):
            if not is_string(values):
                return values

            for sep in other_separators:
                values = values.replace(sep, separator)

            return filter(None, values.split(separator))

        # -----------------------------------------------------------

        @staticmethod
        def __to_split_list(values):
            if isinstance(values, SplitList):
                return values

            return SplitList(values)

        # -----------------------------------------------------------

        def __init__(self, values=None):
            super(SplitList, self).__init__(self.__to_sequence(values))

        # -----------------------------------------------------------

        def __iadd__(self, values):
            return super(SplitList, self).__iadd__(self.__to_sequence(values))

        # -----------------------------------------------------------

        def __isub__(self, values):
            return super(SplitList, self).__isub__(self.__to_sequence(values))

        # -----------------------------------------------------------

        def extend(self, values):
            super(SplitList, self).extend(self.__to_sequence(values))

        # -----------------------------------------------------------

        def extend_front(self, values):
            super(SplitList, self).extend_front(self.__to_sequence(values))

        # -----------------------------------------------------------

        def __eq__(self, other):
            return super(SplitList, self).__eq__(self.__to_split_list(other))

        def __ne__(self, other):
            return super(SplitList, self).__ne__(self.__to_split_list(other))

        def __lt__(self, other):
            return super(SplitList, self).__lt__(self.__to_split_list(other))

        def __le__(self, other):
            return super(SplitList, self).__le__(self.__to_split_list(other))

        def __gt__(self, other):
            return super(SplitList, self).__gt__(self.__to_split_list(other))

        def __ge__(self, other):
            return super(SplitList, self).__ge__(self.__to_split_list(other))

        # -----------------------------------------------------------

        def __str__(self):
            return separator.join(map(cast_str, iter(self)))

    # ==========================================================

    return SplitList

# ==============================================================================


def ValueListType(list_type, value_type):

    class _ValueList (list_type):

        # -----------------------------------------------------------

        @staticmethod
        def __to_sequence(values):
            if isinstance(values, _ValueList):
                return values

            return map(value_type, to_sequence(values))

        # -----------------------------------------------------------

        @staticmethod
        def __to_value_list(values):
            if isinstance(values, _ValueList):
                return values

            return _ValueList(values)

        # -----------------------------------------------------------

        def __init__(self, values=None):
            super(_ValueList, self).__init__(self.__to_sequence(values))

        def __iadd__(self, values):
            return super(_ValueList, self).__iadd__(
                self.__to_value_list(values))

        def __isub__(self, values):
            return super(_ValueList, self).__isub__(
                self.__to_value_list(values))

        def extend(self, values):
            super(_ValueList, self).extend(self.__to_value_list(values))

        def extend_front(self, values):
            super(_ValueList, self).extend_front(self.__to_value_list(values))

        def append(self, value):
            super(_ValueList, self).append(value_type(value))

        def count(self, value):
            return super(_ValueList, self).count(value_type(value))

        def index(self, value, i=0, j=-1):
            return super(_ValueList, self).index(value_type(value), i, j)

        def insert(self, i, value):
            return super(_ValueList, self).insert(i, value_type(value))

        def remove(self, value):
            return super(_ValueList, self).remove(value_type(value))

        def __setitem__(self, index, value):
            if type(index) is slice:
                value = self.__to_value_list(value)
            else:
                value = value_type(value)

            return super(_ValueList, self).__setitem__(index, value)

        # -----------------------------------------------------------

        def __eq__(self, other):
            return super(_ValueList, self).__eq__(self.__to_value_list(other))

        def __ne__(self, other):
            return super(_ValueList, self).__ne__(self.__to_value_list(other))

        def __lt__(self, other):
            return super(_ValueList, self).__lt__(self.__to_value_list(other))

        def __le__(self, other):
            return super(_ValueList, self).__le__(self.__to_value_list(other))

        def __gt__(self, other):
            return super(_ValueList, self).__gt__(self.__to_value_list(other))

        def __ge__(self, other):
            return super(_ValueList, self).__ge__(self.__to_value_list(other))

        # -----------------------------------------------------------

        def __contains__(self, other):
            return super(_ValueList, self).__contains__(value_type(other))

    # ==========================================================

    return _ValueList
