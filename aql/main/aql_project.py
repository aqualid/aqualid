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
import os.path
import site
import types
import itertools

from aql.utils import CLIConfig, CLIOption, get_function_args, exec_file,\
    flatten_list, find_files, cpu_count, Chdir, expand_file_path

from aql.util_types import FilePath, value_list_type, UniqueList,\
    to_sequence, is_sequence

from aql.entity import NullEntity, EntityBase, FileTimestampEntity,\
    FileChecksumEntity, DirEntity, SimpleEntity

from aql.options import builtin_options, Options, op_iupdate

from aql.nodes import BuildManager, Node,\
    NodeFilter, NodeDirNameFilter, NodeBaseNameFilter

from aql.builtin_tools import BuiltinTool

from .aql_info import get_aql_info
from .aql_tools_manager import get_tools_manager, ErrorToolNotFound

__all__ = ('Project', 'ProjectConfig',
           'ErrorProjectBuilderMethodFewArguments',
           'ErrorProjectBuilderMethodUnbound',
           'ErrorProjectBuilderMethodWithKW',
           'ErrorProjectInvalidMethod',
           )

# ==============================================================================


class ErrorProjectInvalidMethod(Exception):

    def __init__(self, method):
        msg = "Invalid project method: '%s'" % (method,)
        super(ErrorProjectInvalidMethod, self).__init__(msg)

# ==============================================================================


class ErrorProjectUnknownTarget(Exception):

    def __init__(self, target):
        msg = "Unknown build target: '%s'" % (target,)
        super(ErrorProjectUnknownTarget, self).__init__(msg)

# ==============================================================================


class ErrorProjectBuilderMethodWithKW(Exception):

    def __init__(self, method):
        msg = "Keyword arguments are not allowed in builder method: '%s'" % (
            method,)
        super(ErrorProjectBuilderMethodWithKW, self).__init__(msg)

# ==============================================================================


class ErrorProjectBuilderMethodUnbound(Exception):

    def __init__(self, method):
        msg = "Unbound builder method: '%s'" % (method,)
        super(ErrorProjectBuilderMethodUnbound, self).__init__(msg)

# ==============================================================================


class ErrorProjectBuilderMethodFewArguments(Exception):

    def __init__(self, method):
        msg = "Too few arguments in builder method: '%s'" % (method,)
        super(ErrorProjectBuilderMethodFewArguments, self).__init__(msg)

# ==============================================================================


class ErrorProjectBuilderMethodInvalidOptions(Exception):

    def __init__(self, value):
        msg = "Type of 'options' argument must be Options, instead of: " \
              "'%s'(%s)" % (type(value), value)
        super(ErrorProjectBuilderMethodInvalidOptions, self).__init__(msg)

# ==============================================================================


def _get_user_config_dir():
    return os.path.join(os.path.expanduser('~'), '.config')

# ==============================================================================


def _add_packages_from_sys_path(paths):

    local_path = os.path.normcase(os.path.expanduser('~'))

    for path in sys.path:
        path = os.path.normcase(path)
        if path.endswith('-packages') and not path.startswith(local_path):
            if path not in paths:
                paths.append(path)

# ==============================================================================


def _add_packages_from_sysconfig(paths):
    try:
        from distutils.sysconfig import get_python_lib

        path = get_python_lib()
        if path not in paths:
            paths.append(path)
    except Exception:
        pass

# ==============================================================================


def _get_site_packages():

    try:
        return site.getsitepackages()
    except Exception:
        pass

    paths = []

    _add_packages_from_sys_path(paths)
    _add_packages_from_sysconfig(paths)

    return paths

# ==============================================================================


def _get_aqualid_install_dir():
    try:
        import aql
        return os.path.dirname(aql.__file__)
    except Exception:
        return None

# ==============================================================================


