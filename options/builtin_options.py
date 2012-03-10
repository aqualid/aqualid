
import os

import logging
import options
import local_host

_Error = logging.Error
_Options = options.Options
_StrOption = options.StrOption
_IntOption = options.IntOption
_PathOption = options.PathOption
_EnumOption = options.EnumOption
_LinkedOption = options.LinkedOption
_VersionOption = options.VersionOption
_BoolOption = options.BoolOption

#//===========================================================================//

def     _add_build_options( options ):
    
    aql_rootdir = os.path.dirname( __file__ )
    
    options.setup = _StrOption( separator = ',', is_list = 1,
                                help = "Setup options", group = "Builds setup" )
    
    options.build_dir = _StrOption( initial_value = 'build', separator = '/', is_list = 1, help = "The building directory prefix.", group = "Builds setup" )
    options.build_path = _PathOption()
    options.build_path = options.build_dir
    
    options.prefix = _StrOption( help = "The building target prefix.",
                                 is_list = 1, separator = '', unique = 0, group = "Builds setup" )
    
    setup_path = os.environ.get('AQL_SETUP_PATH', aql_rootdir + '/setup' )
    options.setup_path = _PathOption( initial_value = setup_path, is_list = 1, update = 'Prepend',
                                      help = "A file path(s) to setup files.\n" \
                                             "By default environment variable AQL_SETUP_PATH is used.",
                                      group = "Builds setup" )
    
    options.tools = _StrOption( separator = ',', is_list = 1,
                                help = "Environment tools", group = "Builds setup" )
    
    tools_path = os.environ.get( 'AQL_TOOLS_PATH', aql_rootdir + '/tools' )
    options.tools_path = _PathOption( initial_value = tools_path, is_list = 1, update = 'Prepend',
                                      help = "A file path(s) to tools files.\n" \
                                             "By default environment variable AQL_TOOLS_PATH is used.",
                                      group = "Builds setup" )
    
    log_level = _IntOption( initial_value = 1, min = 0, max = 3, help = "AQL log level", group = "Builds setup" )
    options.log_level = log_level
    options.ll = log_level
    
    
#//===========================================================================//

def     _add_platform_options( options ):
    
    options.target_os = _EnumOption( allowed_values = ( 'windows', 'linux', 'cygwin', 'darwin', 'java', 'sunos', 'hpux' ),
                                     help = "The target system/OS name, e.g. 'Linux', 'Windows', or 'Java'.", group = "Platform" )
    
    options.target_platform = _StrOption( ignore_case = 1,
                                          help = "The system's distribution, e.g. 'win32', 'Linux'",
                                          group = "Platform")
    
    options.target_os_release = _StrOption( ignore_case = 1,
                                            help = "The target system's release, e.g. '2.2.0' or 'XP'",
                                            group = "Platform")
    
    options.target_os_version = _VersionOption( help = "The target system's release version, e.g. '2.2.0' or '5.1.2600'",
                                                group = "Platform")
    
    options.target_machine = _EnumOption( allowed_values = ('x86-32', 'x86-64', 'arm' ),
                                          aliases = {'i386':'x86-32','i586':'x86-32','i486':'x86-32','i686':'x86-32',
                                                     'i586':'x86-32', 'pc':'x86-32', 'x86':'x86-32', '80x86': 'x86-32'},
                                          help = "The target machine type, e.g. 'i386'", 
                                          group = "Platform" )
    
    options.target_cpu = _StrOption( ignore_case = 1,
                                     help = "The target real processor name, e.g. 'amdk6'.",
                                     group = "Platform" )
    
    options.target_cpu_flags = _StrOption( ignore_case = 1, is_list = 1,
                                           help = "The target CPU flags, e.g. 'mmx', 'sse2'.",
                                           group = "Platform" )
    
    options.target = _StrOption( initial_value = '',
                                 help = "The overall target platform.\n" \
                                         "By default: <target_os>_<target_machine>_<cc_name><cc_ver>",
                                 group = "Platform" )
    
    if local_host.os:       options.target_os = local_host.os
    if local_host.machine:  options.target_machine = local_host.machine

#//===========================================================================//

