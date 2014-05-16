import os
import re

import aql

from cpp_common import ToolCppCommon, CppCommonCompiler, CppCommonArchiver, CppCommonLinker 

#//===========================================================================//

class   ErrorDifferentSourceDirs( Exception ):
  def   __init__( self, src_dir1, src_dir2 ):
    msg = "Can't build batch sources from different dirs: %s, %s" % (src_dir1, src_dir2)
    super(ErrorDifferentSourceDirs, self).__init__( msg )

#//===========================================================================//
#// BUILDERS IMPLEMENTATION
#//===========================================================================//

def   _parseOutput( source_paths, output, exclude_dirs ):

  include_prefix = "Note: including file:"
  results = []

  names = iter(map( os.path.basename, source_paths ))
  sources = iter( source_paths )

  next_name = next( names, None )

  current_file = None
  filtered_output = []
  current_deps = []

  for line in output.split('\n'):
    if line == next_name:
      if current_file is not None:
        results.append( current_deps )
      
      current_file = next( sources, None )
      current_deps = []

      next_name = next( names, None )

    elif line.startswith( include_prefix ):
      dep_file = line[ len(include_prefix): ].strip()
      dep_file = os.path.normcase( os.path.abspath( dep_file ) )
      if not dep_file.startswith( exclude_dirs ):
        current_deps.append( dep_file )
    
    else:
      filtered_output.append( line )
  
  output = '\n'.join( filtered_output )
  results.append( current_deps )
  
  return results, output

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class MsvcCompiler (CppCommonCompiler):
  
  def   build( self, node ):
    
    sources = node.getSources()
    
    obj_files = self.getTargets( sources )
    obj_file = obj_files[0]
    cwd = os.path.dirname( obj_file )
    
    cmd = list(self.cmd)
    cmd += [ '/c', '/showIncludes', '/Fo%s' % obj_file ]
    cmd += sources
    
    try:
      out = self.execCmd( cmd, cwd, file_flag = '@' )
    except aql.ExecCommandResult as ex:
      deps, out = _parseOutput( sources, ex.out, self.ext_cpppath )
      raise aql.ExecCommandResult( cmd, returncode = ex.returncode, out = out )
    
    deps, out = _parseOutput( sources, out, self.ext_cpppath )
    
    node.setFileTargets( obj_file, ideps = deps[0] )
    
    return out
  
  #//-------------------------------------------------------//
  def   getTargets( self, sources ):
    obj_files = []
    cwd = None
    for src in sources:
      obj_file = self.getBuildPath( src ).change( prefix = self.prefix, ext = self.suffix )
      obj_cwd = obj_file.dirname()
      if cwd is None:
        cwd = obj_cwd
      elif cwd != obj_cwd:
        raise ErrorDifferentSourceDirs( cwd, obj_cwd )
      
      obj_files.append( obj_file )
    
    return obj_files 
  
  #//-------------------------------------------------------//
  
  def   buildBatch( self, node ):
    
    source_values = node.getSourceValues()
    
    sources = tuple( src.get() for src in source_values )
    
    obj_files = self.getTargets( sources )
    
    cwd = obj_files[0].dirname()
    
    cmd = list(self.cmd)
    cmd += [ '/c', '/showIncludes' ]
    cmd += sources
    
    try:
      out = self.execCmd( cmd, cwd, file_flag = '@' )
    except aql.ExecCommandResult as ex:
      deps, out = _parseOutput( sources, ex.out, self.ext_cpppath )
      raise aql.ExecCommandResult( cmd, returncode = ex.returncode, out = out )
    
    deps, out = _parseOutput( sources, out, self.ext_cpppath )
    
    for src_value, obj_file, deps in zip( source_values, obj_files, deps ):
      node.setSourceTargets( src_value, obj_file, ideps = deps )

    return out
  
#//===========================================================================//

#noinspection PyAttributeOutsideInit
class MsvcArchiver(CppCommonArchiver):
  
  def   makeCompiler( self, options ):
    return MsvcCompiler( options, shared = False )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    obj_files = self.getSources( node )
    
    cmd = list(self.cmd)
    cmd.append( "/OUT:%s" % self.target )
    cmd += obj_files
    
    cwd = self.target.dirname()
    
    out = self.execCmd( cmd, cwd = cwd, file_flag = '@' )
    
    node.setFileTargets( self.target )
    
    return out

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class MsvcLinker(CppCommonLinker):
  
  def   makeCompiler( self, options ):
    return MsvcCompiler( options, shared = False )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    obj_files = self.getSources( node )
    
    cmd = list(self.cmd)
    
    if self.shared:
      cmd.append( '/dll' )
    
    target = self.target
    itargets = []
    
    if '/DEBUG' in cmd:
      pdb = target + '.pdb'
      cmd.append( "/PDB:%s" % (pdb,) )
      itargets.append( pdb )
      
    cmd += [ '/OUT:%s' % target ]
    cmd += obj_files
    
    cwd = target.dirname()
    
    out = self.execCmd( cmd, cwd = cwd, file_flag = '@' )
    
    node.setFileTargets( target, itargets )
    
    return out
  
  #//-------------------------------------------------------//

#//===========================================================================//
#// TOOL IMPLEMENTATION
#//===========================================================================//

def   _findMsvc( env ):
  cl = aql.whereProgram( 'cl', env )
  link = aql.whereProgram( 'link', env )
  lib = aql.whereProgram( 'lib', env )

  return cl, link, lib