def _get_default_tools_path(info=get_aql_info()):

    aql_module_name = info.module

    tool_dirs = _get_site_packages()

    tool_dirs += (site.USER_SITE, _get_user_config_dir())

    tool_dirs = [os.path.join(path, aql_module_name) for path in tool_dirs]

    aql_dir = _get_aqualid_install_dir()
    if aql_dir:
        tool_dirs.insert(-2, aql_dir)  # insert before the local tools

    tool_dirs = [os.path.join(path, 'tools') for path in tool_dirs]
    return tool_dirs

# ==============================================================================


def _read_config(config_file, cli_config, options):

    tools_path = cli_config.tools_path
    cli_config.tools_path = None

    cli_config.read_file(config_file, {'options': options})

    if cli_config.tools_path:
        tools_path.insert(0, cli_config.tools_path)

    cli_config.tools_path = tools_path

# ==============================================================================


class ProjectConfig(object):

    __slots__ = ('directory', 'makefile', 'targets', 'options', 'arguments',
                 'verbose', 'silent', 'no_output', 'jobs', 'keep_going',
                 'search_up', 'default_tools_path', 'tools_path',
                 'no_tool_errors',
                 'clean', 'list_options', 'list_tool_options',
                 'list_targets',
                 'debug_profile', 'debug_profile_top', 'debug_memory',
                 'debug_explain', 'debug_backtrace',
                 'debug_exec',
                 'use_sqlite', 'force_lock',
                 'show_version',
                 )

    # -----------------------------------------------------------

    def __init__(self, args=None):

        paths_type = value_list_type(UniqueList, FilePath)
        strings_type = value_list_type(UniqueList, str)

        cli_options = (

            CLIOption("-C", "--directory", "directory", FilePath, '',
                      "Change directory before reading the make files.",
                      'FILE PATH', cli_only=True),

            CLIOption("-f", "--makefile", "makefile", FilePath, 'make.aql',
                      "Path to a make file.",
                      'FILE PATH', cli_only=True),

            CLIOption("-l", "--list-options", "list_options", bool, False,
                      "List current options and exit."),

            CLIOption("-L", "--list-tool-options", "list_tool_options",
                      strings_type, [],
                      "List tool options and exit.",
                      "TOOL_NAME", cli_only=True),

            CLIOption("-t", "--list-targets", "list_targets", bool, False,
                      "List all available targets and exit.", cli_only=True),

            CLIOption("-c", "--config", "config", FilePath, None,
                      "The configuration file used to read CLI arguments.",
                      cli_only=True),

            CLIOption("-R", "--clean", "clean", bool, False,
                      "Cleans targets.", cli_only=True),

            CLIOption("-u", "--up", "search_up", bool, False,
                      "Search up directory tree for a make file.",
                      cli_only=True),

            CLIOption("-e", "--no-tool-errors", "no_tool_errors", bool, False,
                      "Stop on any error during initialization of tools."),

            CLIOption("-I", "--tools-path", "tools_path", paths_type, [],
                      "Path to tools and setup scripts.", 'FILE PATH, ...'),

            CLIOption("-k", "--keep-going", "keep_going", bool, False,
                      "Keep going when some targets can't be built."),

            CLIOption("-j", "--jobs", "jobs", int, None,
                      "Number of parallel jobs to process targets.", 'NUMBER'),

            CLIOption("-v", "--verbose", "verbose", bool, False,
                      "Verbose mode."),

            CLIOption("-s", "--silent", "silent", bool, False,
                      "Don't print any messages except warnings and errors."),

            CLIOption(None, "--no-output", "no_output", bool, False,
                      "Don't print builder's output messages."),

            CLIOption(None, "--debug-memory", "debug_memory", bool, False,
                      "Display memory usage."),

            CLIOption("-P", "--debug-profile", "debug_profile", FilePath, None,
                      "Run under profiler and save the results "
                      "in the specified file.",
                      'FILE PATH'),

            CLIOption("-T", "--debug-profile-top", "debug_profile_top",
                      int, 30,
                      "Show the specified number of top functions "
                      "from profiler report.",
                      'FILE PATH'),

            CLIOption(None, "--debug-explain", "debug_explain", bool, False,
                      "Show the reasons why targets are being rebuilt"),

            CLIOption(None, "--debug-exec", "debug_exec", bool, False,
                      "Full trace of all executed commands."),

            CLIOption("--bt", "--debug-backtrace", "debug_backtrace",
                      bool, False, "Show call stack back traces for errors."),

            CLIOption(None, "--force-lock", "force_lock", bool, False,
                      "Forces to lock AQL DB file.", cli_only=True),

            CLIOption(None, "--use-sqlite", "use_sqlite", bool, False,
                      "Use SQLite DB."),

            CLIOption("-V", "--version", "version", bool, False,
                      "Show version and exit.", cli_only=True),
        )

        cli_config = CLIConfig(cli_options, args)

        options = builtin_options()

        # -----------------------------------------------------------
        # Add tools path

        # Read a config file from user's home

        user_config = os.path.join(_get_user_config_dir(), 'default.cfg')
        if os.path.isfile(user_config):
            _read_config(user_config, cli_config, options)

        # -----------------------------------------------------------
        # Read a config file specified from CLI

        config = cli_config.config
        if config:
            _read_config(config, cli_config, options)

        # -----------------------------------------------------------
        # Apply non-cli arguments to options

        arguments = {}

        ignore_options = set(ProjectConfig.__slots__)
        ignore_options.add('config')

        for name, value in cli_config.items():
            if (name not in ignore_options) and (value is not None):
                arguments[name] = value

        options.update(arguments)

        # -----------------------------------------------------------

        self.options = options
        self.arguments = arguments
        self.directory = os.path.abspath(cli_config.directory)
        self.makefile = cli_config.makefile
        self.search_up = cli_config.search_up
        self.tools_path = cli_config.tools_path
        self.default_tools_path = _get_default_tools_path()
        self.no_tool_errors = cli_config.no_tool_errors
        self.targets = cli_config.targets
        self.verbose = cli_config.verbose
        self.silent = cli_config.silent
        self.show_version = cli_config.version
        self.no_output = cli_config.no_output
        self.keep_going = cli_config.keep_going
        self.clean = cli_config.clean
        self.list_options = cli_config.list_options
        self.list_tool_options = cli_config.list_tool_options
        self.list_targets = cli_config.list_targets
        self.jobs = cli_config.jobs
        self.force_lock = cli_config.force_lock
        self.use_sqlite = cli_config.use_sqlite
        self.debug_profile = cli_config.debug_profile
        self.debug_profile_top = cli_config.debug_profile_top
        self.debug_memory = cli_config.debug_memory
        self.debug_explain = cli_config.debug_explain
        self.debug_backtrace = cli_config.debug_backtrace
        self.debug_exec = cli_config.debug_exec

