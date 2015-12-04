import os
import itertools

from aql.utils import find_file_in_paths

from aql.options import StrOptionType, BoolOptionType, VersionOptionType, ListOptionType,\
    AbsPathOptionType, EnumOptionType, SimpleOperation, Options

from aql.nodes import Builder, FileBuilder, Node

from .aql_tool import Tool

__all__ = (
    "ToolCommonCpp", "CommonCppCompiler", "CommonCppArchiver",
    "CommonCppLinker", "ToolCommonRes", "CommonResCompiler",
)


# ==============================================================================


class ErrorBatchBuildCustomExt(Exception):

    def __init__(self, trace, ext):
        msg = "Custom extension '%s' is not supported " \
              "in batch building of node: %s" % (ext, trace)
        super(ErrorBatchBuildCustomExt, self).__init__(msg)

# ==============================================================================


class ErrorBatchBuildWithPrefix(Exception):

    def __init__(self, trace, prefix):
        msg = "Filename prefix '%s' is not supported " \
              "in batch building of node: %s" % (prefix, trace)
        super(ErrorBatchBuildWithPrefix, self).__init__(msg)

# ==============================================================================


class ErrorBatchBuildWithSuffix(Exception):

    def __init__(self, trace, suffix):
        msg = "Filename suffix '%s' is not supported " \
              "in batch building of node: %s" % (suffix, trace)
        super(ErrorBatchBuildWithSuffix, self).__init__(msg)

# ==============================================================================


class ErrorBatchCompileWithCustomTarget(Exception):

    def __init__(self, trace, target):
        msg = "Explicit output target '%s' is not supported " \
              "in batch building of node: %s" % (target, trace)
        super(ErrorBatchCompileWithCustomTarget, self).__init__(msg)

# ==============================================================================


class ErrorCompileWithCustomTarget(Exception):

    def __init__(self, trace, target):
        msg = "Compile several source files using " \
              "the same target '%s' is not supported: %s" % (target, trace)
        super(ErrorCompileWithCustomTarget, self).__init__(msg)

# ==============================================================================
#  BUILDERS IMPLEMENTATION
# ==============================================================================


def _add_prefix(prefix, values):
    prefix = prefix.lstrip()

    if not prefix:
        return values

    if prefix[-1] == ' ':
        prefix = prefix.rstrip()
        return tuple(itertools.chain(*itertools.product((prefix,), values)))

    return tuple("%s%s" % (prefix, value) for value in values)

# ==============================================================================


def _add_ixes(prefix, suffix, values):
    prefix = prefix.lstrip()
    suffix = suffix.strip()

    sep_prefix = prefix and (prefix[-1] == ' ')
    result = []

    for value in values:
        value = "%s%s" % (value, suffix)
        if prefix:
            if sep_prefix:
                result += [prefix, value]
            else:
                result.append("%s%s" % (prefix, value))
        else:
            result.append(value)

    return result

# ==============================================================================


def _preprocessor_options(options):

    options.cppdefines = ListOptionType(
        description="C/C++ preprocessor defines",
        unique=True,
        separators=None)

    options.defines = options.cppdefines

    options.cppdefines_prefix = StrOptionType(
        description="Flag for C/C++ preprocessor defines.", is_hidden=True)

    options.cppdefines_flags = ListOptionType(separators=None)

    options.cppdefines_flags += SimpleOperation(_add_prefix,
                                                options.cppdefines_prefix,
                                                options.cppdefines)

    options.cpppath_flags = ListOptionType(separators=None)

    options.cpppath_prefix = StrOptionType(
        description="Flag for C/C++ preprocessor paths.",
        is_hidden=True)

    options.cpppath = ListOptionType(
        description="C/C++ preprocessor paths to headers",
        value_type=AbsPathOptionType(),
        unique=True,
        separators=None)

    options.include = options.cpppath

    options.cpppath_flags = SimpleOperation(_add_prefix,
                                            options.cpppath_prefix,
                                            options.cpppath)

    options.api_cpppath = ListOptionType(
        value_type=AbsPathOptionType(),
        unique=True,
        description="C/C++ preprocessor paths to API headers",
        separators=None)

    options.cpppath_flags += SimpleOperation(_add_prefix,
                                             options.cpppath_prefix,
                                             options.api_cpppath)

    options.ext_cpppath = ListOptionType(
        value_type=AbsPathOptionType(),
        unique=True,
        description="C/C++ preprocessor path to external headers",
        separators=None)

    options.ext_include = options.ext_cpppath
    options.cpppath_flags += SimpleOperation(_add_prefix,
                                             options.cpppath_prefix,
                                             options.ext_cpppath)

    options.sys_cpppath = ListOptionType(
        value_type=AbsPathOptionType(),
        description="C/C++ preprocessor path to standard headers",
        separators=None)

