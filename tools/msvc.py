import os
import re

from aql import execute_command, ListOptionType, PathOptionType, tool,\
    ToolCommonCpp, CommonCppCompiler, CommonCppArchiver,\
    CommonCppLinker, ToolCommonRes, CommonResCompiler

# ==============================================================================
#  BUILDERS IMPLEMENTATION
# ==============================================================================


def _parse_output(source_paths,
                  output,
                  exclude_dirs,
                  _err_re=re.compile(r".+\s+:\s+(fatal\s)?error\s+[0-9A-Z]+:")
                  ):

    gen_code = ("Generating Code...", "Compiling...")
    include_prefix = "Note: including file:"
    sources_deps = []
    sources_errors = []

    names = iter(map(os.path.basename, source_paths))
    sources = iter(source_paths)

    next_name = next(names, None)

    current_file = None
    filtered_output = []
    current_deps = []
    current_file_failed = False

    for line in output.split('\n'):
        if line == next_name:
            if current_file is not None:
                sources_deps.append(current_deps)
                sources_errors.append(current_file_failed)

            current_file = next(sources, None)
            current_deps = []
            current_file_failed = False

            next_name = next(names, None)

        elif line.startswith(include_prefix):
            dep_file = line[len(include_prefix):].strip()
            dep_file = os.path.normcase(os.path.abspath(dep_file))
            if not dep_file.startswith(exclude_dirs):
                current_deps.append(dep_file)

        elif not line.startswith(gen_code):
            if _err_re.match(line):
                current_file_failed = True

            filtered_output.append(line)

    output = '\n'.join(filtered_output)
    sources_deps.append(current_deps)
    sources_errors.append(current_file_failed)

    return sources_deps, sources_errors, output

# ==============================================================================


class MsvcCompiler (CommonCppCompiler):

    def __init__(self, options):
        super(MsvcCompiler, self).__init__(options)
        self.cmd += ['/nologo', '/c', '/showIncludes']

    # -----------------------------------------------------------

    def build(self, source_entities, targets):

        source = source_entities[0].get()

        obj_file = self.get_obj_path(source)
        cwd = os.path.dirname(obj_file)

        cmd = list(self.cmd)
        cmd += ['/Fo%s' % obj_file, source]

        result = self.exec_cmd_result(cmd, cwd, file_flag='@')

        deps, errors, out = _parse_output((source,),
                                          result.output,
                                          self.ext_cpppath)
        if result.failed():
            result.output = out
            raise result

        targets.add(obj_file)
        targets.add_implicit_deps(deps[0])

        return out

    # -----------------------------------------------------------

    def get_default_obj_ext(self):
        return '.obj'

    # -----------------------------------------------------------

    def _set_targets(self,
                     source_entities,
                     targets,
                     sources,
                     obj_files,
                     output):

        deps, errors, out = _parse_output(sources, output, self.ext_cpppath)

        items = zip(source_entities, obj_files, deps, errors)

        for src_value, obj_file, deps, error in items:
            if not error:
                src_targets = targets[src_value]
                src_targets.add(obj_file)
                src_targets.add_implicit_deps(deps)

        return out

    # -----------------------------------------------------------

    def build_batch(self, source_entities, targets):

        sources = tuple(src.get() for src in source_entities)

        obj_files = self.get_source_target_paths(sources, ext=self.ext)

        cwd = os.path.dirname(obj_files[0])

        cmd = list(self.cmd)
        cmd += sources

        result = self.exec_cmd_result(cmd, cwd, file_flag='@')

        out = self._set_targets(
            source_entities, targets, sources, obj_files, result.output)

        if result.failed():
            result.output = out
            raise result

        return out

# ==============================================================================


class MsvcResCompiler (CommonResCompiler):

    def build(self, source_entities, targets):

        src = source_entities[0].get()

        res_file = self.get_obj_path(src)
        cwd = os.path.dirname(res_file)

        cmd = list(self.cmd)
        cmd += ['/nologo', '/Fo%s' % res_file, src]

        out = self.exec_cmd(cmd, cwd, file_flag='@')

        # deps = _parse_res( src )

        targets.add(res_file)

        return out

# ==============================================================================


class MsvcCompilerMaker (object):

    def make_compiler(self, options):
        return MsvcCompiler(options)

    def make_res_compiler(self, options):
        return MsvcResCompiler(options)

# ==============================================================================


