import os
import re
import itertools

from aql import read_text_file, Tempfile, execute_command, StrOptionType,\
    ListOptionType, PathOptionType, tool, \
    ToolCommonCpp, CommonCppCompiler, CommonCppArchiver, \
    CommonCppLinker, ToolCommonRes, CommonResCompiler


# ==============================================================================
#  BUILDERS IMPLEMENTATION
# ==============================================================================


def _read_deps(deps_file, exclude_dirs,
               _space_splitter_re=re.compile(r'(?<!\\)\s+')):

    deps = read_text_file(deps_file)

    dep_files = []

    target_sep = ': '
    target_sep_len = len(target_sep)

    for line in deps.splitlines():
        pos = line.find(target_sep)
        if pos >= 0:
            line = line[pos + target_sep_len:]

        line = line.rstrip('\\ ').strip()

        tmp_dep_files = _space_splitter_re.split(line)
        tmp_dep_files = [dep_file.replace('\\ ', ' ')
                         for dep_file in tmp_dep_files if dep_file]

        dep_files += map(os.path.abspath, tmp_dep_files)

    dep_files = iter(dep_files)
    next(dep_files)  # skip the source file

    dep_files = tuple(dep_file
                      for dep_file in dep_files
                      if not dep_file.startswith(exclude_dirs))

    return dep_files

# ==============================================================================

# t.c:3:10: error: called object is not a function or function pointer
# t.c:1:17: note: declared here
#  void foo(char **p, char **q)


def _parse_output(output,
                  _err_re=re.compile(r"(.+):\d+:\d+:\s+error:\s+")):

    failed_sources = set()

    for line in output.split('\n'):
        m = _err_re.match(line)
        if m:
            source_path = m.group(1)
            failed_sources.add(source_path)

    return failed_sources

# ==============================================================================

# noinspection PyAttributeOutsideInit


class GccCompiler (CommonCppCompiler):

    def __init__(self, options):
        super(GccCompiler, self).__init__(options)
        self.cmd += ['-c', '-MMD']

    def build(self, source_entities, targets):
        src = source_entities[0].get()

        obj_file = self.get_obj_path(src)

        cwd = os.path.dirname(obj_file)

        with Tempfile(prefix=obj_file, suffix='.d', folder=cwd) as dep_file:

            cmd = list(self.cmd)

            cmd += ['-o', obj_file, '-MF', dep_file, src]

            out = self.exec_cmd(cmd, cwd, file_flag='@')

            implicit_deps = _read_deps(dep_file, self.ext_cpppath)

            targets.add(obj_file)
            targets.add_implicit_deps(implicit_deps)

            return out

    # -----------------------------------------------------------

    def get_default_obj_ext(self):
        return '.o'

    # -----------------------------------------------------------

    def _set_targets(self, source_entities, targets, obj_files, output):

        failed_sources = _parse_output(output)

        for src_value, obj_file in zip(source_entities, obj_files):
            if src_value.get() not in failed_sources:
                dep_file = os.path.splitext(obj_file)[0] + '.d'
                implicit_deps = _read_deps(dep_file, self.ext_cpppath)

                src_targets = targets[src_value]
                src_targets.add(obj_file)
                src_targets.add_implicit_deps(implicit_deps)

    # -----------------------------------------------------------

    def build_batch(self, source_entities, targets):

        sources = tuple(src.get() for src in source_entities)

        obj_files = self.get_source_target_paths(sources, ext=self.ext)

        cwd = os.path.dirname(obj_files[0])

        cmd = list(self.cmd)
        cmd += sources

        result = self.exec_cmd_result(cmd, cwd, file_flag='@')

        output = result.output
        self._set_targets(source_entities, targets, obj_files, output)

        if result.failed():
            raise result

        return output

# ==============================================================================


class GccResCompiler (CommonResCompiler):

    def build(self, source_entities, targets):

        src = source_entities[0].get()

        res_file = self.get_obj_path(src)
        cwd = os.path.dirname(res_file)

        cmd = list(self.cmd)
        cmd += ['-o', res_file, '-i', src]

        out = self.exec_cmd(cmd, cwd, file_flag='@')

        # deps = _parse_res( src )

        targets.add(res_file)

        return out

# ==============================================================================


class GccCompilerMaker (object):

    def make_compiler(self, options):
        return GccCompiler(options)

    def make_res_compiler(self, options):
        return GccResCompiler(options)

# ==============================================================================


class GccArchiver (GccCompilerMaker, CommonCppArchiver):

    def build(self, source_entities, targets):

        cmd = list(self.cmd)
        cmd.append(self.target)
        cmd += (src.get() for src in source_entities)

        cwd = os.path.dirname(self.target)

        out = self.exec_cmd(cmd, cwd=cwd, file_flag='@')

        targets.add(self.target)

        return out

# ==============================================================================


