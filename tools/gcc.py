import os
import re
import itertools

from aql import readTextFile, Tempfile, executeCommand, StrOptionType, ListOptionType, PathOptionType, tool 

from .cpp_common import  ToolCommonCpp, CommonCppCompiler, CommonCppArchiver, CommonCppLinker,\
                        ToolCommonRes, CommonResCompiler

#//===========================================================================//
#// BUILDERS IMPLEMENTATION
#//===========================================================================//

def   _readDeps( dep_file, exclude_dirs, _space_splitter_re = re.compile(r'(?<!\\)\s+') ):
  
  deps = readTextFile( dep_file )
  
  dep_files = []
  
  target_sep = ': '
  target_sep_len = len(target_sep)
  
  for line in deps.splitlines():
    pos = line.find( target_sep )
    if pos >= 0:
      line = line[ pos + target_sep_len: ]
    
    line = line.rstrip('\\ ').strip()
    
    tmp_dep_files = _space_splitter_re.split( line )
    tmp_dep_files = [dep_file.replace('\\ ', ' ') for dep_file in tmp_dep_files if dep_file]
    
    dep_files += map( os.path.abspath, tmp_dep_files )
  
  dep_files = iter(dep_files)
  next( dep_files ) # skip the source file
  
  dep_files = tuple( dep_file for dep_file in dep_files if not dep_file.startswith( exclude_dirs ) )
  
  return dep_files

#//===========================================================================//

# t.c:3:10: error: called object is not a function or function pointer
# t.c:1:17: note: declared here
#  void foo(char **p, char **q)

def   _parseOutput( output,
                    _err_re = re.compile( r"(.+):\d+:\d+:\s+error:\s+") ):

  failed_sources = set()
  
  for line in output.split('\n'):
    m = _err_re.match( line )
    if m:
      source_path = m.group(1)
      failed_sources.add( source_path ) 
  
  return failed_sources

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class GccCompiler (CommonCppCompiler):
  
  def   __init__(self, options ):
    super(GccCompiler, self).__init__( options )
    self.cmd += ['-c', '-MMD']
  
  def   build( self, node ):
    sources = node.getSources()
    
    obj_file = self.getObjPath( sources[0] )
    
    cwd = os.path.dirname( obj_file )
    
    with Tempfile( prefix = obj_file, suffix = '.d', dir = cwd ) as dep_file:
      
      cmd = list(self.cmd)
      
      cmd += ['-o', obj_file, '-MF', dep_file]
      cmd += sources
      
      out = self.execCmd( cmd, cwd, file_flag = '@' )
      
      node.addTargets( obj_file, implicit_deps = _readDeps( dep_file, self.ext_cpppath ) )
      
      return out

  #//-------------------------------------------------------//
  
  def   getDefaultObjExt(self):
    return '.o'
  
  #//-------------------------------------------------------//
  
  def   _setTargets( self, node, obj_files, output ):
    source_values = node.getSourceEntities()
    
    failed_sources = _parseOutput( output )
    
    for src_value, obj_file in zip( source_values, obj_files ):
      if src_value.get() not in failed_sources:
        dep_file = os.path.splitext( obj_file )[0] + '.d'
        implicit_deps = _readDeps( dep_file, self.ext_cpppath )
        
        node.addSourceTargets( src_value, obj_file, implicit_deps = implicit_deps )
  
  #//-------------------------------------------------------//
  
  def   buildBatch( self, node ):
    
    sources = node.getSources()
    
    obj_files = self.getTargetsFromSourceFilePaths( sources, ext = self.ext )
    
    cwd = os.path.dirname( obj_files[0] )
    
    cmd = list(self.cmd)
    cmd += sources
    
    result = self.execCmdResult( cmd, cwd, file_flag = '@' )
    
    output = result.output
    self._setTargets( node, obj_files, output )
    
    if result.failed():
      raise result
    
    return output

#//===========================================================================//

class GccResCompiler (CommonResCompiler):
  
  def   build( self, node ):
    
    src = node.getSources()[0]
    
    res_file = self.getObjPath( src )
    cwd = os.path.dirname( res_file )
    
    cmd = list(self.cmd)
    cmd += [ '-o', res_file, '-i', src ]
    
    out = self.execCmd( cmd, cwd, file_flag = '@' )
    
    # deps = _parseRes( src )
    
    node.addTargets( res_file )
    
    return out

#//===========================================================================//

class GccCompilerMaker (object):
  def   makeCompiler( self, options ):
    return GccCompiler( options )
  
  def   makeResCompiler( self, options ):
    return GccResCompiler( options )

#//===========================================================================//

class GccArchiver (GccCompilerMaker, CommonCppArchiver ):
  
  def   build( self, node ):
    
    cmd = list(self.cmd)
    cmd.append( self.target )
    cmd += node.getSources()
    
    cwd = os.path.dirname( self.target )
    
    out = self.execCmd( cmd, cwd = cwd, file_flag = '@' )
    
    node.addTargets( self.target )
    
    return out

#//===========================================================================//

