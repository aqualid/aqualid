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


import sys

from aql.util_types import to_sequence
from aql.utils import log_warning, log_error, load_module, load_package,\
    expand_file_path, find_files, event_warning

from aql.builtin_tools import Tool

__all__ = ('tool', 'tool_setup', 'get_tools_manager', 'ErrorToolNotFound')


# ==============================================================================
@event_warning
def event_tools_unable_load_module(settings, module, err):
    log_warning("Unable to load module: %s, error: %s", module, err)


# ==============================================================================
@event_warning
def event_tools_tool_failed(settings, ex, tool_info):
    tool_class = tool_info.tool_class
    module = tool_class.__module__
    try:
        filename = sys.modules[module].__file__
    except Exception:
        filename = module[module.rfind('.') + 1:] + '.py'

    names = ','.join(tool_info.names)

    log_error("Failed to initialize tool: name: %s, class: %s, file: %s",
              names, tool_class.__name__, filename)
    log_error(ex)


# ==============================================================================
def _tool_setup_stub(cls, options):
    pass


# ==============================================================================
class ErrorToolInvalid(Exception):

    def __init__(self, tool_class):
        msg = "Invalid tool type: '%s'" % (tool_class,)
        super(ErrorToolInvalid, self).__init__(msg)


# ==============================================================================
class ErrorToolInvalidSetupMethod(Exception):

    def __init__(self, method):
        msg = "Invalid tool setup method: '%s'" % (method,)
        super(ErrorToolInvalidSetupMethod, self).__init__(msg)


# ==============================================================================
class ErrorToolNotFound(Exception):

    def __init__(self, tool_name, loaded_paths):
        loaded_paths = ', '.join(loaded_paths)
        msg = "Tool '%s' has not been found in the following paths: %s" % (
            tool_name, loaded_paths)
        super(ErrorToolNotFound, self).__init__(msg)


# ==============================================================================
class ToolInfo(object):
    __slots__ = (
        'tool_class',
        'names',
        'options',
        'setup_methods',
    )

    # ----------------------------------------------------------

    def __getattr__(self, attr):
        if attr == 'options':
            self.options = self.tool_class.options()
            return self.options

        raise AttributeError("%s instance has no attribute '%s'" %
                             (type(self), attr))

    # ----------------------------------------------------------

    def get_tool(self, options, setup, ignore_errors):

        tool_options = options.override()
        try:
            tool_options.merge(self.options)

            tool_class = self.tool_class

            setup(tool_class, tool_options)

            tool_class.setup(tool_options)

            if tool_options.has_changed_key_options():
                raise NotImplementedError()

            tool_obj = tool_class(tool_options)
            return tool_obj, tool_options

        except NotImplementedError:
            tool_options.clear()

        except Exception as ex:
            tool_options.clear()
            event_tools_tool_failed(ex, self)
            if not ignore_errors:
                raise

        return None, None


# ==============================================================================
class ToolsManager(object):

    __slots__ = (
        'tool_classes',
        'tool_names',
        'tool_info',
        'all_setup_methods',
        'loaded_paths'
    )

    # -----------------------------------------------------------

    def __init__(self):

        self.tool_classes = {}
        self.tool_names = {}
        self.all_setup_methods = {}
        self.tool_info = {}
        self.loaded_paths = []

    # -----------------------------------------------------------

    @staticmethod
    def __add_to_map(values_map, names, value):
        for name in names:
            try:
                value_list = values_map[name]
                if value in value_list:
                    continue
            except KeyError:
                value_list = []
                values_map[name] = value_list

            value_list.insert(0, value)

    # -----------------------------------------------------------

    def add_tool(self, tool_class, names):
        if not issubclass(tool_class, Tool):
            raise ErrorToolInvalid(tool_class)

        if names:
            names = tuple(to_sequence(names))
            self.tool_names.setdefault(tool_class, set()).update(names)
            self.__add_to_map(self.tool_classes, names, tool_class)

    # -----------------------------------------------------------

    def add_setup(self, setup_method, names):
        if not hasattr(setup_method, '__call__'):
            raise ErrorToolInvalidSetupMethod(setup_method)

        names = to_sequence(names)
        self.__add_to_map(self.all_setup_methods, names, setup_method)

    # -----------------------------------------------------------

    def load_tools(self, paths):

        for path in to_sequence(paths):

            path = expand_file_path(path)

            if path in self.loaded_paths:
                continue

            self.loaded_paths.append(path)

            module_files = find_files(path, mask="*.py")
            if not module_files:
                continue

            self._load_tools_package(path, module_files)

    @staticmethod
    def _load_tools_package(path, module_files):
        try:
            package = load_package(path, generate_name=True)
            package_name = package.__name__
        except ImportError:
            package_name = None

        for module_file in module_files:
            try:
                load_module(module_file, package_name)
            except Exception as ex:
                event_tools_unable_load_module(module_file, ex)

    # -----------------------------------------------------------

    def __get_tool_info_list(self, name):

        tools_info = []

        if (type(name) is type) and issubclass(name, Tool):
            tool_classes = (name, )
        else:
            tool_classes = self.tool_classes.get(name, tuple())

        for tool_class in tool_classes:
            tool_info = self.tool_info.get(tool_class, None)
            if tool_info is None:
                names = self.tool_names.get(tool_class, [])

                tool_info = ToolInfo()
                tool_info.tool_class = tool_class
                tool_info.names = names

                self.tool_info[tool_class] = tool_info

                setup_methods = set()
                tool_info.setup_methods = setup_methods

                for name in names:
                    setup_methods.update(self.all_setup_methods.get(name, []))

                if not setup_methods:
                    setup_methods.add(_tool_setup_stub)

            tools_info.append(tool_info)

        return tools_info

    # ==========================================================

    def get_tool(self, tool_name, options, ignore_errors):

        tool_info_list = self.__get_tool_info_list(tool_name)

        for tool_info in tool_info_list:
            get_tool = tool_info.get_tool
            for setup in tool_info.setup_methods:

                tool_obj, tool_options = get_tool(options, setup,
                                                  ignore_errors)
                if tool_obj is not None:
                    tool_names = self.tool_names.get(tool_info.tool_class, [])
                    return tool_obj, tool_names, tool_options

        raise ErrorToolNotFound(tool_name, self.loaded_paths)

# ==============================================================================

_tools_manager = ToolsManager()


def get_tools_manager():
    return _tools_manager


def tool(*tool_names):
    def _tool(tool_class):
        _tools_manager.add_tool(tool_class, tool_names)
        return tool_class

    return _tool

# ==============================================================================


def tool_setup(*tool_names):
    def _tool_setup(setup_method):
        _tools_manager.add_setup(setup_method, tool_names)
        return setup_method

    return _tool_setup
