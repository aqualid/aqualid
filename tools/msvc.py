import os
import re

import aql

from cpp_common import ToolCommonCpp, CommonCppCompiler, CommonCppArchiver, CommonCppLinker, \
                       ToolCommonRes, CommonResCompiler

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

class MsvcCompiler (CommonCppCompiler):
  
  def   __init__(self, options ):
    super(MsvcCompiler, self).__init__( options, shared = False )
    self.cmd += [ '/nologo', '/c', '/showIncludes' ]
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    sources = node.getSources()
    
    obj_file = self.getObjPath( sources[0] )
    cwd = obj_file.dirname()
    
    cmd = list(self.cmd)
    cmd += [ '/Fo%s' % obj_file ]
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
  
  def   getDefaultObjExt(self):
    return '.obj'
  
  #//-------------------------------------------------------//
  
  def   buildBatch( self, node ):
    
    source_values = node.getSourceValues()
    
    sources = tuple( src.get() for src in source_values )
    
    obj_files = self.getFileBuildPaths( sources, ext = self.ext )
    
    cwd = obj_files[0].dirname()
    
    cmd = list(self.cmd)
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

class MsvcResCompiler (CommonResCompiler):
  
  def   build( self, node ):
    
    src = node.getSources()[0]
    
    res_file = self.getObjPath( src )
    cwd = res_file.dirname()
    
    cmd = list(self.cmd)
    cmd += [ '/nologo', '/Fo%s' % res_file, src ]
    
    out = self.execCmd( cmd, cwd, file_flag = '@' )
    
    # deps = _parseRes( src )
    
    node.setFileTargets( res_file )
    
    return out
  
#//===========================================================================//

class   MsvcArchiver (CommonCppArchiver):
  
  def   makeCompiler( self, options ):
    return MsvcCompiler( options )
  
  def   makeResCompiler( self, options ):
    return MsvcResCompiler( options )
  
  def   build( self, node ):
    
    obj_files = node.getSources()
    
    cmd = list(self.cmd)
    cmd += [ '/nologo', "/OUT:%s" % self.target ]
    cmd += obj_files
    
    cwd = self.target.dirname()
    
    out = self.execCmd( cmd, cwd = cwd, file_flag = '@' )
    
    node.setFileTargets( self.target )
    
    return out

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class MsvcLinker (CommonCppLinker):
  
  def   makeCompiler( self, options ):
    return MsvcCompiler( options )
  
  def   makeResCompiler( self, options ):
    return MsvcResCompiler( options )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    obj_files = node.getSources()
    
    cmd = list(self.cmd)
    
    if self.shared:
      cmd.append( '/dll' )
      if self.def_file:
        cmd.append( '/DEF:%s' % self.def_file )
    
    target = self.target
    itargets = []
    
    if '/DEBUG' in cmd:
      pdb = target + '.pdb'
      cmd.append( "/PDB:%s" % (pdb,) )
      itargets.append( pdb )
      
    cmd += [ '/nologo', '/OUT:%s' % target ]
    
    cmd += obj_files
    
    cwd = target.dirname()
    
    out = self.execCmd( cmd, cwd = cwd, file_flag = '@' )
    
    node.setFileTargets( target, itargets )
    
    return out
  
  #//-------------------------------------------------------//

#//===========================================================================//
#// TOOL IMPLEMENTATION
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

class ToolMsvcCommon( ToolCommonCpp ):
  
  @classmethod
  def   setup( cls, options, env ):
    
    cl = aql.whereProgram( 'cl', env )
    link, lib, rc = aql.findOptionalPrograms( ['link', 'lib', 'rc' ], env )
    
    specs = _getMsvcSpecs( cl )
    
    options.update( specs )
    
    options.cc = cl
    options.link = link
    options.lib = lib
    options.rc = rc
  
  #//-------------------------------------------------------//
  
  def   __init__(self, options ):
    super(ToolMsvcCommon,self).__init__( options )
    
    options.env['INCLUDE']  = aql.ListOptionType( value_type = aql.PathOptionType(), separators = os.pathsep )
    options.env['LIB']      = aql.ListOptionType( value_type = aql.PathOptionType(), separators = os.pathsep )
    options.env['LIBPATH']  = aql.ListOptionType( value_type = aql.PathOptionType(), separators = os.pathsep )
    
    options.objsuffix     = '.obj'
    options.ressuffix     = '.res'
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
    
    options.linkflags += ['/INCREMENTAL:NO']
    
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
    
    if_.target_arch.eq( 'x86-32').libflags += '/MACHINE:X86'
    if_.target_arch.eq( 'x86-64').libflags += '/MACHINE:X64'
    if_.target_arch.eq( 'arm'   ).libflags += '/MACHINE:ARM'
    if_.target_arch.eq( 'arm64' ).libflags += '/MACHINE:ARM64'
    
    if_.target_arch.eq( 'x86-32').linkflags += '/MACHINE:X86'
    if_.target_arch.eq( 'x86-64').linkflags += '/MACHINE:X64'
    if_.target_arch.eq( 'arm'   ).linkflags += '/MACHINE:ARM'
    if_.target_arch.eq( 'arm64' ).linkflags += '/MACHINE:ARM64'
    
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
    if_.optimization.eq('speed').olinkflags += ['/OPT:REF','/OPT:ICF']

    if_.optimization.eq('size').occflags += '/Os'
    if_.optimization.eq('size').olinkflags += ['/OPT:REF','/OPT:ICF']

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
    
    if_.whole_optimization.isTrue().ccflags += '/GL'
    if_.whole_optimization.isTrue().linkflags += '/LTCG'
  
  #//-------------------------------------------------------//
  
  def   makeCompiler( self, options, shared ):
    return MsvcCompiler( options )
  
  def   makeResCompiler( self, options ):
    return MsvcResCompiler( options )
  
  def   makeArchiver( self, options, target, batch ):
    return MsvcArchiver( options, target, batch )
  
  def   makeLinker( self, options, target, shared, def_file, batch ):
    return MsvcLinker( options, target, shared = shared, def_file = def_file, batch = batch )
  
#//===========================================================================//

@aql.tool('c++', 'msvcpp','msvc++', 'cpp', 'cxx')
class ToolMsVCpp( ToolMsvcCommon ):
  language = "c++"

#//===========================================================================//

@aql.tool('c', 'msvc', 'cc')
class ToolMsvc( ToolMsvcCommon ):
  language = "c"

#//===========================================================================//

@aql.tool('rc', 'msrc')
class ToolMsrc( ToolCommonRes ):
  
  @classmethod
  def   setup( cls, options, env ):
    
    rc = aql.whereProgram( 'rc', env )
    options.target_os = 'windows'
    options.rc = rc
  
  def   __init__(self, options ):
    super(ToolMsrc,self).__init__( options )
    options.ressuffix   = '.res'
  
  def   makeResCompiler( self, options ):
    return MsvcResCompiler( options )
