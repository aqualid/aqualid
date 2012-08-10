
from aql_options import Options
from aql_simple_types import IgnoreCaseString, FilePath
from aql_option_types import OptionType, BoolOptionType, EnumOptionType, RangeOptionType, ListOptionType, PathOptionType, StrOptionType, VersionOptionType

#//===========================================================================//

def   _build_options():
    options = Options()
    
    options.build_dir         = PathOptionType( description = "The building directory full path." )
    options.build_dir_prefix  = PathOptionType( description = "The building directory prefix." )
    options.build_dir_suffix  = PathOptionType( description = "The building directory suffix." )
    options.build_dir_name    = StrOptionType( description = "The building directory name." )
    options.prefix            = StrOptionType( description = "Output files prefix." )
    
    build_variant = EnumOptionType( values =  [
                                                ('debug', 'dbg', 'd' ),
                                                ('release_speed', 'release', 'rel', 'rs'),
                                                ('release_size', 'rz'),
                                                ('final', 'f'),
                                              ],
                                    description = "Current build variant" )
    
    options.build_variant = build_variant
    options.bv = build_variant
    
    options.build_variants = ListOptionType( value_type = build_variant, unique = True,
                                             description = "Active build variants" )
    options.bvs = options.build_variants
    
    options.setGroup( "Build output" )
    
    return options

#//===========================================================================//

def   _target_options():
    options = Options()
    
    options.target_os = EnumOptionType( values = ['native', 'windows', 'linux', 'cygwin', 'darwin', 'java', 'sunos', 'hpux'],
                                        description = "The target system/OS name, e.g. 'Linux', 'Windows', or 'Java'." )
    
    options.target_arch = EnumOptionType( values = [ 'native',
                                                     ('x86-32', 'x86', '80x86', 'i386', 'i486', 'i586', 'i686'),
                                                     'x86-64',
                                                     'arm' ],
                                            description = "The target machine type, e.g. 'i386'" )
    
    options.target_platform = StrOptionType( ignore_case = True,
                                             description = "The target system's distribution, e.g. 'win32', 'Linux'" )
    
    options.target_os_release = StrOptionType( ignore_case = 1,
                                                description = "The target system's release, e.g. '2.2.0' or 'XP'" )
    
    options.target_os_version = VersionOptionType( description = "The target system's release version, e.g. '2.2.0' or '5.1.2600'" )
    
    options.target_cpu = StrOptionType( ignore_case = 1,
                                        description = "The target real processor name, e.g. 'amdk6'." )
    
    options.target_cpu_flags = ListOptionType( value_type = IgnoreCaseString,
                                               description = "The target CPU flags, e.g. 'mmx', 'sse2'." )
    
    options.setGroup( "Target system" )
    
    return options

#//===========================================================================//

def   _optimization_options():
    
    options = Options()
    
    options.optimization = EnumOptionType( values = [ ('off', 0), ('size', 1), ('speed', 2) ],
                                           description = 'Optimization level' )
    options.optlevel = options.optimization
    options.opt = options.optimization
    
    #//-------------------------------------------------------//
    
    options.inlining = EnumOptionType( values = ['off', 'on', 'full'],
                                       description = 'Inline function expansion' )
    
    #//-------------------------------------------------------//
    
    options.whole_optimization = BoolOptionType( description = 'Whole program optimization' )
    options.whole_opt = options.whole_optimization
    
    options.setGroup("Optimization")
    
    return options

#//===========================================================================//

def   _code_gen_options():
    
    options = Options()
    
    options.debug_symbols = BoolOptionType( description = 'Include debug symbols' )
    
    options.profile = BoolOptionType( description = 'Enable compiler profiling' )
    options.console_app = BoolOptionType( description = 'This option specifies that a console application is to be generated.' )
    
    options.keep_asm = BoolOptionType( description = 'Keep generated assemblers files' )
    
    
    options.runtime_link = EnumOptionType( values = ['default', 'static', ('shared', 'dynamic') ],
                                           description = 'Linkage type of runtime library' )
    options.rt_link = options.runtime_link
    
    
    options.runtime_debug = BoolOptionType( description = 'Use debug version of runtime library' )
    options.rt_debug = options.runtime_debug
    
    
    options.runtime_thread = EnumOptionType( values = ['default', 'single', 'multi' ],
                                             description = 'Threading mode of runtime library' )
    options.rt_thread = options.runtime_thread
    
    options.setGroup( "Code generation" )
    return options

