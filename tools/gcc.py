import os
import re
import itertools

import aql

from cpp_common import ToolCppCommon, CppCommonCompiler, CppCommonArchiver, CppCommonLinker

#//===========================================================================//
#// BUILDERS IMPLEMENTATION
#//===========================================================================//

def   _readDeps( dep_file, exclude_dirs, _space_splitter_re = re.compile(r'(?<!\\)\s+') ):
  
  deps = aql.readTextFile( dep_file )
  
  dep_files = []
  
  target_sep = ': '
  target_sep_len = len(target_sep)
  
  for line in deps.splitlines():
    pos = line.find( target_sep )
    if pos >= 0:
      line = line[ pos + target_sep_len: ]
    
    line = line.rstrip('\\ ').strip()
    
    tmp_dep_files = filter( None, _space_splitter_re.split( line ) )
    tmp_dep_files = [dep_file.replace('\\ ', ' ') for dep_file in tmp_dep_files ]
    
    dep_files += map( os.path.abspath, tmp_dep_files )
  
  dep_files = iter(dep_files)
  next( dep_files ) # skip the source file
  
  dep_files = tuple( dep_file for dep_file in dep_files if not dep_file.startswith( exclude_dirs ) )
  
  return dep_files

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class GccCompiler (CppCommonCompiler):
  
  def   build( self, node ):
    
    sources = node.getSources()
    
    obj_files = self.getTargets( sources )
    obj_file = obj_files[0]
    cwd = obj_file.dirname()
    
    with aql.Tempfile( prefix = obj_file, suffix = '.d', dir = cwd ) as dep_file:
      
      cmd = list(self.cmd)
      if self.shared:
        cmd += ['-fPIC']
      
      cmd += ['-c', '-o', obj_file, '-MMD', '-MF', dep_file]
      cmd += sources
      
      out = self.execCmd( cmd, cwd, file_flag = '@' )
      
      node.setFileTargets( obj_file, ideps = _readDeps( dep_file, self.ext_cpppath ) )
      
      return out

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class GccArchiver(CppCommonArchiver):
  
  def   makeCompiler( self, options ):
    return GccCompiler( options, shared = False )
  
  #//=======================================================//
  
  def   build( self, node ):
    
    cmd = list(self.cmd)
    cmd.append( self.target )
    cmd += self.getSources( node )
    
    cwd = self.target.dirname()
    
    out = self.execCmd( cmd, cwd = cwd, file_flag = '@' )
    
    node.setFileTargets( self.target )
    
    return out

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class GccLinker(CppCommonLinker):
  
  def   makeCompiler( self, options ):
    return GccCompiler( options, shared = False )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    cmd = list(self.cmd)
    
    cmd[2:2] = self.getSources( node )
    
    if self.shared:
      cmd += [ '-shared' ]
    
    cmd += [ '-o', self.target ]
    
    cwd = self.target.dirname()
    
    out = self.execCmd( cmd, cwd = cwd, file_flag = '@' )
    
    node.setFileTargets( self.target )
    
    return out

#//===========================================================================//
#// TOOL IMPLEMENTATION
#//===========================================================================//

def   _checkProg( gcc_path, prog ):
  prog = os.path.join( gcc_path, prog )
  return prog if os.path.isfile( prog ) else None

#//===========================================================================//

def   _findGcc( env, gcc_prefix, gcc_suffix ):
  gcc = '%sgcc%s' % (gcc_prefix, gcc_suffix)
  gcc = aql.whereProgram( gcc, env )
  
  gxx = None
  ar = None
  
  gcc_ext = os.path.splitext( gcc )[1]
  
  gcc_prefixes = [gcc_prefix, ''] if gcc_prefix else ['']
  gcc_suffixes = [gcc_suffix + gcc_ext, gcc_ext ] if gcc_suffix else [gcc_ext]
  
  gcc_path = os.path.dirname( gcc )
  
  for gcc_prefix, gcc_suffix in itertools.product( gcc_prefixes, gcc_suffixes ):
    if not gxx: gxx = _checkProg( gcc_path, '%sg++%s' % (gcc_prefix, gcc_suffix) )
    if not gxx: gxx = _checkProg( gcc_path, '%sc++%s' % (gcc_prefix, gcc_suffix) )
    if not ar:  ar  = _checkProg( gcc_path, '%sar%s' % (gcc_prefix, gcc_suffix) )
  
  if not gxx or not ar:
    raise NotImplementedError()
  
  return gcc, gxx, ar

#//===========================================================================//

def   _getGccSpecs( gcc ):
  result = aql.executeCommand( [gcc, '-v'] )
  
  target_re = re.compile( r'^\s*Target:\s+(.+)$', re.MULTILINE )
  version_re = re.compile( r'^\s*gcc version\s+(.+)$', re.MULTILINE )
  
  out = result.out
  
  match = target_re.search( out )
  target = match.group(1).strip() if match else ''
  
  match = version_re.search( out )
  version = str(aql.Version( match.group(1).strip() if match else '' ))
  
  target_list = target.split('-', 2)
  
  target_os = target_list[-1]
  if len(target_list) > 1:
    target_arch = target_list[0]
  else:
    target_arch = 'native'
  
  if target_os.find('mingw32') != -1:
    target_os = 'windows'
  
  specs = {
    'cc_name':      'gcc',
    'cc_ver':       version,
    'target_os':    target_os,
    'target_arch':  target_arch,
  }
  
  return specs