class MsvcArchiver (MsvcCompilerMaker, CommonCppArchiver):

    def build(self, source_entities, targets):

        obj_files = (src.get() for src in source_entities)

        cmd = list(self.cmd)
        cmd += ['/nologo', "/OUT:%s" % self.target]
        cmd += obj_files

        cwd = os.path.dirname(self.target)

        out = self.exec_cmd(cmd, cwd=cwd, file_flag='@')

        targets.add(self.target)

        return out

# ==============================================================================


class MsvcLinker (MsvcCompilerMaker, CommonCppLinker):

    def __init__(self, options, target, shared, def_file):
        super(MsvcLinker, self).__init__(options, target, shared)

        self.libsuffix = options.libsuffix.get()

        if shared:
            self.def_file = def_file

    # -----------------------------------------------------------

    def build(self, source_entities, targets):

        obj_files = (src.get() for src in source_entities)

        cmd = list(self.cmd)
        target = self.target

        if self.shared:
            cmd.append('/dll')
            if self.def_file:
                cmd.append('/DEF:%s' % self.def_file)

            import_lib = os.path.splitext(target)[0] + self.libsuffix
            cmd.append('/IMPLIB:%s' % import_lib)

        itargets = []

        if '/DEBUG' in cmd:
            pdb = target + '.pdb'
            cmd.append("/PDB:%s" % (pdb,))
            itargets.append(pdb)

        cmd += ['/nologo', '/OUT:%s' % target]

        cmd += obj_files

        cwd = os.path.dirname(target)

        out = self.exec_cmd(cmd, cwd=cwd, file_flag='@')

        # -----------------------------------------------------------
        #  SET TARGETS

        if not self.shared:
            tags = None
        else:
            tags = 'shlib'
            if os.path.exists(import_lib):
                targets.add(import_lib, tags='implib')

            exports_lib = os.path.splitext(target)[0] + '.exp'
            if os.path.exists(exports_lib):
                itargets.append(exports_lib)

        targets.add(target, tags=tags)
        targets.add_side_effects(itargets)

        return out

    # -----------------------------------------------------------

# ==============================================================================
# TOOL IMPLEMENTATION
# ==============================================================================


def _get_msvc_specs(cl):

    result = execute_command(cl)

    specs_re = re.compile(r'Compiler Version (?P<version>[0-9.]+) '
                          r'for (?P<machine>[a-zA-Z0-9_-]+)',
                          re.MULTILINE)

    out = result.output

    match = specs_re.search(out)
    if match:
        target_arch = match.group('machine').strip()
        version = match.group('version').strip()
    else:
        target_arch = 'x86-32'
        version = ''

    target_os = 'windows'

    specs = {
        'cc_name':      'msvc',
        'cc_ver':       version,
        'target_os':    target_os,
        'target_arch':  target_arch,
    }

    return specs

# ==============================================================================