def     _set_target( options ):
    
    # <target OS>_<target CPU>_<cc name><cc ver>
    
    if_ = options.If()
    
    #//-------------------------------------------------------//
    # Add OS
    
    target_os_nzero = if_.target_os.ne( None )
    target_os_nzero.target += options.target_os
    
    target_os_release_nzero = target_os_nzero.target_os_release.ne('')
    target_os_release_nzero.target += '-'
    target_os_release_nzero.target += options.target_os_release
    
    target_os_release_nzero.target_os_version.ne('').target += options.target_os_version
    
    target_os_nzero.target += '_'
    
    #//-------------------------------------------------------//
    # Add CPU
    
    target_machine_nzero = if_.target_machine.ne( None )
    target_machine_nzero.target += options.target_machine
    
    target_cpu_nzero = target_machine_nzero.target_cpu.ne('')
    target_cpu_nzero.target += '-'
    target_cpu_nzero.target += options.target_cpu
    
    target_machine_nzero.target += '_'
    
    #//-------------------------------------------------------//
    # add C/C++ compiler
    
    options.target += options.cc_name
    
    cc_name_nzero = if_.cc_name.ne('')
    cc_name_nzero.target += '-'
    cc_name_nzero.target += options.cc_ver
    
    #//-------------------------------------------------------//
    # profiler
    
    cc_name_nzero.profiling['true'].target += '_'
    if_.profiling['true'].target += 'prof'

#//===========================================================================//

def     _set_build_dir( options ):
    
    # build_dir = build/<target>/<build variant>
    
    bd_if = options.If()
    
    options.build_dir += options.target
    options.build_dir += options.build_variant

#//===========================================================================//

def     _add_variants( options ):
    
    bv_aliases = { 'release': 'release_speed',
                   'rel': 'release_speed',
                   'dbg': 'debug',
                   'r': 'release_speed',
                   'rs' : 'release_speed',
                   'rz' : 'release_size',
                   'f' : 'final',
                   'd' : 'debug' }
    
    build_variants = _EnumOption( initial_value = 'debug',
                                  allowed_values = ('debug', 'release_speed', 'release_size', 'final'),
                                  aliases = bv_aliases,
                                  separator = ',',
                                  is_list = 1 ,
                                  update = 'Set',
                                  help = "Active build variants",
                                  group = "Builds setup" )
    
    options.build_variants = build_variants
    options.builds = build_variants
    options.b = build_variants
    
    build_variant = _LinkedOption( initial_value = 'debug',
                                   options = options,
                                   linked_opt_name = 'build_variants',
                                   help = "The current build variant.",
                                   group = "Builds setup" )
    
    options.build_variant = build_variant
    options.bv = build_variant
    
    _set_build_dir( options )
    
    if_bv = options.If().bv
    
    debug = if_bv['debug']
    debug.optimization          = 'off'
    debug.inlining              = 'off'
    debug.whole_optimization    = 'off'
    debug.debug_symbols         = 'on'
    debug.runtime_debugging     = 'on'
    
    release_speed = if_bv.one_of( ('release_speed', 'final') )
    release_speed.optimization          = 'speed'
    release_speed.inlining              = 'full'
    release_speed.whole_optimization    = 'on'
    release_speed.debug_symbols         = 'off'
    release_speed.runtime_debugging     = 'off'
    
    release_size = if_bv['release_size']
    release_size.optimization       = 'size'
    release_size.inlining           = 'on'
    release_size.whole_optimization = 'on'
    release_size.debug_symbols      = 'off'
    release_size.runtime_debugging  = 'off'

#//===========================================================================//

def     _add_optimization_options( options ):
    
    optimization = _EnumOption(  initial_value = 'off', allowed_values = ('off', 'size', 'speed'),
                                        aliases = {'0': 'off', '1': 'size', '2': 'speed'},
                                        help = 'Compiler optimization level',
                                        group = "Optimization" )
    
    allowed_values = {'off':0, 'size':2, 'speed':3 }
    allowed_values = (('off',0), ('size',2 ), ('speed',3) )
    allowed_values = ('off', ('size', 1), ('speed', 2) )
    
    options.optimization = optimization
    options.opt = optimization
    options.optim = optimization
    options.O = optimization
    
    #//-------------------------------------------------------//
    
    inlining = _EnumOption( initial_value = 'off', allowed_values = ('off', 'on', 'full'),
                            help = 'Inline function expansion', group = "Optimization" )
    options.inlining = inlining
    options.inline = inlining
    
    #//-------------------------------------------------------//
    
    whole_optimization = _BoolOption( initial_value = 'off', help = 'Whole program optimization', group = "Optimization" )
    options.whole_optimization = whole_optimization
    options.whole_opt = whole_optimization