class GccLinker( GccCompilerMaker, CommonCppLinker ):
  
  def   __init__( self, options, target, shared ):
    super(GccLinker, self).__init__( options, target, shared )
    
    self.is_windows = options.target_os == 'windows'
    self.libsuffix = options.libsuffix.get()
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    target = self.target
    import_lib = None
    shared = self.shared
    
    cmd = list(self.cmd)
    
    obj_files = node.getSources()
    
    cmd[2:2] = obj_files
    
    if shared:
      cmd.append( '-shared' )
      
      if self.is_windows:
        import_lib = os.path.splitext( target )[0] + self.libsuffix
        cmd.append( '-Wl,--out-implib,%s' % import_lib )
          
    cmd += [ '-o', target ]
    
    cwd = os.path.dirname( target )
    
    out = self.execCmd( cmd, cwd = cwd, file_flag = '@' )
    
    if shared:
      if import_lib:
        tags = ('shlib',)
        node.addTargets( import_lib, tags = ('implib',) )
      else:
        tags = ('shlib', 'implib')
    else:
      tags = None

    node.addTargets( target, tags = tags )
    
    return out

#//===========================================================================//
#// TOOL IMPLEMENTATION
#//===========================================================================//

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

def   _getTargetOs( target_os ):
  for target in target_os.split('-'):
    for prefix in _OS_PREFIXES:
      if target.startswith( prefix ):
        name = _OS_NAMES.get( prefix, prefix )
        return name
  
  return target_os

#//===========================================================================//

def   _getGccSpecs( gcc ):
  result = executeCommand( [gcc, '-v'] )
  
  target_re = re.compile( r'^\s*Target:\s+(.+)$', re.MULTILINE )
  version_re = re.compile( r'^\s*gcc version\s+(.+)$', re.MULTILINE )
  
  out = result.output
  
  match = target_re.search( out )
  target = match.group(1).strip() if match else ''
  
  match = version_re.search( out )
  version = match.group(1).strip() if match else ''
  
  target_list = target.split('-', 1)
  
  target_os = target_list[1]
  if len(target_list) > 1:
    target_arch = target_list[0]
  else:
    target_arch = 'unknown'
  
  target_os = _getTargetOs( target_os )
  
  specs = {
    'cc_name':      'gcc',
    'cc_ver':       version,
    'target_os':    target_os,
    'target_arch':  target_arch,
  }
  
  return specs

#//===========================================================================//

def   _generateProgNames( prog, prefix, suffix ):
  prefixes = [prefix, ''] if prefix else ['']
  suffixes = [suffix, '' ] if suffix else ['']
  
  return tuple( prefix + prog + suffix for prefix, suffix in itertools.product( prefixes, suffixes ) )

#//===========================================================================//