#//===========================================================================//

def _getMsvcSpecs( cl ):

  result = aql.executeCommand( cl )

  specs_re = re.compile( r'Compiler Version (?P<version>[0-9.]+) for (?P<machine>[a-zA-Z0-9_-]+)', re.MULTILINE )

  out = result.out
  
  match = specs_re.search( out )
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

#//===========================================================================//

class ToolMsvcCommon( ToolCppCommon ):
  
  @staticmethod
  def   setup( options, env ):
    
    cl, link, lib = _findMsvc( env )
    specs = _getMsvcSpecs( cl )
    
    options.update( specs )
    
    options.cc = cl
    options.link = link
    options.lib = lib
  
  def   __init__(self, options ):
    super(ToolMsvcCommon,self).__init__( options )
    
    options.env['INCLUDE']  = aql.ListOptionType( value_type = aql.PathOptionType(), separators = os.pathsep )
    options.env['LIB']      = aql.ListOptionType( value_type = aql.PathOptionType(), separators = os.pathsep )
    options.env['LIBPATH']  = aql.ListOptionType( value_type = aql.PathOptionType(), separators = os.pathsep )
    
    options.objsuffix     = '.obj'
    options.libprefix     = ''
    options.libsuffix     = '.lib'
    options.shlibprefix   = ''
    options.shlibsuffix   = '.dll'
    options.progsuffix    = '.exe'
    
    options.cpppath_prefix    = '/I '
    options.libpath_prefix    = '/LIBPATH:'
    options.cppdefines_prefix = '/D'
    options.libs_prefix = ''
    options.libs_suffix = '.lib'
    
    options.ccflags   += ['/nologo']
    options.libflags  += ['/nologo']
    options.linkflags += ['/nologo', '/INCREMENTAL:NO']
    
    options.sys_cpppath = options.env['INCLUDE']
    
    if_ = options.If()
    
    options.language = self.language
    
    options.cflags    += '/TC'
    options.cxxflags  += '/TP'
    
    if_.rtti.isTrue().cxxflags  += '/GR'
    if_.rtti.isFalse().cxxflags += '/GR-'

    if_.exceptions.isTrue().cxxflags  += '/EHsc'
    if_.exceptions.isFalse().cxxflags += ['/EHs-', '/EHc-']
    
    if_.target_subsystem.eq('console').linkflags += '/SUBSYSTEM:CONSOLE'
    if_.target_subsystem.eq('windows').linkflags += '/SUBSYSTEM:WINDOWS'
    
    if_.debug_symbols.isTrue().ccflags += '/Z7'
    if_.debug_symbols.isTrue().linkflags += '/DEBUG'
    
    if_runtime_link = if_.runtime_link
    
    if_runtime_link.eq('shared').runtime_debug.isFalse().ccflags += '/MD'
    if_runtime_link.eq('shared').runtime_debug.isTrue().ccflags += '/MDd'
    if_runtime_link.eq('static').runtime_debug.isFalse().runtime_thread.eq('single').ccflags += '/ML'
    if_runtime_link.eq('static').runtime_debug.isFalse().runtime_thread.eq('multi' ).ccflags += '/MT'
    if_runtime_link.eq('static').runtime_debug.isTrue().runtime_thread.eq('single').ccflags += '/MLd'
    if_runtime_link.eq('static').runtime_debug.isTrue().runtime_thread.eq('multi' ).ccflags += '/MTd'

    # if_.cc_ver.ge(7).cc_ver.lt(8).ccflags += '/Zc:forScope /Zc:wchar_t'

    if_.optimization.eq('speed').occflags += '/Ox'
    if_.optimization.eq('speed').olinkflags += '/OPT:REF /OPT:ICF'

    if_.optimization.eq('size').occflags += '/Os'
    if_.optimization.eq('size').olinkflags += '/OPT:REF /OPT:ICF'

    if_.optimization.eq('off').occflags += '/Od'

    if_.inlining.eq('off' ).occflags += '/Ob0'
    if_.inlining.eq('on'  ).occflags += '/Ob1'
    if_.inlining.eq('full').occflags += '/Ob2'

    if_warning_level = if_.warning_level
    
    if_warning_level.eq(0).ccflags += '/w'
    if_warning_level.eq(1).ccflags += '/W1'
    if_warning_level.eq(2).ccflags += '/W2'
    if_warning_level.eq(3).ccflags += '/W3'
    if_warning_level.eq(4).ccflags += '/W4'

    if_.warnings_as_errors.isTrue().ccflags += '/WX'
    if_.warnings_as_errors.isTrue().linkflags += '/WX'
  
  #//-------------------------------------------------------//
  
  def   makeCompiler( self, options, shared ):
    return MsvcCompiler( options, shared = False )
  
  def   makeArchiver( self, options, target ):
    return MsvcArchiver( options, target )
  
  def   makeLinker( self, options, target, shared ):
    return MsvcLinker( options, target, shared = shared )

#//===========================================================================//

@aql.tool('c++', 'msvcpp','msvc++', 'cpp', 'cxx')
class ToolMsvcpp( ToolMsvcCommon ):
  language = "c++"

#//===========================================================================//

@aql.tool('c', 'msvc', 'cc')
class ToolMsvc( ToolMsvcCommon ):
  language = "c"