# ==============================================================================


def _compiler_options(options):

    options.language = EnumOptionType(values=[('c++', 'cpp'), 'c'],
                                      default='c++',
                                      description='Current language',
                                      is_hidden=True)

    options.pic = BoolOptionType(
        description="Generate position-independent code.", default=True)

    options.objsuffix = StrOptionType(
        description="Object file suffix.", is_hidden=True)

    options.cxxflags = ListOptionType(
        description="C++ compiler flags", separators=None)

    options.cflags = ListOptionType(
        description="C++ compiler flags", separators=None)

    options.ccflags = ListOptionType(
        description="Common C/C++ compiler flags", separators=None)

    options.occflags = ListOptionType(
        description="Common C/C++ compiler optimization flags",
        separators=None)

    options.cc = AbsPathOptionType(description="C/C++ compiler program")

    options.cc_name = StrOptionType(is_tool_key=True,
                                    ignore_case=True,
                                    description="C/C++ compiler name")

    options.cc_ver = VersionOptionType(is_tool_key=True,
                                       description="C/C++ compiler version")

    options.cc_cmd = ListOptionType(separators=None,
                                    description="C/C++ compiler full command",
                                    is_hidden=True)

    options.cc_cmd = options.cc
    options.If().language.eq('c++').cc_cmd += options.cxxflags
    options.If().language.eq('c').cc_cmd += options.cflags
    options.cc_cmd += options.ccflags + options.occflags + \
        options.cppdefines_flags + options.cpppath_flags

    options.cxxstd = EnumOptionType(values=['default',
                                            ('c++98', 'c++03'),
                                            ('c++11', 'c++0x'),
                                            ('c++14', 'c++1y')],
                                    default='default',
                                    description='C++ language standard.')

# ==============================================================================


def _resource_compiler_options(options):

    options.rc = AbsPathOptionType(
        description="C/C++ resource compiler program")

    options.ressuffix = StrOptionType(
        description="Compiled resource file suffix.",
        is_hidden=True)

    options.rcflags = ListOptionType(
        description="C/C++ resource compiler flags",
        separators=None)

    options.rc_cmd = ListOptionType(
        description="C/C++ resource resource compiler full command",
        separators=None,
        is_hidden=True)

    options.rc_cmd = [options.rc] + options.rcflags + \
        options.cppdefines_flags + options.cpppath_flags

# ==============================================================================


