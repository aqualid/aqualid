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


import operator
import weakref

from aql.util_types import to_sequence, UniqueList, List, Dict
from aql.utils import simplify_value

from .aql_option_types import OptionType, DictOptionType, auto_option_type,\
    OptionHelpGroup,\
    ErrorOptionTypeCantDeduce, ErrorOptionTypeUnableConvertValue
from .aql_option_value import OptionValue, Operation, InplaceOperation,\
    ConditionalValue, Condition,\
    op_set, op_iadd, op_isub, op_iupdate, SimpleOperation,\
    op_set_key, op_iadd_key, op_isub_key

__all__ = (
    'Options',
    'ErrorOptionsCyclicallyDependent', 'ErrorOptionsMergeNonOptions',
    'ErrorOptionsNoIteration',
)

# ==============================================================================


class ErrorOptionsCyclicallyDependent(TypeError):

    def __init__(self):
        msg = "Options cyclically depend from each other."
        super(ErrorOptionsCyclicallyDependent, self).__init__(msg)


class ErrorOptionsMergeNonOptions(TypeError):

    def __init__(self, value):
        msg = "Type '%s' can't be merged with Options." % (type(value),)
        super(ErrorOptionsMergeNonOptions, self).__init__(msg)


class ErrorOptionsMergeDifferentOptions(TypeError):

    def __init__(self, name1, name2):
        msg = "Can't merge one an optional value into two different options " \
              "'%s' and '%s' " % (name1, name2)
        super(ErrorOptionsMergeDifferentOptions, self).__init__(msg)


class ErrorOptionsMergeChild(TypeError):

    def __init__(self):
        msg = "Can't merge child options into the parent options. " \
              "Use join() to move child options into its parent."
        super(ErrorOptionsMergeChild, self).__init__(msg)


class ErrorOptionsJoinNoParent(TypeError):

    def __init__(self, options):
        msg = "Can't join options without parent: %s" % (options, )
        super(ErrorOptionsJoinNoParent, self).__init__(msg)


class ErrorOptionsJoinParent(TypeError):

    def __init__(self, options):
        msg = "Can't join options with children: %s" % (options, )
        super(ErrorOptionsJoinParent, self).__init__(msg)


class ErrorOptionsNoIteration(TypeError):

    def __init__(self):
        msg = "Options doesn't support iteration"
        super(ErrorOptionsNoIteration, self).__init__(msg)


class ErrorOptionsUnableEvaluate(TypeError):

    def __init__(self, name, err):
        msg = "Unable to evaluate option '%s', error: %s" % (name, err)
        super(ErrorOptionsUnableEvaluate, self).__init__(msg)

# ==============================================================================


class _OpValueRef(tuple):

    def __new__(cls, value):
        return super(_OpValueRef, cls).__new__(cls, (value.name, value.key))

    def get(self, options, context):
        name, key = self

        value = getattr(options, name).get(context)

        if key is not NotImplemented:
            value = value[key]

        return value


class _OpValueExRef(tuple):

    def __new__(cls, value):
        return super(_OpValueExRef, cls).__new__(cls, (value.name,
                                                       value.key,
                                                       value.options))

    def get(self):
        name, key, options = self

        value = getattr(options, name).get()

        if key is not NotImplemented:
            value = value[key]

        return value

# ==============================================================================


def _store_op_value(options, value):
    # print("_store_op_value: %s (%s)" % (value,type(value)))

    if isinstance(value, OptionValueProxy):
        value_options = value.options

        if (options is value_options) or options._is_parent(value_options):
            value = _OpValueRef(value)
        else:
            value_options._add_dependency(options)
            value = _OpValueExRef(value)

    elif isinstance(value, dict):
        value = dict((k, _store_op_value(options, v))
                     for k, v in value.items())

    elif isinstance(value, (list, tuple, UniqueList, set, frozenset)):
        value = [_store_op_value(options, v) for v in value]

    return value

# ==============================================================================