#//===========================================================================//

def     _add_debug_options( options ):
    
    debug_symbols = _BoolOption( initial_value = 'off', help = 'Include debug symbols', group = "Debug" )
    options.debug_symbols = debug_symbols
    options.debug_info = debug_symbols
    
    #//-------------------------------------------------------//
    
    profiling = _BoolOption( initial_value = 'disabled', help = 'Enable compiler profiling', group = "Debug" )
    options.profiling = profiling
    options.prof = profiling


#//===========================================================================//

def     _add_warning_options( options ):
    
    warning_level = _IntOption( initial_value = 4, min=0, max=4, help = 'Compiler warning level', group = "Warning")
    options.warning_level = warning_level
    options.warning = warning_level
    options.warn = warning_level
    options.wl = warning_level
    
    #//-------------------------------------------------------//
    
    warnings_as_errors = _BoolOption( initial_value = 'off', help = 'Treat warnings as errors', group = "Warning" )
    options.warnings_as_errors = warnings_as_errors
    options.warn_err = warnings_as_errors
    options.warn_as_err = warnings_as_errors
    options.we = warnings_as_errors

#//===========================================================================//

def     _add_code_generation_options( options ):
    
    user_interface = _EnumOption( initial_value = 'console', allowed_values = ['console', 'gui'],
                                  help = 'Application user interface', group = "Code generation" )
    options.user_interface = user_interface
    options.ui = user_interface
    
    #//-------------------------------------------------------//
    
    options.rtti = _BoolOption( initial_value = 'off', help = 'Enable C++ realtime type information', group = "Code generation" )
    
    #//-------------------------------------------------------//
    
    exception_handling = _BoolOption( initial_value = 'on', help = 'Enable C++ exceptions handling', group = "Code generation" )
    options.exception_handling = exception_handling
    options.exceptions = exception_handling
    
    #//-------------------------------------------------------//
    
    keep_asm = _BoolOption( initial_value = 'off', help = 'Keep generated assemblers files', group = "Code generation" )
    options.keep_asm = keep_asm
    options.asm = keep_asm

#//===========================================================================//

def     _add_runtime_options( options ):
    
    runtime_linking = _EnumOption( initial_value = 'default', allowed_values = ['default', 'static', 'shared'],
                                   aliases = {'dynamic': 'shared'},
                                    help = 'Linkage type of runtime library', group = "Runtime" )
    options.runtime_linking = runtime_linking
    options.runtime_link = runtime_linking
    options.link_runtime = runtime_linking
    options.rtlink = runtime_linking
    
    #//-------------------------------------------------------//
    
    runtime_debugging = _BoolOption( initial_value = 'no', help = 'Use debug version of runtime library', group = "Runtime" )
    options.runtime_debugging = runtime_debugging
    options.runtime_debug = runtime_debugging
    options.rt_debug = runtime_debugging
    
    #//-------------------------------------------------------//
    
    runtime_threading = _EnumOption( initial_value = 'single', allowed_values = ['single', 'multi' ],
                                     help = 'Threading mode of runtime library', group = "Runtime" )
    options.runtime_threading = runtime_threading
    options.rt_threading = runtime_threading

#//===========================================================================//