def _linker_options(options):

    options.libprefix = StrOptionType(
        description="Static library archiver prefix.", is_hidden=True)

    options.libsuffix = StrOptionType(
        description="Static library archiver suffix.", is_hidden=True)

    options.libflags = ListOptionType(
        description="Static library archiver flags", separators=None)

    options.olibflags = ListOptionType(
        description="Static library archiver optimization flags",
        separators=None)

    options.lib = AbsPathOptionType(
        description="Static library archiver program")

    options.lib_cmd = ListOptionType(
        description="Static library archiver full command",
        separators=None,
        is_hidden=True)

    options.lib_cmd = [options.lib] + options.libflags + options.olibflags

    options.shlibprefix = StrOptionType(description="Shared library prefix.",
                                        is_hidden=True)

    options.shlibsuffix = StrOptionType(description="Shared library suffix.",
                                        is_hidden=True)

    options.libpath = ListOptionType(value_type=AbsPathOptionType(),
                                     description="Paths to external libraries",
                                     unique=True,
                                     separators=None)

    options.libpath_prefix = StrOptionType(
        description="Flag for library paths.",
        is_hidden=True)

    options.libpath_flags = ListOptionType(separators=None)

    options.libpath_flags = SimpleOperation(_add_prefix,
                                            options.libpath_prefix,
                                            options.libpath)

    options.libs = ListOptionType(value_type=StrOptionType(),
                                  description="Linking external libraries",
                                  unique=True,
                                  separators=None)

    options.libs_prefix = StrOptionType(
        description="Prefix flag for libraries.", is_hidden=True)

    options.libs_suffix = StrOptionType(
        description="Suffix flag for libraries.", is_hidden=True)

    options.libs_flags = ListOptionType(separators=None)

    options.libs_flags = SimpleOperation(_add_ixes,
                                         options.libs_prefix,
                                         options.libs_suffix,
                                         options.libs)

    options.progsuffix = StrOptionType(
        description="Program suffix.", is_hidden=True)

    options.linkflags = ListOptionType(
        description="Linker flags", separators=None)

    options.olinkflags = ListOptionType(
        description="Linker optimization flags", separators=None)

    options.link = AbsPathOptionType(description="Linker program")

    options.link_cmd = ListOptionType(description="Linker full command",
                                      separators=None,
                                      is_hidden=True)

    options.link_cmd = [options.link] + options.linkflags + \
        options.olinkflags + options.libpath_flags + options.libs_flags

# ==============================================================================


def _get_cpp_options():
    options = Options()
    _preprocessor_options(options)
    _compiler_options(options)
    _resource_compiler_options(options)
    _linker_options(options)

    return options

# ==============================================================================


def _get_res_options():
    options = Options()
    _preprocessor_options(options)
    _resource_compiler_options(options)

    return options

# ==============================================================================


class HeaderChecker (Builder):

    SIGNATURE_ATTRS = ('cpppath', )

    def __init__(self, options):

        cpppath = list(options.cpppath.get())
        cpppath += options.ext_cpppath.get()
        cpppath += options.sys_cpppath.get()

        self.cpppath = cpppath

    # -----------------------------------------------------------

    def build(self, source_entities, targets):

        has_headers = True

        cpppath = self.cpppath

        for header in source_entities:
            found = find_file_in_paths(cpppath, header.get())
            if not found:
                has_headers = False
                break

        targets.add_targets(has_headers)