def _load_op_value(options, context, value):
    if isinstance(value, _OpValueRef):
        value = value.get(options, context)
        value = simplify_value(value)

    elif isinstance(value, _OpValueExRef):
        value = value.get()
        value = simplify_value(value)

    elif isinstance(value, dict):
        value = dict((k, _load_op_value(options, context, v))
                     for k, v in value.items())

    elif isinstance(value, (list, tuple, UniqueList, set, frozenset)):
        value = [_load_op_value(options, context, v) for v in value]

    else:
        value = simplify_value(value)

    return value


# ==============================================================================
def _eval_cmp_value(value):
    if isinstance(value, OptionValueProxy):
        value = value.get()

    value = simplify_value(value)

    return value


# ==============================================================================
class OptionValueProxy (object):

    def __init__(self,
                 option_value,
                 from_parent,
                 name,
                 options,
                 key=NotImplemented):

        self.option_value = option_value
        self.from_parent = from_parent
        self.name = name
        self.options = options
        self.key = key
        self.child_ref = None

    # -----------------------------------------------------------

    def is_set(self):
        return self.option_value.is_set()

    # -----------------------------------------------------------

    def is_set_not_to(self, value):
        return self.option_value.is_set() and (self != value)

    # -----------------------------------------------------------

    def get(self, context=None):
        self.child_ref = None

        v = self.options.evaluate(self.option_value, context, self.name)
        return v if self.key is NotImplemented else v[self.key]

    # -----------------------------------------------------------

    def __iadd__(self, other):
        self.child_ref = None

        if self.key is not NotImplemented:
            other = op_iadd_key(self.key, other)

        self.options._append_value(
            self.option_value, self.from_parent, other, op_iadd)
        return self

    # -----------------------------------------------------------

    def __add__(self, other):
        return SimpleOperation(operator.add, self, other)

    # -----------------------------------------------------------

    def __radd__(self, other):
        return SimpleOperation(operator.add, other, self)

    # -----------------------------------------------------------

    def __sub__(self, other):
        return SimpleOperation(operator.sub, self, other)

    # -----------------------------------------------------------

    def __rsub__(self, other):
        return SimpleOperation(operator.sub, other, self)

    # -----------------------------------------------------------

    def __isub__(self, other):
        self.child_ref = None

        if self.key is not NotImplemented:
            other = op_isub_key(self.key, other)

        self.options._append_value(
            self.option_value, self.from_parent, other, op_isub)
        return self

    # -----------------------------------------------------------

    def set(self, value):
        self.child_ref = None

        if self.key is not NotImplemented:
            value = op_set_key(self.key, value)

        self.options._append_value(
            self.option_value, self.from_parent, value, op_set)

    # -----------------------------------------------------------

    def __setitem__(self, key, value):
        child_ref = self.child_ref
        if (child_ref is not None) and (child_ref() is value):
            return

        if self.key is not NotImplemented:
            raise KeyError(key)

        option_type = self.option_value.option_type

        if isinstance(option_type, DictOptionType):
            if isinstance(value, OptionType) or (type(value) is type):
                option_type.set_value_type(key, value)
                return

        value = op_set_key(key, value)

        self.child_ref = None

        self.options._append_value(
            self.option_value, self.from_parent, value, op_set)

    # -----------------------------------------------------------

    def __getitem__(self, key):
        if self.key is not NotImplemented:
            raise KeyError(key)

        child = OptionValueProxy(
            self.option_value, self.from_parent, self.name, self.options, key)
        self.child_ref = weakref.ref(child)
        return child

    # -----------------------------------------------------------

    def update(self, value):
        self.child_ref = None
        self.options._append_value(
            self.option_value, self.from_parent, value, op_iupdate)

    # -----------------------------------------------------------

    def __iter__(self):
        raise TypeError()

    # -----------------------------------------------------------

    def __bool__(self):
        return bool(self.get(context=None))

    def __nonzero__(self):
        return bool(self.get(context=None))

    def __str__(self):
        return str(self.get(context=None))

    # -----------------------------------------------------------

    def is_true(self, context):
        return bool(self.get(context))

    def is_false(self, context):
        return not bool(self.get(context))

    # -----------------------------------------------------------

    def eq(self, context, other):
        return self.cmp(context, operator.eq, other)

    def ne(self, context, other):
        return self.cmp(context, operator.ne, other)

    def lt(self, context, other):
        return self.cmp(context, operator.lt, other)

    def le(self, context, other):
        return self.cmp(context, operator.le, other)

    def gt(self, context, other):
        return self.cmp(context, operator.gt, other)

    def ge(self, context, other):
        return self.cmp(context, operator.ge, other)

    def __eq__(self, other):
        return self.eq(None, _eval_cmp_value(other))

    def __ne__(self, other):
        return self.ne(None, _eval_cmp_value(other))

    def __lt__(self, other):
        return self.lt(None, _eval_cmp_value(other))

    def __le__(self, other):
        return self.le(None, _eval_cmp_value(other))

    def __gt__(self, other):
        return self.gt(None, _eval_cmp_value(other))

    def __ge__(self, other):
        return self.ge(None, _eval_cmp_value(other))

    def __contains__(self, other):
        return self.has(None, _eval_cmp_value(other))

    # -----------------------------------------------------------

    def cmp(self, context, cmp_operator, other):
        self.child_ref = None

        value = self.get(context)

        if not isinstance(value, (Dict, List)) and\
           (self.key is NotImplemented):

            other = self.option_value.option_type(other)

        return cmp_operator(value, other)

    # -----------------------------------------------------------

    def has(self, context, other):
        value = self.get(context)

        return other in value

    # -----------------------------------------------------------

    def has_any(self, context, others):

        value = self.get(context)

        for other in to_sequence(others):
            if other in value:
                return True
        return False

    # -----------------------------------------------------------

    def has_all(self, context, others):

        value = self.get(context)

        for other in to_sequence(others):
            if other not in value:
                return False
        return True

    # -----------------------------------------------------------

    def one_of(self, context, others):

        value = self.get(context)

        for other in others:
            other = self.option_value.option_type(other)
            if value == other:
                return True
        return False

    # -----------------------------------------------------------

    def not_in(self, context, others):
        return not self.one_of(context, others)

    # -----------------------------------------------------------

    def option_type(self):
        self.child_ref = None
        return self.option_value.option_type