class ToolGccCommon( ToolCommonCpp ):
  
  @classmethod
  def   setup( cls, options ):
    
    if options.cc_name.isSetNotTo('gcc'):
      raise NotImplementedError()
    
    gcc_prefix = options.gcc_prefix.get()
    gcc_suffix = options.gcc_suffix.get()
    
    if cls.language == 'c':
      cc = "gcc"
    else:
      cc = "g++"
    
    gcc = cls.findProgram( options, gcc_prefix + cc + gcc_suffix )
    
    specs = _getGccSpecs( gcc )
    
    options.update( specs )
    
    options.cc = gcc
    options.link = gcc
    
    ar = _generateProgNames( 'ar', gcc_prefix, gcc_suffix )
    rc = _generateProgNames( 'windres', gcc_prefix, gcc_suffix )
    
    lib, rc = cls.findOptionalPrograms( options, [ar, rc], gcc )
    
    options.lib = lib
    options.rc = rc
  
  #//-------------------------------------------------------//
  
  @classmethod
  def   options( cls ):
    options = super(ToolGccCommon, cls).options()
    
    options.gcc_prefix  = StrOptionType( description = "GCC C/C++ compiler prefix" )
    options.gcc_suffix  = StrOptionType( description = "GCC C/C++ compiler suffix" )
    
    return options
  
  #//-------------------------------------------------------//
  
  def   __init__(self, options ):
    super(ToolGccCommon,self).__init__( options )
    
    options.env['CPATH']  = ListOptionType( value_type = PathOptionType(), separators = os.pathsep )
    if self.language == 'c':
      options.env['C_INCLUDE_PATH'] = ListOptionType( value_type = PathOptionType(), separators = os.pathsep )
    else:
      options.env['CPLUS_INCLUDE_PATH'] = ListOptionType( value_type = PathOptionType(), separators = os.pathsep )
    
    options.env['LIBRARY_PATH'] = ListOptionType( value_type = PathOptionType(), separators = os.pathsep )
    
    if_ = options.If()
    if_windows = if_.target_os.eq('windows')
    
    options.objsuffix     = '.o'
    options.ressuffix     = options.objsuffix
    options.libprefix     = 'lib'
    options.libsuffix     = '.a'
    options.shlibprefix   = 'lib'
    options.shlibsuffix   = '.so'
    if_windows.shlibprefix = ''
    if_windows.shlibsuffix = '.dll'
    if_windows.progsuffix = '.exe'
    
    options.cpppath_prefix    = '-I '
    options.libpath_prefix    = '-L '
    options.cppdefines_prefix = '-D '
    options.libs_prefix = '-l'
    options.libs_suffix = ''

    options.ccflags   += ['-pipe', '-x', self.language ]
    options.libflags  += ['-rcs']
    options.linkflags += ['-pipe']
    
    options.language = self.language
    
    if_.rtti.isTrue().cxxflags   += '-frtti'
    if_.rtti.isFalse().cxxflags  += '-fno-rtti'
    
    if_.exceptions.isTrue().cxxflags   += '-fexceptions'
    if_.exceptions.isFalse().cxxflags  += '-fno-exceptions'
    
    if_windows.target_subsystem.eq('console').linkflags += '-Wl,--subsystem,console'
    if_windows.target_subsystem.eq('windows').linkflags += '-Wl,--subsystem,windows'
    
    if_.debug_symbols.isTrue().ccflags += '-g'
    if_.debug_symbols.isFalse().linkflags += '-Wl,--strip-all'
    
    if_.runtime_link.eq('static').linkflags += '-static-libgcc'
    if_.runtime_link.eq('shared').linkflags += '-shared-libgcc'
    
    if_.target_os.eq('windows').runtime_thread.eq('multi').ccflags += '-mthreads'
    if_.target_os.ne('windows').runtime_thread.eq('multi').ccflags += '-pthreads'
    
    if_.optimization.eq('speed').occflags += '-Ofast'
    if_.optimization.eq('size').occflags  += '-Os'
    if_.optimization.eq('off').occflags   += '-O0'
    
    if_.inlining.eq('off').occflags   += '-fno-inline'
    if_.inlining.eq('on').occflags    += '-finline'
    if_.inlining.eq('full').occflags  += '-finline-functions'
    
    if_.warning_level.eq(0).ccflags += '-w'
    if_.warning_level.eq(3).ccflags += '-Wall'
    if_.warning_level.eq(4).ccflags += ['-Wall', '-Wextra', '-Wfloat-equal', '-Wundef', '-Wshadow', '-Wredundant-decls']
    
    if_.warning_as_error.isTrue().ccflags += '-Werror'
    
    if_profiling_true = if_.profile.isTrue()
    if_profiling_true.ccflags += '-pg'
    if_profiling_true.linkflags += '-pg'
    
    if_cxxstd = if_.cxxstd
    
    if_cxx11 = if_cxxstd.eq('c++11')
    if_cxx14 = if_cxxstd.eq('c++14')
    
    if_cxxstd.eq('c++98').cxxflags  += '-std=c++98'
    if_cxx11.cc_ver.ge("4.7").cxxflags += '-std=c++11'
    if_cxx11.cc_ver.ge("4.3").cc_ver.le("4.6").cxxflags += '-std=c++0x'
    if_cxx14.cc_ver.ge("4.8").cxxflags += '-std=c++1y'
    
    if_.pic.isTrue().target_os.notIn(['windows', 'cygwin'] ).ccflags += '-fPIC'
  
  #//-------------------------------------------------------//
  
  def   Compile( self, options ):
    return GccCompiler( options )
  
  def   CompileResource( self, options ):
    return GccResCompiler( options )
  
  def   LinkStaticLibrary( self, options, target ):
    return GccArchiver( options, target )
  
  def   LinkSharedLibrary( self, options, target, def_file = None ):
    return GccLinker( options, target, shared = True )
  
  def   LinkProgram( self, options, target ):
    return GccLinker( options, target, shared = False )

#//===========================================================================//

@tool('c++', 'g++', 'gxx', 'cpp', 'cxx')
class ToolGxx( ToolGccCommon ):
  language = "c++"

#//===========================================================================//

@tool('c', 'gcc', 'cc')
class ToolGcc( ToolGccCommon ):
  language = "c"

#//===========================================================================//

@tool('rc', 'windres')
class ToolWindRes( ToolCommonRes ):
  
  #//-------------------------------------------------------//
  
  @classmethod
  def   options( cls ):
    options = super(ToolWindRes, cls).options()
    
    options.gcc_prefix = StrOptionType( description = "GCC C/C++ compiler prefix" )
    options.gcc_suffix = StrOptionType( description = "GCC C/C++ compiler suffix" )
    
    return options
  
  #//-------------------------------------------------------//
  
  @classmethod
  def   setup( cls, options ):
    
    gcc_prefix = options.gcc_prefix.get()
    gcc_suffix = options.gcc_suffix.get()
    
    rc = _generateProgNames( 'windres', gcc_prefix, gcc_suffix )
    
    rc = cls.findProgram( options, rc )
    options.target_os = 'windows'
    options.rc = rc
  
  def   __init__(self, options ):
    super(ToolWindRes,self).__init__( options )
    options.ressuffix = '.o'
      
  def   Compile( self, options ):
    return GccResCompiler( options )