def     _add_cc_options( options ):
    
    options.cflags = _StrOption( is_list = 1, help = "C compiler options", group = "C/C++ compiler" )
    options.ccflags = _StrOption( is_list = 1, help = "Common C/C++ compiler options", group = "C/C++ compiler" )
    options.cxxflags = _StrOption( is_list = 1, help = "C++ compiler options", group = "C/C++ compiler" )
    options.linkflags = _StrOption( is_list = 1, help = "Linker options", group = "C/C++ compiler" )
    options.arflags = _StrOption( is_list = 1, help = "Archiver options", group = "C/C++ compiler" )
    
    options.ocflags = _StrOption( is_list = 1, help = "C compiler optimization options", group = "Optimization" )
    options.occflags = _StrOption( is_list = 1, help = "Common C/C++ compiler optimization options", group = "Optimization" )
    options.ocxxflags = _StrOption( is_list = 1, help = "C++ compiler optimization options", group = "Optimization" )
    options.olinkflags = _StrOption( is_list = 1, help = "Linker optimization options", group = "Optimization" )
    options.oarflags = _StrOption( is_list = 1, help = "Archiver optimization options", group = "Optimization" )
    
    options.cflags = options.ocflags
    options.ccflags = options.occflags
    options.cxxflags = options.ocxxflags
    options.linkflags = options.olinkflags
    options.arflags = options.oarflags
    
    options.cc_name = _StrOption( help = "C/C++ compiler name", group = "C/C++ compiler" )
    options.cc = options.cc_name
    
    options.cc_ver = _VersionOption( help = "C/C++ compiler version", group = "C/C++ compiler" )
    
    options.gcc_path = _StrOption()
    options.gcc_target = _StrOption()
    options.gcc_prefix = _StrOption( help = "GCC C/C++ compiler prefix", group = "C/C++ compiler" )
    options.gcc_suffix = _StrOption( help = "GCC C/C++ compiler suffix", group = "C/C++ compiler" )
    
    cppdefines = _StrOption( is_list = 1, help = "C/C++ preprocessor defines", group = "C/C++ compiler" )
    options.cppdefines = cppdefines
    options.defines = cppdefines
    
    cpppath = _PathOption( is_list = 1, help = "C/C++ preprocessor paths to headers", is_node = 1, group = "C/C++ compiler" )
    options.cpppath = cpppath
    options.include = cpppath
    
    cpppath_lib = _PathOption( is_list = 1, help = "C/C++ preprocessor path to library headers", is_node = 1, group = "C/C++ compiler" )
    options.cpppath_const = cpppath_lib
    options.cpppath_lib = cpppath_lib
    
    options.libpath = _PathOption( is_list = 1, help = "Paths to libraries", is_node = 1, group = "C/C++ compiler" )
    options.libs = _StrOption( is_list = 1, help = "Libraries", group = "C/C++ compiler" )


#//===========================================================================//

def     _add_lint_options( options ):
    
    options.lint = _EnumOption( initial_value = 'off', allowed_values = ['off', 'on', 'global'],
                                aliases = {'0': 'off', '1':'on', '2':'global' },
                                help = 'Lint method', group = "Lint" )
    
    #//-------------------------------------------------------//
    
    options.lint_flags = _StrOption( initial_value = '-b', is_list = 1, help = "Flexelint options", group = "Lint" )
    
    options.lint_passes = _IntOption( initial_value = 3, min=1, help = 'The number of passes Flexelint makes over the source code', group = "Lint" )
    options.lint_passes_flag = _StrOption( initial_value = '-passes(' )
    options.lint_passes_flag += options.lint_passes
    options.lint_passes_flag += ')'
    
    options.lint_warning_level_flag = _StrOption( initial_value = '-w' )
    options.lint_warning_level_flag += options.warning_level
    
    options.lint_flags += options.lint_passes_flag
    options.lint_flags += options.lint_warning_level_flag
    
    #TODO:
    #options.lint_flags += '-passes(' + options.lint_passes + ')'
    #options.lint_flags += '-w' + options.warning_level
    
    options.If().warnings_as_errors['off'].lint_flags += '-zero'

#//===========================================================================//

def     BuiltinOptions():
    
    options = _Options()
    
    _add_build_options( options )
    _add_platform_options( options )
    _add_optimization_options( options )
    _add_debug_options( options )
    _add_warning_options( options )
    _add_code_generation_options( options )
    _add_runtime_options( options )
    _add_cc_options( options )
    _add_lint_options( options )
    
    _add_variants( options )
    _set_target( options )
    
    return options
