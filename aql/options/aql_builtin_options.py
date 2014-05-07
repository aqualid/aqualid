#
# Copyright (c) 2012-2014 The developers of Aqualid project - http://aqualid.googlecode.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__all__ = (
  'builtinOptions',
)

import os

from aql.util_types import IgnoreCaseString, UpperCaseString

from .aql_options import Options
from .aql_option_value import SimpleOperation

from .aql_option_types import BoolOptionType, EnumOptionType, RangeOptionType, ListOptionType, DictOptionType, \
                              PathOptionType, StrOptionType, VersionOptionType

#//===========================================================================//

def   _build_options():
  options = Options()
  
  options.build_path            = PathOptionType( description = "The building directory full path." )
  options.build_dir             = PathOptionType( description = "The building directory." )
  options.relative_build_paths  = BoolOptionType( description = "The building directory suffix.", default = True )
  options.build_dir_name        = StrOptionType( description  = "The building directory name." )
  options.prefix                = StrOptionType( description  = "Output files prefix." )
  options.suffix                = StrOptionType( description  = "Output files suffix." )
  
  build_variant = EnumOptionType( values =  [
                                              ('debug', 'dbg', 'd' ),
                                              ('release_speed', 'release', 'rel', 'rs'),
                                              ('release_size', 'rz'),
                                              ('final', 'f'),
                                            ],
                                  default = 'debug',
                                  description = "Current build variant" )
  
  options.build_variant = build_variant
  options.bv = options.build_variant
  
  options.build_variants = ListOptionType( value_type = build_variant, unique = True,
                                           description = "Active build variants" )
  options.bvs = options.build_variants
  
  
  #//-------------------------------------------------------//
  
  file_signature = EnumOptionType(  values =  [('checksum', 'md5', 'sign'), ('timestamp', 'time')],
                                    default = 'checksum',
                                    description = "Type used to detect changes in dependency files" )
  
  options.file_signature = file_signature
  options.fcheck = options.file_signature
  
  #//-------------------------------------------------------//
  
  options.tools_path    = ListOptionType( value_type = PathOptionType(), unique = True, description = "Tools search path" )
  
  #//-------------------------------------------------------//
  
  options.setGroup( "Build" )
  
  return options

#//===========================================================================//

def   _target_options():
  options = Options()
  
  options.target_os = EnumOptionType( values = ['native', ('windows', 'win32', 'win64'), ('linux', 'linux-gnu'),
                                                'cygwin', 'darwin', 'java', 'sunos', 'hpux', 'elf'],
                                      default = 'native',
                                      is_tool_key = True,
                                      description = "The target system/OS name, e.g. 'Linux', 'Windows', or 'Java'." )
  
  options.target_arch = EnumOptionType( values = [ 'native',
                                                   ('x86-32', 'x86_32', 'x86', '80x86', 'i386', 'i486', 'i586', 'i686'),
                                                   ('x86-64','x86_64', 'amd64', 'x64'),
                                                   'arm',
                                                   'alpha',
                                                   'mips' ],
                                        default = 'native',
                                        is_tool_key = True,
                                        description = "The target machine type, e.g. 'i386'" )
  
  options.target_subsystem = EnumOptionType(  values = [ 'console', 'windows' ],
                                              default = 'console',
                                              description = "The target subsystem." )
  
  options.target_platform = StrOptionType(  ignore_case = True,
                                            description = "The target system's distribution, e.g. 'win32', 'Linux'" )
  
  options.target_os_release = StrOptionType(  ignore_case = True,
                                              description = "The target system's release, e.g. '2.2.0' or 'XP'" )
  
  options.target_os_version = VersionOptionType( description = "The target system's release version, e.g. '2.2.0' or '5.1.2600'" )
  
  options.target_cpu = StrOptionType( ignore_case = True,
                                      is_tool_key = True,
                                      description = "The target real processor name, e.g. 'amdk6'." )
  
  options.target_cpu_flags = ListOptionType( value_type = IgnoreCaseString,
                                             description = "The target CPU flags, e.g. 'mmx', 'sse2'." )
  
  options.setGroup( "Target system" )
  
  return options