#//===========================================================================//

def     _diagnostic_options( ):
    
    options = Options()
    
    options.warning_level = RangeOptionType( 0, 4, description = 'Warning level' )
    options.warn_level = options.warning_level
    
    options.warning_as_error = BoolOptionType( description = 'Treat warnings as errors' )
    options.werror = options.warning_as_error
    
    options.lint = EnumOptionType( values = [('off', 0), ('on', 1), ('global',2)],
                                   description = 'Lint source code.' )
    
    options.lint_flags = ListOptionType( description = "Lint tool options" )
    
    options.setGroup( "Diagnostic" )
    return options

#//===========================================================================//

def   _setup_options():
    
    options = Options()
    
    #~ setup_path = os.environ.get('AQL_SETUP_PATH', aql_rootdir + '/setup' )
    
    options.setup_path = ListOptionType( value_type = FilePath,
                                          description = "A file path(s) to setup files.\n" \
                                                        "By default environment variable AQL_SETUP_PATH is used." )
    
    options.tools = ListOptionType( value_type = IgnoreCaseString,
                                    description = "Environment tools" )
    
    #~ tools_path = os.environ.get( 'AQL_TOOLS_PATH', aql_rootdir + '/tools' )
    options.tools_path = ListOptionType( value_type = FilePath,
                                         description = "A file path(s) to tools files.\n" \
                                                       "By default environment variable AQL_TOOLS_PATH is used." )
    
    options.log_level = RangeOptionType( 0, 3, description = "Log level" )
    
    options.setGroup( "Setup" )
    return options

#//===========================================================================//

def   _init_defaults( options ):
    
    #//-------------------------------------------------------//
    
    options.target_os   = 'native'
    options.target_arch = 'native'
    
    #//-------------------------------------------------------//
    
    options.build_variant   = 'debug'
    options.build_variants  = 'debug'
    options.optimization    = 'off'
    options.inlining        = 'off'
    options.console_app     = True
    options.runtime_link    = 'default'
    options.runtime_thread  = 'default'
    options.lint            = 'off'
    
    #//-------------------------------------------------------//
    # build_dir_name set to <target OS>_<target arch>
    
    options.build_dir_name = options.target_os
    options.build_dir_name += '_'
    options.build_dir_name += options.target_arch
    options.build_dir_name += '_'
    options.build_dir_name += options.build_variant
    
    #//-------------------------------------------------------//
    
    bv = options.If().build_variant
    
    debug_build_variant = bv['debug']
    debug_build_variant.optimization        = 'off'
    debug_build_variant.inlining            = 'off'
    debug_build_variant.whole_optimization  = 'off'
    debug_build_variant.debug_symbols       = 'on'
    debug_build_variant.runtime_debug       = 'on'
    
    speed_build_variant = bv.oneOf( ['release_speed', 'final'] )
    speed_build_variant.optimization          = 'speed'
    speed_build_variant.inlining              = 'full'
    speed_build_variant.whole_optimization    = 'on'
    speed_build_variant.debug_symbols         = 'off'
    speed_build_variant.runtime_debug         = 'off'
    
    size_build_variant = bv['release_size']
    size_build_variant.optimization       = 'size'
    size_build_variant.inlining           = 'on'
    size_build_variant.whole_optimization = 'on'
    size_build_variant.debug_symbols      = 'off'
    size_build_variant.runtime_debug      = 'off'

#//===========================================================================//

def     builtinOptions():
    
    options = Options()
    
    options.update( _build_options() )
    options.update( _target_options() )
    options.update( _optimization_options() )
    options.update( _code_gen_options() )
    options.update( _diagnostic_options() )
    options.update( _setup_options() )
    
    _init_defaults( options )
    
    return options