# ==============================================================================


class ConditionGeneratorHelper(object):

    __slots__ = ('name', 'options', 'condition', 'key')

    def __init__(self, name, options, condition, key=NotImplemented):
        self.name = name
        self.options = options
        self.condition = condition
        self.key = key

    # -----------------------------------------------------------

    @staticmethod
    def __cmp_value(options, context, cmp_method, name, key, *args):
        opt = getattr(options, name)
        if key is not NotImplemented:
            opt = opt[key]

        return getattr(opt, cmp_method)(context, *args)

    # -----------------------------------------------------------

    @staticmethod
    def __make_cmp_condition(condition, cmp_method, name, key, *args):
        return Condition(condition,
                         ConditionGeneratorHelper.__cmp_value,
                         cmp_method,
                         name,
                         key,
                         *args)

    # -----------------------------------------------------------

    def cmp(self, cmp_method, *args):
        condition = self.__make_cmp_condition(
            self.condition, cmp_method, self.name, self.key, *args)
        return ConditionGenerator(self.options, condition)

    # -----------------------------------------------------------

    def __iter__(self):
        raise TypeError()

    # -----------------------------------------------------------

    def __getitem__(self, key):
        if self.key is not NotImplemented:
            raise KeyError(key)

        return ConditionGeneratorHelper(self.name,
                                        self.options,
                                        self.condition,
                                        key)

    # -----------------------------------------------------------

    def __setitem__(self, key, value):
        if not isinstance(value, ConditionGeneratorHelper):

            value = op_set_key(key, value)

            self.options.append_value(
                self.name, value, op_set, self.condition)

    # -----------------------------------------------------------

    def eq(self, other):
        return self.cmp('eq', other)

    def ne(self, other):
        return self.cmp('ne', other)

    def gt(self, other):
        return self.cmp('gt', other)

    def ge(self, other):
        return self.cmp('ge', other)

    def lt(self, other):
        return self.cmp('lt', other)

    def le(self, other):
        return self.cmp('le', other)

    def has(self, value):
        return self.cmp('has', value)

    def has_any(self, values):
        return self.cmp('has_any', values)

    def has_all(self, values):
        return self.cmp('has_all', values)

    def one_of(self, values):
        return self.cmp('one_of', values)

    def not_in(self, values):
        return self.cmp('not_in', values)

    def is_true(self):
        return self.cmp('is_true')

    def is_false(self):
        return self.cmp('is_false')

    # -----------------------------------------------------------

    def __iadd__(self, value):
        if self.key is not NotImplemented:
            value = op_iadd_key(self.key, value)

        self.options.append_value(self.name, value, op_iadd, self.condition)
        return self

    # -----------------------------------------------------------

    def __isub__(self, value):
        if self.key is not NotImplemented:
            value = op_isub_key(self.key, value)

        self.options.append_value(self.name, value, op_isub, self.condition)
        return self