#//===========================================================================//

def   _optimization_options():
  
  options = Options()
  
  options.optimization = EnumOptionType( values = [ ('off', 0), ('size', 1), ('speed', 2) ],
                                         default = 'off',
                                         description = 'Optimization level' )
  options.optlevel = options.optimization
  options.opt = options.optimization
  
  #//-------------------------------------------------------//
  
  options.inlining = EnumOptionType( values = ['off', 'on', 'full'],
                                     default = 'off',
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
  
  options.keep_asm = BoolOptionType( description = 'Keep generated assemblers files' )

  options.runtime_link = EnumOptionType( values = ['default', 'static', ('shared', 'dynamic') ],
                                         default = 'default',
                                         description = 'Linkage type of runtime library' )
  options.rt_link = options.runtime_link
  
  
  options.runtime_debug = BoolOptionType( description = 'Use debug version of runtime library' )
  options.rt_debug = options.runtime_debug

  options.rtti = BoolOptionType( description = 'Enable Run Time Type Information', default = True )
  options.exceptions = BoolOptionType( description = 'Allow to throw exceptions', default = True )

  options.runtime_thread = EnumOptionType( values = ['default', 'single', 'multi' ],
                                           default = 'default',
                                           description = 'Threading mode of runtime library' )
  options.rt_thread = options.runtime_thread
  
  options.setGroup( "Code generation" )
  return options

#//===========================================================================//

def     _diagnostic_options():
  
  options = Options()
  
  options.warning_level = RangeOptionType( 0, 4, description = 'Warning level', default = 4 )
  options.warn_level = options.warning_level
  
  options.warning_as_error = BoolOptionType( description = 'Treat warnings as errors' )
  options.werror = options.warning_as_error
  options.warnings_as_errors = options.warning_as_error

  options.lint = EnumOptionType( values = [('off', 0), ('on', 1), ('global',2)],
                                 default = 'off',
                                 description = 'Lint source code.' )
  
  options.lint_flags = ListOptionType( description = "Lint tool options" )
  
  options.setGroup( "Diagnostic" )
  return options

#//===========================================================================//

#noinspection PyUnresolvedReferences
def   _env_options():
  
  options = Options()
  options.env = DictOptionType( key_type = UpperCaseString )
  options.env['PATH'] = ListOptionType( value_type = PathOptionType(), separators = os.pathsep )
  options.env['TEMP'] = PathOptionType()
  options.env['TMP'] = PathOptionType()
  options.env['HOME'] = PathOptionType()
  options.env['HOMEPATH'] = PathOptionType()
  
  options.env = os.environ.copy()
  
  return options

#//===========================================================================//

def   _init_defaults( options ):
    
    #//-------------------------------------------------------//
    # build_dir_name set to <target OS>_<target arch>_<build variant>
    
    if_ = options.If()
    
    if_.target_os.ne('native').build_dir_name    += options.target_os + '_'
    if_.target_arch.ne('native').build_dir_name  += options.target_arch + '_'
    options.build_dir_name += options.build_variant
    
    options.build_path = SimpleOperation( os.path.join, options.build_dir, options.build_dir_name )
    
    #//-------------------------------------------------------//
    
    bv = if_.build_variant
    
    debug_build_variant = bv.eq('debug')
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
    
    size_build_variant = bv.eq('release_size')
    size_build_variant.optimization       = 'size'
    size_build_variant.inlining           = 'on'
    size_build_variant.whole_optimization = 'on'
    size_build_variant.debug_symbols      = 'off'
    size_build_variant.runtime_debug      = 'off'

#//===========================================================================//

def     builtinOptions():
    
    options = Options()
    
    options.merge( _build_options() )
    options.merge( _target_options() )
    options.merge( _optimization_options() )
    options.merge( _code_gen_options() )
    options.merge( _diagnostic_options() )
    options.merge( _env_options() )
    
    _init_defaults( options )
    
    return options