# ==============================================================================


class BuilderWrapper(object):
    __slots__ = ('project', 'options', 'tool', 'method', 'arg_names')

    def __init__(self, tool, method, project, options):
        self.arg_names = self.__check_builder_method(method)
        self.tool = tool
        self.method = method
        self.project = project
        self.options = options

    # -----------------------------------------------------------

    @staticmethod
    def __check_builder_method(method):
        if not hasattr(method, '__call__'):
            raise ErrorProjectInvalidMethod(method)

        f_args, f_varargs, f_kw, f_defaults = get_function_args(method)

        if f_kw:
            raise ErrorProjectBuilderMethodWithKW(method)

        min_args = 1  # at least one argument: options

        if isinstance(method, types.MethodType):
            if method.__self__ is None:
                raise ErrorProjectBuilderMethodUnbound(method)

        if len(f_args) < min_args:
            raise ErrorProjectBuilderMethodFewArguments(method)

        return frozenset(f_args)

    # -----------------------------------------------------------

    @staticmethod
    def _add_sources(name, value, sources,
                     _names=('sources', 'source')):
        if name in _names:
            if is_sequence(value):
                sources.extend(value)
            else:
                sources.append(value)

            return True

        return False

    # -----------------------------------------------------------

    @staticmethod
    def _add_deps(value, deps,
                  _node_types=(Node, NodeFilter, EntityBase)):

        if is_sequence(value):
            deps.extend(v for v in value if isinstance(v, _node_types))
        else:
            if isinstance(value, _node_types):
                deps.append(value)

    # -----------------------------------------------------------

    def _get_builder_args(self, kw):
        builder_args = {}
        sources = []
        deps = []

        options = kw.pop("options", None)
        if options is not None:
            if not isinstance(options, Options):
                raise ErrorProjectBuilderMethodInvalidOptions(options)
        else:
            options = self.options

        options = options.override()

        for name, value in kw.items():
            if self._add_sources(name, value, sources):
                continue

            self._add_deps(value, deps)

            if name in self.arg_names:
                builder_args[name] = value
            else:
                options.append_value(name, value, op_iupdate)

        return options, deps, sources, builder_args

    # -----------------------------------------------------------

    def __call__(self, *args, **kw):

        options, deps, sources, builder_args = self._get_builder_args(kw)

        sources += args
        sources = flatten_list(sources)

        builder = self.method(options, **builder_args)

        node = Node(builder, sources)

        node.depends(deps)

        self.project.add_nodes((node,))

        return node