class ToolMsvcCommon(ToolCommonCpp):

    @classmethod
    def setup(cls, options):

        if options.cc_name.is_set_not_to('msvc'):
            raise NotImplementedError()

        cl = cls.find_program(options, 'cl')
        link, lib, rc = cls.find_optional_programs(options,
                                                   ['link', 'lib', 'rc'],
                                                   cl)

        specs = _get_msvc_specs(cl)

        options.update(specs)

        options.cc = cl
        options.link = link
        options.lib = lib
        options.rc = rc

    # -----------------------------------------------------------

    def __init__(self, options):
        super(ToolMsvcCommon, self).__init__(options)

        options.env['INCLUDE'] = ListOptionType(value_type=PathOptionType(),
                                                separators=os.pathsep)

        options.env['LIB'] = ListOptionType(value_type=PathOptionType(),
                                            separators=os.pathsep)

        options.env['LIBPATH'] = ListOptionType(value_type=PathOptionType(),
                                                separators=os.pathsep)

        options.objsuffix = '.obj'
        options.ressuffix = '.res'
        options.libprefix = ''
        options.libsuffix = '.lib'
        options.shlibprefix = ''
        options.shlibsuffix = '.dll'
        options.progsuffix = '.exe'

        options.cpppath_prefix = '/I '
        options.libpath_prefix = '/LIBPATH:'
        options.cppdefines_prefix = '/D'
        options.libs_prefix = ''
        options.libs_suffix = '.lib'

        options.linkflags += ['/INCREMENTAL:NO']

        options.sys_cpppath = options.env['INCLUDE']

        if_ = options.If()

        options.language = self.language

        options.cflags += '/TC'
        options.cxxflags += '/TP'

        if_.rtti.is_true().cxxflags += '/GR'
        if_.rtti.is_false().cxxflags += '/GR-'

        if_.exceptions.is_true().cxxflags += '/EHsc'
        if_.exceptions.is_false().cxxflags += ['/EHs-', '/EHc-']

        if_.target_subsystem.eq('console').linkflags += '/SUBSYSTEM:CONSOLE'
        if_.target_subsystem.eq('windows').linkflags += '/SUBSYSTEM:WINDOWS'

        if_.target_arch.eq('x86-32').libflags += '/MACHINE:X86'
        if_.target_arch.eq('x86-64').libflags += '/MACHINE:X64'
        if_.target_arch.eq('arm').libflags += '/MACHINE:ARM'
        if_.target_arch.eq('arm64').libflags += '/MACHINE:ARM64'

        if_.target_arch.eq('x86-32').linkflags += '/MACHINE:X86'
        if_.target_arch.eq('x86-64').linkflags += '/MACHINE:X64'
        if_.target_arch.eq('arm').linkflags += '/MACHINE:ARM'
        if_.target_arch.eq('arm64').linkflags += '/MACHINE:ARM64'

        if_.debug_symbols.is_true().ccflags += '/Z7'
        if_.debug_symbols.is_true().linkflags += '/DEBUG'

        if_runtime_link = if_.runtime_link

        if_runtime_link.eq('shared').runtime_debug.is_false().ccflags += '/MD'
        if_runtime_link.eq('shared').runtime_debug.is_true().ccflags += '/MDd'

        if_runtime_link.eq('static').runtime_debug.is_false().\
            runtime_thread.eq('single').ccflags += '/ML'

        if_runtime_link.eq('static').runtime_debug.is_false().\
            runtime_thread.eq('multi').ccflags += '/MT'

        if_runtime_link.eq('static').runtime_debug.is_true().\
            runtime_thread.eq('single').ccflags += '/MLd'

        if_runtime_link.eq('static').runtime_debug.is_true().\
            runtime_thread.eq('multi').ccflags += '/MTd'

        # if_.cc_ver.ge(7).cc_ver.lt(8).ccflags += '/Zc:forScope /Zc:wchar_t'

        if_.optimization.eq('speed').occflags += '/Ox'
        if_.optimization.eq('speed').olinkflags += ['/OPT:REF', '/OPT:ICF']

        if_.optimization.eq('size').occflags += '/Os'
        if_.optimization.eq('size').olinkflags += ['/OPT:REF', '/OPT:ICF']

        if_.optimization.eq('off').occflags += '/Od'

        if_.inlining.eq('off').occflags += '/Ob0'
        if_.inlining.eq('on').occflags += '/Ob1'
        if_.inlining.eq('full').occflags += '/Ob2'

        if_warning_level = if_.warning_level

        if_warning_level.eq(0).ccflags += '/w'
        if_warning_level.eq(1).ccflags += '/W1'
        if_warning_level.eq(2).ccflags += '/W2'
        if_warning_level.eq(3).ccflags += '/W3'
        if_warning_level.eq(4).ccflags += '/W4'

        if_.warnings_as_errors.is_true().ccflags += '/WX'
        if_.warnings_as_errors.is_true().linkflags += '/WX'

        if_.whole_optimization.is_true().ccflags += '/GL'
        if_.whole_optimization.is_true().linkflags += '/LTCG'

    # -----------------------------------------------------------

    def compile(self, options):
        return MsvcCompiler(options)

    def compile_resource(self, options):
        return MsvcResCompiler(options)

    def link_static_library(self, options, target):
        return MsvcArchiver(options, target)

    def link_shared_library(self, options, target, def_file=None):
        return MsvcLinker(options, target, shared=True, def_file=def_file)

    def link_program(self, options, target):
        return MsvcLinker(options, target, shared=False, def_file=None)

# ==============================================================================


@tool('c++', 'msvcpp', 'msvc++', 'cpp', 'cxx')
class ToolMsVCpp(ToolMsvcCommon):
    language = "c++"

# ==============================================================================


@tool('c', 'msvc', 'cc')
class ToolMsvc(ToolMsvcCommon):
    language = "c"

# ==============================================================================


@tool('rc', 'msrc')
class ToolMsrc(ToolCommonRes):

    @classmethod
    def setup(cls, options):

        rc = cls.find_program(options, 'rc')
        options.target_os = 'windows'
        options.rc = rc

    def __init__(self, options):
        super(ToolMsrc, self).__init__(options)
        options.ressuffix = '.res'

    def compile(self, options):
        return MsvcResCompiler(options)