#//===========================================================================//

class ToolGccCommon( ToolCppCommon ):
  
  @classmethod
  def   setup( cls, options, env ):
    
    gcc_prefix = options.gcc_prefix.get()
    gcc_suffix = options.gcc_suffix.get()
    
    gcc, gxx, ar = _findGcc( env, gcc_prefix, gcc_suffix )
    specs = _getGccSpecs( gcc )
    
    options.update( specs )
    
    if cls.language == 'c++':
      options.cc = gxx
      options.link = gxx
    else:
      options.cc = gcc
      options.link = gcc
    
    options.lib = ar
  
  #//-------------------------------------------------------//
  
  @classmethod
  def   options( cls ):
    options = super(ToolGccCommon, cls).options()
    
    options.gcc_path    = aql.PathOptionType()
    options.gcc_target  = aql.StrOptionType( ignore_case = True )
    options.gcc_prefix  = aql.StrOptionType( description = "GCC C/C++ compiler prefix" )
    options.gcc_suffix  = aql.StrOptionType( description = "GCC C/C++ compiler suffix" )
    
    return options
  
  #//-------------------------------------------------------//
  
  def   __init__(self, options ):
    super(ToolGccCommon,self).__init__( options )
    
    options.env['CPATH']  = aql.ListOptionType( value_type = aql.PathOptionType(), separators = os.pathsep )
    if self.language == 'c++':
      options.env['CPLUS_INCLUDE_PATH'] = aql.ListOptionType( value_type = aql.PathOptionType(), separators = os.pathsep )
    else:
      options.env['C_INCLUDE_PATH'] = aql.ListOptionType( value_type = aql.PathOptionType(), separators = os.pathsep )
    
    options.env['LIBRARY_PATH'] = aql.ListOptionType( value_type = aql.PathOptionType(), separators = os.pathsep )
    
    if_ = options.If()
    if_windows = if_.target_os.eq('windows')
    
    options.objsuffix     = '.o'
    options.shobjsuffix   = '.os'
    options.libprefix     = 'lib'
    options.libsuffix     = '.a'
    options.shlibprefix   = 'lib'
    options.shlibsuffix   = '.so'
    if_windows.progsuffix = '.exe'
    
    options.cpppath_flag    = '-I '
    options.libpath_flag    = '-L '
    options.cppdefines_flag = '-D '
    
    options.ccflags   = ['-pipe', '-x', self.language ]
    options.libflags  = ['-rcs']
    options.linkflags = ['-pipe']
    
    if self.language == 'c++':
      if_.rtti.isTrue().ccflags   += '-frtti'
      if_.rtti.isFalse().ccflags  += '-fno-rtti'
      
      if_.exceptions.isTrue().ccflags   += '-fexceptions'
      if_.exceptions.isFalse().ccflags  += '-fno-exceptions'
    
    if_windows.target_subsystem.eq('console').linkflags += '-Wl,--subsystem,console'
    if_windows.target_subsystem.eq('windows').linkflags += '-Wl,--subsystem,windows'
    
    if_.debug_symbols.isTrue().ccflags += '-g'
    if_.debug_symbols.isFalse().linkflags += '-Wl,--strip-all'
    
    if_.runtime_link.eq('static').linkflags += '-static-libgcc'
    if_.runtime_link.eq('shared').linkflags += '-shared-libgcc'
    
    if_.target_os.eq('windows').runtime_thread.eq('multi').ccflags += '-mthreads'
    if_.target_os.ne('windows').runtime_thread.eq('multi').ccflags += '-pthreads'
    
    if_.optimization.eq('speed').occflags += '-O3'
    if_.optimization.eq('size').occflags  += '-Os'
    if_.optimization.eq('off').occflags   += '-O0'
    
    if_.inlining.eq('off').occflags   += '-fno-inline'
    if_.inlining.eq('on').occflags    += '-finline'
    if_.inlining.eq('full').occflags  += '-finline-functions'
    
    if_.warning_as_error.isTrue().ccflags += '-Werror'
    
    if_profiling_true = if_.profile.isTrue()
    if_profiling_true.ccflags += '-pg'
    if_profiling_true.linkflags += '-pg'
    
  #//-------------------------------------------------------//
  
  def   makeCompiler( self, options, shared ):
    return GccCompiler( options, shared = shared )
  
  def   makeArchiver( self, options, target ):
    return GccArchiver( options, target )
  
  def   makeLinker( self, options, target, shared ):
    return GccLinker( options, target, shared = shared )

#//===========================================================================//

@aql.tool('c++', 'g++', 'cpp', 'cxx')
class ToolGxx( ToolGccCommon ):
  language = "c++"

#//===========================================================================//

@aql.tool('c', 'gcc', 'cc')
class ToolGcc( ToolGccCommon ):
  language = "c"