# ==============================================================================


class ToolWrapper(object):

    def __init__(self, tool, project, options):
        self.project = project
        self.options = options
        self.tool = tool

    # -----------------------------------------------------------

    def __getattr__(self, attr):
        method = getattr(self.tool, attr)

        if attr.startswith('_') or not isinstance(method, types.MethodType):
            return method

        builder = BuilderWrapper(self.tool, method, self.project, self.options)

        setattr(self, attr, builder)
        return builder

# ==============================================================================


class ProjectTools(object):

    def __init__(self, project):
        self.project = project
        self.tools_cache = {}

        tools = get_tools_manager()

        config = self.project.config

        tools.load_tools(config.default_tools_path)
        tools.load_tools(config.tools_path)

        self.tools = tools

    # -----------------------------------------------------------

    def _get_tools_options(self):
        tools_options = {}
        for name, tool in self.tools_cache.items():
            tool = next(iter(tool.values()))
            tools_options.setdefault(tool.options, []).append(name)

        return tools_options

    # -----------------------------------------------------------

    def _get_tool_names(self):
        return sorted(self.tools_cache)

    # -----------------------------------------------------------

    def __add_tool(self, tool_name, options):

        options_ref = options.get_hash_ref()

        try:
            return self.tools_cache[tool_name][options_ref]
        except KeyError:
            pass

        project = self.project

        ignore_errors = not project.config.no_tool_errors

        tool, tool_names, tool_options = self.tools.get_tool(tool_name,
                                                             options,
                                                             ignore_errors)

        tool = ToolWrapper(tool, project, tool_options)

        set_attr = self.__dict__.setdefault

        for name in tool_names:
            set_attr(name, tool)
            self.tools_cache.setdefault(name, {})[options_ref] = tool

        return tool

    # -----------------------------------------------------------

    def __getattr__(self, name,
                    _func_types=(types.FunctionType, types.MethodType)):

        options = self.project.options

        tool = BuiltinTool(options)
        tool_method = getattr(tool, name, None)
        if tool_method and isinstance(tool_method, _func_types):
            return BuilderWrapper(tool, tool_method, self.project, options)

        return self.__add_tool(name, options)

    # -----------------------------------------------------------

    def __getitem__(self, name):
        return getattr(self, name)

    # -----------------------------------------------------------

    def get_tools(self, *tool_names, **kw):

        options = kw.pop('options', None)

        tools_path = kw.pop('tools_path', None)
        if tools_path:
            self.tools.load_tools(tools_path)

        if options is None:
            options = self.project.options

        if kw:
            options = options.override()
            options.update(kw)

        tools = [self.__add_tool(tool_name, options)
                 for tool_name in tool_names]

        return tools

    # -----------------------------------------------------------

    def get_tool(self, tool_name, **kw):
        return self.get_tools(tool_name, **kw)[0]

    # -----------------------------------------------------------

    def try_tool(self, tool_name, **kw):
        try:
            return self.get_tools(tool_name, **kw)[0]
        except ErrorToolNotFound:
            return None

    # -----------------------------------------------------------

    def add_tool(self, tool_class, tool_names=tuple()):
        self.tools.add_tool(tool_class, tool_names)

        return self.__add_tool(tool_class, self.project.options)