# ==============================================================================
class CommonCompiler (FileBuilder):

    NAME_ATTRS = ('prefix', 'suffix', 'ext')
    SIGNATURE_ATTRS = ('cmd', )

    # -----------------------------------------------------------

    def __init__(self, options, ext, cmd):

        self.prefix = options.prefix.get()
        self.suffix = options.suffix.get()
        self.ext = ext
        self.cmd = list(cmd)

        target = options.target.get()
        if target:
            self.target = self.get_target_path(target, self.ext, self.prefix)
        else:
            self.target = None

        ext_cpppath = list(options.ext_cpppath.get())
        ext_cpppath += options.sys_cpppath.get()

        self.ext_cpppath = tuple(set(os.path.normcase(
            os.path.abspath(folder)) + os.path.sep for folder in ext_cpppath))

    # -----------------------------------------------------------

    def get_target_entities(self, source_values):
        return self.get_obj_path(source_values[0].get())

    # -----------------------------------------------------------

    def get_obj_path(self, source):
        if self.target:
            return self.target

        return self.get_source_target_path(source,
                                           ext=self.ext,
                                           prefix=self.prefix,
                                           suffix=self.suffix)

    # -----------------------------------------------------------

    def get_default_obj_ext(self):
        """
        Returns a default extension of output object files.
        """
        raise NotImplementedError(
            "Abstract method. It should be implemented in a child class.")

    # -----------------------------------------------------------

    def check_batch_split(self, source_entities):

        default_ext = self.get_default_obj_ext()

        if self.ext != default_ext:
            raise ErrorBatchBuildCustomExt(
                self.get_trace(source_entities), self.ext)

        if self.prefix:
            raise ErrorBatchBuildWithPrefix(
                self.get_trace(source_entities), self.prefix)

        if self.suffix:
            raise ErrorBatchBuildWithSuffix(
                self.get_trace(source_entities), self.suffix)

        if self.target:
            raise ErrorBatchCompileWithCustomTarget(
                self.get_trace(source_entities), self.target)

    # -----------------------------------------------------------

    def split_batch(self, source_entities):
        self.check_batch_split(source_entities)
        return self.split_batch_by_build_dir(source_entities)

    # -----------------------------------------------------------

    def split(self, source_entities):

        if self.target and (len(source_entities) > 1):
            raise ErrorCompileWithCustomTarget(
                self.get_trace(source_entities), self.target)

        return self.split_single(source_entities)

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        if brief:
            name = self.cmd[0]
            name = os.path.splitext(os.path.basename(name))[0]
        else:
            name = ' '.join(self.cmd)

        return name

# ==============================================================================


class CommonCppCompiler (CommonCompiler):

    def __init__(self, options):
        super(CommonCppCompiler, self).__init__(options,
                                                ext=options.objsuffix.get(),
                                                cmd=options.cc_cmd.get())


# ==============================================================================
class CommonResCompiler (CommonCompiler):

    def __init__(self, options):
        super(CommonResCompiler, self).__init__(options,
                                                ext=options.ressuffix.get(),
                                                cmd=options.rc_cmd.get())


# ==============================================================================
class CommonCppLinkerBase(FileBuilder):

    CPP_EXT = (".cc", ".cp", ".cxx", ".cpp", ".CPP", ".c++", ".C", ".c")

    NAME_ATTRS = ('target', )
    SIGNATURE_ATTRS = ('cmd', )

    def __init__(self, options):
        self.compilers = self.get_source_builders(options)

    def get_cpp_exts(self, _cpp_ext=CPP_EXT):
        return _cpp_ext

    # -----------------------------------------------------------

    def get_res_exts(self):
        return '.rc',

    # -----------------------------------------------------------

    def make_compiler(self, options):
        """
        It should return a builder of C/C++ compiler
        """
        raise NotImplementedError(
            "Abstract method. It should be implemented in a child class.")

    # -----------------------------------------------------------

    def make_res_compiler(self, options):
        """
        It should return a builder of C/C++ resource compiler
        """
        raise NotImplementedError(
            "Abstract method. It should be implemented in a child class.")

    # -----------------------------------------------------------

    def add_source_builders(self, builders, exts, builder):
        if builder:
            for ext in exts:
                builders[ext] = builder

    # -----------------------------------------------------------

    def get_source_builders(self, options):
        builders = {}

        compiler = self.make_compiler(options)

        self.add_source_builders(builders, self.get_cpp_exts(), compiler)

        rc_compiler = self.make_res_compiler(options)
        self.add_source_builders(builders, self.get_res_exts(), rc_compiler)

        return builders

    # -----------------------------------------------------------

    def replace(self, options, source_entities):

        cwd = os.getcwd()

        def _add_sources():
            if current_builder is None:
                new_sources.extend(current_sources)
                return

            src_node = Node(current_builder, current_sources, cwd)

            new_sources.append(src_node)

        new_sources = []

        builders = self.compilers

        current_builder = None
        current_sources = []

        for src_file in source_entities:

            ext = os.path.splitext(src_file.get())[1]
            builder = builders.get(ext, None)

            if current_builder is builder:
                current_sources.append(src_file)
            else:
                if current_sources:
                    _add_sources()

                current_builder = builder
                current_sources = [src_file]

        if current_sources:
            _add_sources()

        return new_sources

    # -----------------------------------------------------------

    def get_target_entities(self, source_values):
        return self.target

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        if brief:
            name = self.cmd[0]
            name = os.path.splitext(os.path.basename(name))[0]
        else:
            name = ' '.join(self.cmd)

        return name