class GccLinker(GccCompilerMaker, CommonCppLinker):

    def __init__(self, options, target, shared):
        super(GccLinker, self).__init__(options, target, shared)

        self.is_windows = options.target_os == 'windows'
        self.libsuffix = options.libsuffix.get()

    # -----------------------------------------------------------

    def build(self, source_entities, targets):

        target = self.target
        import_lib = None
        shared = self.shared

        cmd = list(self.cmd)

        obj_files = (src.get() for src in source_entities)

        cmd[2:2] = obj_files

        if shared:
            cmd.append('-shared')

            if self.is_windows:
                import_lib = os.path.splitext(target)[0] + self.libsuffix
                cmd.append('-Wl,--out-implib,%s' % import_lib)

        cmd += ['-o', target]

        cwd = os.path.dirname(target)

        out = self.exec_cmd(cmd, cwd=cwd, file_flag='@')

        if shared:
            if import_lib:
                tags = ('shlib',)
                targets.add(import_lib, tags=('implib',))
            else:
                tags = ('shlib', 'implib')
        else:
            tags = None

        targets.add(target, tags=tags)

        return out

# ==============================================================================
#  TOOL IMPLEMENTATION
# ==============================================================================

_OS_PREFIXES = (

    'linux', 'mingw32', 'cygwin',
    'freebsd', 'openbsd', 'netbsd', 'darwin',
    'sunos', 'hpux', 'vxworks', 'solaris', 'interix',
    'uclinux', 'elf',
)

_OS_NAMES = {

    'mingw32': 'windows',
    'darwin': 'osx',
    'sunos': 'solaris',
}


def _get_target_os(target_os):
    for target in target_os.split('-'):
        for prefix in _OS_PREFIXES:
            if target.startswith(prefix):
                name = _OS_NAMES.get(prefix, prefix)
                return name

    return target_os

# ==============================================================================


def _get_gcc_specs(gcc):
    result = execute_command([gcc, '-v'])

    target_re = re.compile(r'^\s*Target:\s+(.+)$', re.MULTILINE)
    version_re = re.compile(r'^\s*gcc version\s+(.+)$', re.MULTILINE)

    out = result.output

    match = target_re.search(out)
    target = match.group(1).strip() if match else ''

    match = version_re.search(out)
    version = match.group(1).strip() if match else ''

    target_list = target.split('-', 1)

    if len(target_list) > 1:
        target_arch = target_list[0]
        target_os = target_list[1]
    else:
        target_os = target_list[0]
        target_arch = 'unknown'

    target_os = _get_target_os(target_os)

    specs = {
        'cc_name':      'gcc',
        'cc_ver':       version,
        'target_os':    target_os,
        'target_arch':  target_arch,
    }

    return specs

# ==============================================================================


def _generate_prog_names(prog, prefix, suffix):
    prefixes = [prefix, ''] if prefix else ['']
    suffixes = [suffix, ''] if suffix else ['']

    return tuple(prefix + prog + suffix
                 for prefix, suffix in itertools.product(prefixes, suffixes))

# ==============================================================================