# ==============================================================================


def _text_targets(targets):
    text = ["", "  Targets:", "==================", ""]

    max_name = ""
    for names, is_built, description in targets:
        max_name = max(max_name, *names, key=len)

    name_format = "{is_built} {name:<%s}" % len(max_name)

    for names, is_built, description in targets:
        if len(names) > 1 and text[-1]:
            text.append('')

        is_built_mark = "*" if is_built else " "

        for name in names:
            text.append(name_format.format(name=name, is_built=is_built_mark))

        text[-1] += ' :  ' + description

        if len(names) > 1:
            text.append('')

    text.append('')
    return text

# ==============================================================================


class Project(object):

    def __init__(self, config):

        self.targets = config.targets
        self.options = config.options
        self.arguments = config.arguments
        self.config = config
        self.scripts_cache = {}
        self.configs_cache = {}
        self.aliases = {}
        self.alias_descriptions = {}
        self.defaults = []

        self.build_manager = BuildManager()

        self.tools = ProjectTools(self)

    # -----------------------------------------------------------

    def __getattr__(self, attr):
        if attr == 'script_locals':
            self.script_locals = self.__get_script_locals()
            return self.script_locals

        raise AttributeError("No attribute '%s'" % (attr,))

    # -----------------------------------------------------------

    def __get_script_locals(self):

        script_locals = {
            'options':          self.options,
            'tools':            self.tools,
            'Tool':             self.tools.get_tool,
            'TryTool':          self.tools.try_tool,
            'Tools':            self.tools.get_tools,
            'AddTool':          self.tools.add_tool,
            'LoadTools':        self.tools.tools.load_tools,
            'FindFiles':        find_files,
            'GetProject':       self.get_project,
            'GetProjectConfig': self.get_project_config,
            'GetBuildTargets':  self.get_build_targets,
            'File':             self.make_file_entity,
            'Entity':           self.make_entity,
            'Dir':              self.make_dir_entity,
            'Config':           self.read_config,
            'Script':           self.read_script,
            'SetBuildDir':      self.set_build_dir,
            'Depends':          self.depends,
            'Requires':         self.requires,
            'RequireModules':   self.require_modules,
            'Sync':             self.sync_nodes,
            'BuildIf':          self.build_if,
            'SkipIf':           self.skip_if,
            'Alias':            self.alias_nodes,
            'Default':          self.default_build,
            'AlwaysBuild':      self.always_build,
            'Build':            self.build,
            'Clear':            self.clear,
            'DirName':          self.node_dirname,
            'BaseName':         self.node_basename,
        }

        return script_locals

    # -----------------------------------------------------------

    def get_project(self):
        return self

    # -----------------------------------------------------------

    def get_project_config(self):
        return self.config

    # -----------------------------------------------------------

    def get_build_targets(self):
        return self.targets

    # -----------------------------------------------------------

    def make_file_entity(self, filepath, options=None):
        if options is None:
            options = self.options

        file_type = FileTimestampEntity \
            if options.file_signature == 'timestamp' \
            else FileChecksumEntity

        return file_type(filepath)

    # -----------------------------------------------------------

    def make_dir_entity(self, filepath):
        return DirEntity(filepath)

    # -----------------------------------------------------------

    def make_entity(self, data, name=None):
        return SimpleEntity(data=data, name=name)

    # -----------------------------------------------------------

    def _get_config_options(self, config, options):

        if options is None:
            options = self.options

        options_ref = options.get_hash_ref()

        config = os.path.normcase(os.path.abspath(config))

        options_set = self.configs_cache.setdefault(config, set())

        if options_ref in options_set:
            return None

        options_set.add(options_ref)

        return options

    # -----------------------------------------------------------

    def _remove_overridden_options(self, result):
        for arg in self.arguments:
            try:
                del result[arg]
            except KeyError:
                pass

    # -----------------------------------------------------------

    def read_config(self, config, options=None):

        options = self._get_config_options(config, options)

        if options is None:
            return

        config_locals = {'options': options}

        dir_name, file_name = os.path.split(config)
        with Chdir(dir_name):
            result = exec_file(file_name, config_locals)

        tools_path = result.pop('tools_path', None)
        if tools_path:
            self.tools.tools.load_tools(tools_path)

        self._remove_overridden_options(result)

        options.update(result)

    # -----------------------------------------------------------

    def read_script(self, script):

        script = os.path.normcase(os.path.abspath(script))

        scripts_cache = self.scripts_cache

        script_result = scripts_cache.get(script, None)
        if script_result is not None:
            return script_result

        dir_name, file_name = os.path.split(script)
        with Chdir(dir_name):
            script_result = exec_file(file_name, self.script_locals)

        scripts_cache[script] = script_result
        return script_result

    # -----------------------------------------------------------

    def add_nodes(self, nodes):
        self.build_manager.add(nodes)

    # -----------------------------------------------------------

    def set_build_dir(self, build_dir):
        build_dir = os.path.abspath(expand_file_path(build_dir))
        if self.options.build_dir != build_dir:
            self.options.build_dir = build_dir

    # -----------------------------------------------------------

    def build_if(self, condition, nodes):
        self.build_manager.build_if(condition, nodes)

    # -----------------------------------------------------------

    def skip_if(self, condition, nodes):
        self.build_manager.skip_if(condition, nodes)

    # -----------------------------------------------------------

    def depends(self, nodes, dependencies):
        dependencies = tuple(to_sequence(dependencies))

        depends = self.build_manager.depends
        for node in to_sequence(nodes):
            node.depends(dependencies)
            depends(node, node.dep_nodes)

    # -----------------------------------------------------------

    def requires(self, nodes, dependencies):
        dependencies = tuple(
            dep for dep in to_sequence(dependencies) if isinstance(dep, Node))

        depends = self.build_manager.depends
        for node in to_sequence(nodes):
            depends(node, dependencies)

    # -----------------------------------------------------------

    def require_modules(self, nodes, dependencies):
        dependencies = tuple(
            dep for dep in to_sequence(dependencies) if isinstance(dep, Node))

        module_depends = self.build_manager.module_depends
        for node in to_sequence(nodes):
            module_depends(node, dependencies)

    # -----------------------------------------------------------

    # TODO: It works not fully correctly yet. See test aq_test_sync_modules
    # def   SyncModules( self, nodes ):
    #   nodes = tuple( node for node in to_sequence( nodes )
    #                  if isinstance( node, Node ) )
    #   self.build_manager.sync( nodes, deep = True)

    # -----------------------------------------------------------

    def sync_nodes(self, *nodes):
        nodes = flatten_list(nodes)

        nodes = tuple(node for node in nodes if isinstance(node, Node))
        self.build_manager.sync(nodes)

    # -----------------------------------------------------------

    def alias_nodes(self, alias, nodes, description=None):
        for alias, node in itertools.product(to_sequence(alias),
                                             to_sequence(nodes)):

            self.aliases.setdefault(alias, set()).add(node)

            if description:
                self.alias_descriptions[alias] = description

    # -----------------------------------------------------------

    def default_build(self, nodes):
        for node in to_sequence(nodes):
            self.defaults.append(node)

    # -----------------------------------------------------------

    def always_build(self, nodes):
        null_value = NullEntity()
        for node in to_sequence(nodes):
            node.depends(null_value)

    # ----------------------------------------------------------

    def _add_alias_nodes(self, target_nodes, aliases):
        try:
            for alias in aliases:
                target_nodes.update(self.aliases[alias])
        except KeyError as ex:
            raise ErrorProjectUnknownTarget(ex.args[0])

    # ----------------------------------------------------------

    def _add_default_nodes(self, target_nodes):
        for node in self.defaults:
            if isinstance(node, Node):
                target_nodes.add(node)
            else:
                self._add_alias_nodes(target_nodes, (node,))

    # ----------------------------------------------------------

    def _get_build_nodes(self):
        target_nodes = set()

        self._add_alias_nodes(target_nodes, self.targets)

        if not target_nodes:
            self._add_default_nodes(target_nodes)

        if not target_nodes:
            target_nodes = None

        return target_nodes

    # ----------------------------------------------------------

    def _get_jobs_count(self, jobs=None):
        if jobs is None:
            jobs = self.config.jobs

        if not jobs:
            jobs = 0
        else:
            jobs = int(jobs)

        if not jobs:
            jobs = cpu_count()

        if jobs < 1:
            jobs = 1

        elif jobs > 32:
            jobs = 32

        return jobs

    # ----------------------------------------------------------

    def build(self, jobs=None):

        jobs = self._get_jobs_count(jobs)

        if not self.options.batch_groups.is_set():
            self.options.batch_groups = jobs

        build_nodes = self._get_build_nodes()

        config = self.config
        keep_going = config.keep_going,
        explain = config.debug_explain
        with_backtrace = config.debug_backtrace
        force_lock = config.force_lock
        use_sqlite = config.use_sqlite

        is_ok = self.build_manager.build(jobs=jobs,
                                         keep_going=bool(keep_going),
                                         nodes=build_nodes,
                                         explain=explain,
                                         with_backtrace=with_backtrace,
                                         use_sqlite=use_sqlite,
                                         force_lock=force_lock)
        return is_ok

    # ----------------------------------------------------------

    def clear(self):

        build_nodes = self._get_build_nodes()

        force_lock = self.config.force_lock
        use_sqlite = self.config.use_sqlite

        self.build_manager.clear(nodes=build_nodes,
                                 use_sqlite=use_sqlite,
                                 force_lock=force_lock)

    # ----------------------------------------------------------

    def list_targets(self):
        targets = []
        node2alias = {}

        for alias, nodes in self.aliases.items():
            key = frozenset(nodes)
            target_info = node2alias.setdefault(key, [[], ""])
            target_info[0].append(alias)
            description = self.alias_descriptions.get(alias, None)
            if description:
                if len(target_info[1]) < len(description):
                    target_info[1] = description

        build_nodes = self._get_build_nodes()
        self.build_manager.shrink(build_nodes)
        build_nodes = self.build_manager.get_nodes()

        for nodes, aliases_and_description in node2alias.items():

            aliases, description = aliases_and_description

            aliases.sort(key=str.lower)
            max_alias = max(aliases, key=len)
            aliases.remove(max_alias)
            aliases.insert(0, max_alias)

            is_built = (build_nodes is None) or nodes.issubset(build_nodes)
            targets.append((tuple(aliases), is_built, description))

        # sorted list in format: [(target_names, is_built, description), ...]
        targets.sort(key=lambda names: names[0][0].lower())

        return _text_targets(targets)

    # ----------------------------------------------------------

    def list_options(self, brief=False):
        result = self.options.help_text("Builtin options:", brief=brief)
        result.append("")
        tool_names = self.tools._get_tool_names()
        if tool_names:
            result.append("Available options of tools: %s" %
                          (', '.join(tool_names)))
        if result[-1]:
            result.append("")
        return result

    # ----------------------------------------------------------

    def list_tools_options(self, tools, brief=False):
        tools = set(to_sequence(tools))
        result = []

        for tools_options, names in self.tools._get_tools_options().items():
            names_set = tools & set(names)
            if names_set:
                tools -= names_set
                options_name = "Options of tool: %s" % (', '.join(names))
                result += tools_options.help_text(options_name, brief=brief)
        if result and result[-1]:
            result.append("")
        return result

    # ----------------------------------------------------------

    def node_dirname(self, node):
        return NodeDirNameFilter(node)

    # ----------------------------------------------------------

    def node_basename(self, node):
        return NodeBaseNameFilter(node)