# ==============================================================================


class CommonCppArchiver(CommonCppLinkerBase):

    def __init__(self, options, target):

        super(CommonCppArchiver, self).__init__(options)

        prefix = options.libprefix.get()
        ext = options.libsuffix.get()

        self.target = self.get_target_path(target, ext=ext, prefix=prefix)
        self.cmd = options.lib_cmd.get()
        self.shared = False

# ==============================================================================


class CommonCppLinker(CommonCppLinkerBase):

    def __init__(self, options, target, shared):

        super(CommonCppLinker, self).__init__(options)

        if shared:
            prefix = options.shlibprefix.get()
            ext = options.shlibsuffix.get()
        else:
            prefix = options.prefix.get()
            ext = options.progsuffix.get()

        self.target = self.get_target_path(target, prefix=prefix, ext=ext)
        self.cmd = options.link_cmd.get()
        self.shared = shared

    # -----------------------------------------------------------

    def get_weight(self, source_entities):
        return 2 * len(source_entities)


# ==============================================================================
# TOOL IMPLEMENTATION
# ==============================================================================

class ToolCommonCpp(Tool):

    def __init__(self, options):
        options.If().cc_name.is_true().build_dir_name += '_' + \
            options.cc_name + '_' + options.cc_ver

        self.Object = self.compile
        self.Compile = self.compile

        self.Resource = self.compile_resource
        self.CompileResource = self.compile_resource

        self.Library = self.link_static_library
        self.LinkLibrary = self.link_static_library
        self.LinkStaticLibrary = self.link_static_library

        self.SharedLibrary = self.link_shared_library
        self.LinkSharedLibrary = self.link_shared_library

        self.Program = self.link_program
        self.LinkProgram = self.link_program

    # -----------------------------------------------------------

    @classmethod
    def options(cls):
        options = _get_cpp_options()
        options.set_group("C/C++ compiler")

        return options

    # ----------------------------------------------------------

    def check_headers(self, options):
        return HeaderChecker(options)

    CheckHeaders = check_headers

    # ----------------------------------------------------------

    def compile(self, options):
        raise NotImplementedError(
            "Abstract method. It should be implemented in a child class.")

    # ----------------------------------------------------------

    def compile_resource(self, options):
        raise NotImplementedError(
            "Abstract method. It should be implemented in a child class.")

    # ----------------------------------------------------------

    def link_static_library(self, options, target):
        raise NotImplementedError(
            "Abstract method. It should be implemented in a child class.")

    def link_shared_library(self, options, target, def_file=None):
        raise NotImplementedError(
            "Abstract method. It should be implemented in a child class.")

    def link_program(self, options, target):
        raise NotImplementedError(
            "Abstract method. It should be implemented in a child class.")

# ==============================================================================


class ToolCommonRes(Tool):

    def __init__(self, options):
        self.Object = self.compile
        self.Compile = self.compile

    @classmethod
    def options(cls):
        options = _get_res_options()
        options.set_group("C/C++ resource compiler")

        return options

    # -----------------------------------------------------------

    def compile(self, options):
        """
        It should return a builder of C/C++ resource compiler
        """
        raise NotImplementedError(
            "Abstract method. It should be implemented in a child class.")