class ToolGccCommon(ToolCommonCpp):

    @classmethod
    def setup(cls, options):

        if options.cc_name.is_set_not_to('gcc'):
            raise NotImplementedError()

        gcc_prefix = options.gcc_prefix.get()
        gcc_suffix = options.gcc_suffix.get()

        if cls.language == 'c':
            cc = "gcc"
        else:
            cc = "g++"

        gcc = cls.find_program(options, gcc_prefix + cc + gcc_suffix)

        specs = _get_gcc_specs(gcc)

        options.update(specs)

        options.cc = gcc
        options.link = gcc

        ar = _generate_prog_names('ar', gcc_prefix, gcc_suffix)
        rc = _generate_prog_names('windres', gcc_prefix, gcc_suffix)

        lib, rc = cls.find_optional_programs(options, [ar, rc], gcc)

        options.lib = lib
        options.rc = rc

    # -----------------------------------------------------------

    @classmethod
    def options(cls):
        options = super(ToolGccCommon, cls).options()

        options.gcc_prefix = StrOptionType(
            description="GCC C/C++ compiler prefix")
        options.gcc_suffix = StrOptionType(
            description="GCC C/C++ compiler suffix")

        return options

    # -----------------------------------------------------------

    def __init__(self, options):
        super(ToolGccCommon, self).__init__(options)

        options.env['CPATH'] = ListOptionType(value_type=PathOptionType(),
                                              separators=os.pathsep)
        if self.language == 'c':
            options.env['C_INCLUDE_PATH'] = ListOptionType(
                value_type=PathOptionType(),
                separators=os.pathsep
            )

        else:
            options.env['CPLUS_INCLUDE_PATH'] = ListOptionType(
                value_type=PathOptionType(),
                separators=os.pathsep
            )

        options.env['LIBRARY_PATH'] = ListOptionType(
            value_type=PathOptionType(),
            separators=os.pathsep
        )

        if_ = options.If()
        if_windows = if_.target_os.eq('windows')

        options.objsuffix = '.o'
        options.ressuffix = options.objsuffix
        options.libprefix = 'lib'
        options.libsuffix = '.a'
        options.shlibprefix = 'lib'
        options.shlibsuffix = '.so'
        if_windows.shlibprefix = ''
        if_windows.shlibsuffix = '.dll'
        if_windows.progsuffix = '.exe'

        options.cpppath_prefix = '-I '
        options.libpath_prefix = '-L '
        options.cppdefines_prefix = '-D '
        options.libs_prefix = '-l'
        options.libs_suffix = ''

        options.ccflags += ['-pipe', '-x', self.language]
        options.libflags += ['-rcs']
        options.linkflags += ['-pipe']

        options.language = self.language

        if_.rtti.is_true().cxxflags += '-frtti'
        if_.rtti.is_false().cxxflags += '-fno-rtti'

        if_.exceptions.is_true().cxxflags += '-fexceptions'
        if_.exceptions.is_false().cxxflags += '-fno-exceptions'

        if_windows.target_subsystem.eq('console').linkflags +=\
            '-Wl,--subsystem,console'

        if_windows.target_subsystem.eq('windows').linkflags +=\
            '-Wl,--subsystem,windows'

        if_.debug_symbols.is_true().ccflags += '-g'
        if_.debug_symbols.is_false().linkflags += '-Wl,--strip-all'

        if_.runtime_link.eq('static').linkflags += '-static-libgcc'
        if_.runtime_link.eq('shared').linkflags += '-shared-libgcc'

        if_.target_os.eq('windows').runtime_thread.eq(
            'multi').ccflags += '-mthreads'
        if_.target_os.ne('windows').runtime_thread.eq(
            'multi').ccflags += '-pthreads'

        if_.optimization.eq('speed').occflags += '-Ofast'
        if_.optimization.eq('size').occflags += '-Os'
        if_.optimization.eq('off').occflags += '-O0'

        if_.inlining.eq('off').occflags += '-fno-inline'
        if_.inlining.eq('on').occflags += '-finline'
        if_.inlining.eq('full').occflags += '-finline-functions'

        if_.warning_level.eq(0).ccflags += '-w'
        if_.warning_level.eq(3).ccflags += '-Wall'
        if_.warning_level.eq(4).ccflags += ['-Wall', '-Wextra',
                                            '-Wfloat-equal',
                                            '-Wundef', '-Wshadow',
                                            '-Wredundant-decls']

        if_.warning_as_error.is_true().ccflags += '-Werror'

        if_profiling_true = if_.profile.is_true()
        if_profiling_true.ccflags += '-pg'
        if_profiling_true.linkflags += '-pg'

        if_cxxstd = if_.cxxstd

        if_cxx11 = if_cxxstd.eq('c++11')
        if_cxx14 = if_cxxstd.eq('c++14')

        if_cxxstd.eq('c++98').cxxflags += '-std=c++98'
        if_cxx11.cc_ver.ge("4.7").cxxflags += '-std=c++11'
        if_cxx11.cc_ver.ge("4.3").cc_ver.le("4.6").cxxflags += '-std=c++0x'
        if_cxx14.cc_ver.ge("4.8").cxxflags += '-std=c++1y'

        if_.pic.is_true().target_os.not_in(
            ['windows', 'cygwin']).ccflags += '-fPIC'

    # -----------------------------------------------------------

    def compile(self, options):
        return GccCompiler(options)

    def compile_resource(self, options):
        return GccResCompiler(options)

    def link_static_library(self, options, target):
        return GccArchiver(options, target)

    def link_shared_library(self, options, target, def_file=None):
        return GccLinker(options, target, shared=True)

    def link_program(self, options, target):
        return GccLinker(options, target, shared=False)

# ==============================================================================


@tool('c++', 'g++', 'gxx', 'cpp', 'cxx')
class ToolGxx(ToolGccCommon):
    language = "c++"

# ==============================================================================


@tool('c', 'gcc', 'cc')
class ToolGcc(ToolGccCommon):
    language = "c"

# ==============================================================================


@tool('rc', 'windres')
class ToolWindRes(ToolCommonRes):

    # -----------------------------------------------------------

    @classmethod
    def options(cls):
        options = super(ToolWindRes, cls).options()

        options.gcc_prefix = StrOptionType(
            description="GCC C/C++ compiler prefix")

        options.gcc_suffix = StrOptionType(
            description="GCC C/C++ compiler suffix")

        return options

    # -----------------------------------------------------------

    @classmethod
    def setup(cls, options):

        gcc_prefix = options.gcc_prefix.get()
        gcc_suffix = options.gcc_suffix.get()

        rc = _generate_prog_names('windres', gcc_prefix, gcc_suffix)

        rc = cls.find_program(options, rc)
        options.target_os = 'windows'
        options.rc = rc

    def __init__(self, options):
        super(ToolWindRes, self).__init__(options)
        options.ressuffix = '.o'

    def compile(self, options):
        return GccResCompiler(options)