# ==============================================================================


class ConditionGenerator(object):

    def __init__(self, options, condition=None):
        self.__dict__['__options'] = options
        self.__dict__['__condition'] = condition

    # -----------------------------------------------------------

    def __getattr__(self, name):
        return ConditionGeneratorHelper(name,
                                        self.__dict__['__options'],
                                        self.__dict__['__condition'])

    # -----------------------------------------------------------

    def __setattr__(self, name, value):
        if not isinstance(value, ConditionGeneratorHelper):

            condition = self.__dict__['__condition']

            self.__dict__['__options'].append_value(name,
                                                    value,
                                                    op_set,
                                                    condition)

# ==============================================================================


def _items_by_value(items):

    values = {}

    for name, value in items:
        try:
            values[value].add(name)
        except KeyError:
            values[value] = {name}

    return values

# ==============================================================================

# noinspection PyProtectedMember


class Options (object):

    def __init__(self, parent=None):
        self.__dict__['__parent'] = parent
        self.__dict__['__cache'] = {}
        self.__dict__['__opt_values'] = {}
        self.__dict__['__children'] = []

        if parent is not None:
            parent.__dict__['__children'].append(weakref.ref(self))

    # -----------------------------------------------------------

    def _add_dependency(self, child):

        children = self.__dict__['__children']

        for child_ref in children:
            if child_ref() is child:
                return

        if child._is_dependency(self):
            raise ErrorOptionsCyclicallyDependent()

        children.append(weakref.ref(child))

    # -----------------------------------------------------------

    def _is_dependency(self, other):

        children = list(self.__dict__['__children'])

        while children:

            child_ref = children.pop()
            child = child_ref()

            if child is None:
                continue

            if child is other:
                return True

            children += child.__dict__['__children']

        return False

    # -----------------------------------------------------------

    def _is_parent(self, other):

        if other is None:
            return False

        parent = self.__dict__['__parent']

        while parent is not None:
            if parent is other:
                return True

            parent = parent.__dict__['__parent']

        return False

    # -----------------------------------------------------------

    def __copy_parent_option(self, opt_value):
        parent = self.__dict__['__parent']
        items = parent._values_map_by_name().items()
        names = [name for name, value in items if value is opt_value]
        opt_value = opt_value.copy()
        self.__set_opt_value(opt_value, names)

        return opt_value

    # -----------------------------------------------------------

    def get_hash_ref(self):
        if self.__dict__['__opt_values']:
            return weakref.ref(self)

        parent = self.__dict__['__parent']

        if parent is None:
            return weakref.ref(self)

        return parent.get_hash_ref()

    # -----------------------------------------------------------

    def has_changed_key_options(self):

        parent = self.__dict__['__parent']

        for name, opt_value in self.__dict__['__opt_values'].items():
            if not opt_value.is_tool_key() or not opt_value.is_set():
                continue

            parent_opt_value, from_parent = parent._get_value(
                name, raise_ex=False)
            if parent_opt_value is None:
                continue

            if parent_opt_value.is_set():
                value = self.evaluate(opt_value, None, name)
                parent_value = parent.evaluate(parent_opt_value, None, name)
                if value != parent_value:
                    return True

        return False

    # -----------------------------------------------------------

    def __add_new_option(self, name, value):
        self.clear_cache()

        if isinstance(value, OptionType):
            opt_value = OptionValue(value)

        elif isinstance(value, OptionValueProxy):
            if value.options is self:
                if not value.from_parent:
                    opt_value = value.option_value
                else:
                    opt_value = self.__copy_parent_option(value.option_value)

            elif self._is_parent(value.options):
                opt_value = self.__copy_parent_option(value.option_value)

            else:
                opt_value = value.option_value.copy()
                opt_value.reset()
                value = self._make_cond_value(value, op_set)
                opt_value.append_value(value)

        elif isinstance(value, OptionValue):
            opt_value = value

        else:
            opt_value = OptionValue(auto_option_type(value))

            value = self._make_cond_value(value, op_set)
            opt_value.append_value(value)

        self.__dict__['__opt_values'][name] = opt_value

    # -----------------------------------------------------------

    def __set_value(self, name, value, operation_type=op_set):

        opt_value, from_parent = self._get_value(name, raise_ex=False)

        if opt_value is None:
            self.__add_new_option(name, value)
            return

        if isinstance(value, OptionType):
            opt_value.option_type = value
            return

        elif isinstance(value, OptionValueProxy):
            if value.option_value is opt_value:
                return

        elif value is opt_value:
            return

        self._append_value(opt_value, from_parent, value, operation_type)

    # -----------------------------------------------------------

    def __set_opt_value(self, opt_value, names):
        opt_values = self.__dict__['__opt_values']
        for name in names:
            opt_values[name] = opt_value

    # -----------------------------------------------------------

    def __setattr__(self, name, value):
        self.__set_value(name, value)

    # -----------------------------------------------------------

    def __setitem__(self, name, value):
        self.__set_value(name, value)

    # -----------------------------------------------------------

    def _get_value(self, name, raise_ex):
        try:
            return self.__dict__['__opt_values'][name], False
        except KeyError:
            parent = self.__dict__['__parent']
            if parent is not None:
                value, from_parent = parent._get_value(name, False)
                if value is not None:
                    return value, True

            if raise_ex:
                raise AttributeError(
                    "Options '%s' instance has no option '%s'" %
                    (type(self), name))

            return None, False

    # -----------------------------------------------------------

    def __getitem__(self, name):
        return self.__getattr__(name)

    # -----------------------------------------------------------

    def __getattr__(self, name):
        opt_value, from_parent = self._get_value(name, raise_ex=True)
        return OptionValueProxy(opt_value, from_parent, name, self)

    # -----------------------------------------------------------

    def __contains__(self, name):
        return self._get_value(name, raise_ex=False)[0] is not None

    # -----------------------------------------------------------

    def __iter__(self):
        raise ErrorOptionsNoIteration()

    # -----------------------------------------------------------

    def _values_map_by_name(self, result=None):

        if result is None:
            result = {}

        parent = self.__dict__['__parent']
        if parent is not None:
            parent._values_map_by_name(result=result)

        result.update(self.__dict__['__opt_values'])

        return result

    # -----------------------------------------------------------

    def _values_map_by_value(self):
        items = self._values_map_by_name().items()
        return _items_by_value(items)

    # -----------------------------------------------------------

    def help(self, with_parent=False, hidden=False):

        if with_parent:
            options_map = self._values_map_by_name()
        else:
            options_map = self.__dict__['__opt_values']

        options2names = _items_by_value(options_map.items())

        result = {}
        for option, names in options2names.items():
            option_help = option.option_type.help()

            if option_help.is_hidden() and not hidden:
                continue

            option_help.names = names

            try:
                option_help.current_value = self.evaluate(option, {}, names)
            except Exception:
                pass

            group_name = option_help.group if option_help.group else ""

            try:
                group = result[group_name]
            except KeyError:
                group = result[group_name] = OptionHelpGroup(group_name)

            group.append(option_help)

        return sorted(result.values(), key=operator.attrgetter('name'))

    # -----------------------------------------------------------

    def help_text(self, title, with_parent=False, hidden=False, brief=False):

        border = "=" * len(title)
        result = ["", title, border, ""]

        for group in self.help(with_parent=with_parent, hidden=hidden):
            text = group.text(brief=brief, indent=2)
            if result[-1]:
                result.append("")
            result.extend(text)

        return result

    # -----------------------------------------------------------

    def set_group(self, group):
        opt_values = self._values_map_by_name().values()

        for opt_value in opt_values:
            if isinstance(opt_value, OptionValueProxy):
                opt_value = opt_value.option_value

            opt_value.option_type.group = group

    # -----------------------------------------------------------

    def __nonzero__(self):
        return bool(self.__dict__['__opt_values']) or \
            bool(self.__dict__['__parent'])

    def __bool__(self):
        return bool(self.__dict__['__opt_values']) or \
            bool(self.__dict__['__parent'])

    # -----------------------------------------------------------

    def update(self, other):
        if not other:
            return

        if self is other:
            return

        if isinstance(other, Options):
            self.merge(other)

        else:
            ignore_types = (ConditionGeneratorHelper,
                            ConditionGenerator,
                            Options)

            for name, value in other.items():
                if isinstance(value, ignore_types):
                    continue

                try:
                    self.__set_value(name, value, op_iupdate)
                except ErrorOptionTypeCantDeduce:
                    pass

    # -----------------------------------------------------------

    def __merge(self, self_names, other_names, move_values=False):

        self.clear_cache()

        other_values = _items_by_value(other_names.items())

        self_names_set = set(self_names)
        self_values = _items_by_value(self_names.items())

        for value, names in other_values.items():
            same_names = names & self_names_set
            if same_names:
                self_value_name = next(iter(same_names))
                self_value = self_names[self_value_name]
                self_values_names = self_values[self_value]
                self_other_names = same_names - self_values_names
                if self_other_names:
                    raise ErrorOptionsMergeDifferentOptions(
                        self_value_name, self_other_names.pop())
                else:
                    new_names = names - self_values_names
                    self_value.merge(value)
            else:
                if move_values:
                    self_value = value
                else:
                    self_value = value.copy()

                new_names = names

            self.__set_opt_value(self_value, new_names)

    # -----------------------------------------------------------

    def merge(self, other):
        if not other:
            return

        if self is other:
            return

        if not isinstance(other, Options):
            raise ErrorOptionsMergeNonOptions(other)

        if other._is_parent(self):
            raise ErrorOptionsMergeChild()

        self.__merge(self._values_map_by_name(), other._values_map_by_name())

    # -----------------------------------------------------------

    def join(self):
        parent = self.__dict__['__parent']
        if parent is None:
            raise ErrorOptionsJoinNoParent(self)

        if self.__dict__['__children']:
            raise ErrorOptionsJoinParent(self)

        parent.__merge(parent.__dict__['__opt_values'],
                       self.__dict__['__opt_values'],
                       move_values=True)

        self.clear()

    # -----------------------------------------------------------

    def unjoin(self):
        parent = self.__dict__['__parent']
        if parent is None:
            return

        self.__merge(
            self.__dict__['__opt_values'], parent._values_map_by_name())

        self.__dict__['__parent'] = None

    # -----------------------------------------------------------

    def __unjoin_children(self):

        children = self.__dict__['__children']

        for child_ref in children:
            child = child_ref()
            if child is not None:
                child.unjoin()

        del children[:]

    # -----------------------------------------------------------

    def __clear_children_cache(self):

        def _clear_child_cache(ref):
            child = ref()
            if child is not None:
                child.clear_cache()
                return True

            return False

        self.__dict__['__children'] = list(
            filter(_clear_child_cache, self.__dict__['__children']))

    # -----------------------------------------------------------

    def __remove_child(self, child):

        def _filter_child(child_ref, removed_child=child):
            filter_child = child_ref()
            return (filter_child is not None) and \
                   (filter_child is not removed_child)

        self.__dict__['__children'] = list(
            filter(_filter_child, self.__dict__['__children']))

    # -----------------------------------------------------------

    def clear(self):
        parent = self.__dict__['__parent']

        self.__unjoin_children()

        if parent is not None:
            parent.__remove_child(self)

        self.__dict__['__parent'] = None
        self.__dict__['__cache'].clear()
        self.__dict__['__opt_values'].clear()

    # -----------------------------------------------------------

    def override(self, **kw):
        other = Options(self)
        other.update(kw)
        return other

    # -----------------------------------------------------------

    def copy(self):

        other = Options()

        for opt_value, names in self._values_map_by_value().items():
            other.__set_opt_value(opt_value.copy(), names)

        return other

    # -----------------------------------------------------------

    def _evaluate(self, option_value, context):
        try:
            if context is not None:
                return context[option_value]
        except KeyError:
            pass

        attrs = self.__dict__

        if attrs['__opt_values']:
            cache = attrs['__cache']
        else:
            cache = attrs['__parent'].__dict__['__cache']

        try:
            return cache[option_value]
        except KeyError:
            pass

        value = option_value.get(self, context, _load_op_value)
        cache[option_value] = value

        return value

    # -----------------------------------------------------------

    def evaluate(self, option_value, context, name):

        try:
            return self._evaluate(option_value, context)

        except ErrorOptionTypeUnableConvertValue as ex:
            if not name:
                raise

            option_help = ex.option_help
            if option_help.names:
                raise

            option_help.names = tuple(to_sequence(name))
            raise ErrorOptionTypeUnableConvertValue(
                option_help, ex.invalid_value)

        except Exception as ex:
            raise ErrorOptionsUnableEvaluate(name, ex)

    # -----------------------------------------------------------

    def _store_value(self, value):
        if isinstance(value, Operation):
            value.convert(self, _store_op_value)
        else:
            value = _store_op_value(self, value)

        return value

    # -----------------------------------------------------------

    def _load_value(self, value):
        if isinstance(value, Operation):
            return value(self, {}, _load_op_value)
        else:
            value = _load_op_value(self, {}, value)

        return value

    # -----------------------------------------------------------

    def _make_cond_value(self, value, operation_type, condition=None):
        if isinstance(value, ConditionalValue):
            return value

        if not isinstance(value, InplaceOperation):
            value = operation_type(value)

        value = ConditionalValue(value, condition)

        value.convert(self, _store_op_value)

        return value

    # -----------------------------------------------------------

    def append_value(self, name, value, operation_type, condition=None):
        opt_value, from_parent = self._get_value(name, raise_ex=True)
        self._append_value(
            opt_value, from_parent, value, operation_type, condition)

    # -----------------------------------------------------------

    def _append_value(self,
                      opt_value,
                      from_parent,
                      value,
                      operation_type,
                      condition=None):

        value = self._make_cond_value(value, operation_type, condition)

        self.clear_cache()

        if from_parent:
            opt_value = self.__copy_parent_option(opt_value)

        opt_value.append_value(value)

    # -----------------------------------------------------------

    def clear_cache(self):
        self.__dict__['__cache'].clear()
        self.__clear_children_cache()

    # -----------------------------------------------------------

    def when(self, cond=None):

        if cond is not None:
            if isinstance(cond, ConditionGeneratorHelper):
                cond = cond.condition

            elif isinstance(cond, ConditionGenerator):
                cond = cond.__dict__['__condition']

            elif not isinstance(cond, Condition):
                cond = Condition(None,
                                 lambda options, context, arg: bool(arg),
                                 cond)

        return ConditionGenerator(self, cond)

    If = when
