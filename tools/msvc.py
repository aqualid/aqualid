import os
import re
import itertools

import aql

from .cpp_common import ToolCppCommon, CppCommonCompiler, CppCommonArchiver, CppCommonLinker 

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
  current_output = []
  current_deps = []

  for line in output.split('\n'):
    if line == next_name:
      if current_file is not None:
        current_output = '\n'.join( current_output )
        results.append( ( current_file, current_deps, current_output ) )
      
      current_file = next( sources, None )
      current_deps = []
      current_output = []

      next_name = next( names, None )

    elif line.startswith( include_prefix ):
      dep_file = line[ len(include_prefix): ].strip()
      dep_file = os.path.normcase( os.path.abspath( dep_file ) )
      if not dep_file.startswith( exclude_dirs ):
        current_deps.append( dep_file )
    
    else:
      current_output.append( line )
  
  current_output = '\n'.join( current_output )
  results.append( ( current_file, current_deps, current_output ) )

  return results

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class MsvcCompiler (CppCommonCompiler):
  
  def   __init__(self, options, language, shared ):
    super( MsvcCompiler, self).__init__( options, language, shared, ['INCLUDE'] )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    sources = node.getSources()
    
    obj_files = self.getTargets( sources )
    obj_file = obj_files[0]
    cwd = os.path.dirname( obj_file )
    
    cmd = list(self.cmd)
    cmd += ['/Fo%s' % obj_file ]
    cmd += sources
    
    out = self.execCmd( cmd, cwd, file_flag = '@' )
    
    outs = _parseOutput( sources, out, self.ext_cpppath )
    
    source, deps, out = outs[0]
    
    node.setFileTargets( obj_file, ideps = deps )

    return out
  
#//===========================================================================//

#noinspection PyAttributeOutsideInit
class MsvcArchiver(CppCommonArchiver):
  
  #//-------------------------------------------------------//
  
  def setCmd(self, options, language, shared ):
    self.cmd = [ options.lib.get(), '/nologo' ]
    self.cmd += options.libflags.get()
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    obj_files = tuple( src.get() for src in self.getSources( node ) )
    
    cmd = list(self.cmd)
    cmd.append( "/OUT:%s" % self.target )
    cmd += obj_files
    
    cwd = self.target.dirname()
    
    out = self.execCmd( cmd, cwd = cwd, file_flag = '@' )
    
    node.setFileTargets( self.target )
    
    return out

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class MsvcLinker(MsvcLinkerBase):
  
  def   __init__( self, options, target, language, shared ):
    if shared:
      prefix = options.shlibprefix.get() + options.prefix.get()
      suffix = options.shlibsuffix.get()
    else:
      prefix = options.prefix.get()
      suffix = options.progsuffix.get()
    
    self.target = self.getBuildPath( target ).change( prefix = prefix, ext = suffix )
    
    self.cmd = self.__getCmd( options, self.target, language, shared )
    self.language = language
    
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __getCmd( options, target, language, shared ):
    
    cmd = [ options.link.get(), '/nologo' ]

    if shared:
      cmd += [ '/dll' ]
    
    cmd += options.linkflags.get()
    cmd += ('/LIBPATH:%s' % path for path in options.libpath.get() )
    cmd += options.libs.get()
    
    return cmd
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    obj_files = tuple( src.get() for src in node.builder_data )
    
    cmd = list(self.cmd)
    
    cmd[2:2] = obj_files
    
    cmd += [ '/OUT:%s' % self.target ]
    
    cwd = self.target.dirname()
    
    out = self.execCmd( cmd, cwd = cwd, file_flag = '@' )
    
    node.setFileTargets( self.target )
    
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
    options.cxx = cl
    options.link = link
    options.lib = lib
    
    options.If().cc_name.isTrue().build_dir_name += '_' + options.cc_name + '_' + options.cc_ver
    
  #//-------------------------------------------------------//
  
  @staticmethod
  def   options():
    options = super( ToolMsvcCommon ).options()
    
    if_ = options.If()
    
    options.objsuffix     = '.obj'
    options.libprefix     = ''
    options.libsuffix     = '.a'
    options.shlibprefix   = ''
    options.shlibsuffix   = '.dll'
    options.progsuffix    = '.exe'
    
    options.cpppath_flag    = '/I '
    options.cppdefines_flag = '/D'
    
    options.ccflags += ['/nologo', '/c', '/showIncludes']
    options.cxxflags += ['/TP']
    options.cflags += ['/TC']
    
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

    if_.rtti.isTrue().cxxflags  += '/GR'
    if_.rtti.isFalse().cxxflags += '/GR-'

    if_.exceptions.isTrue().cxxflags  += '/EHsc'
    if_.exceptions.isFalse().cxxflags += '/EHs- /EHc-'
    
    if_warning_level = if_.warning_level
    
    if_warning_level.eq(0).ccflags += '/w'
    if_warning_level.eq(1).ccflags += '/W1'
    if_warning_level.eq(2).ccflags += '/W2'
    if_warning_level.eq(3).ccflags += '/W3'
    if_warning_level.eq(4).ccflags += '/W4'

    if_.warnings_as_errors.isTrue().ccflags += '/WX'
    if_.warnings_as_errors.isTrue().linkflags += '/WX'
    
    if_.linkflags += '/INCREMENTAL:NO'
    
    return options
  
  #//-------------------------------------------------------//
  
  def   makeCompiler( self, options, shared ):
    return MsvcCompiler( options, self.language )
  
  def   makeArchiver( self, options, target ):
    return MsvcArchiver( options, target, self.language )
  
  def   makeLinker( self, options, target, shared ):
    return MsvcLinker( options, target, self.language, shared = shared )

#//===========================================================================//

@aql.tool('c++', 'msvcpp', 'cpp', 'cxx')
class ToolMsvcpp( ToolMsvcCommon ):
  language = "c++"

#//===========================================================================//

@aql.tool('c', 'msvc', 'cc')
class ToolMsvc( ToolMsvcCommon ):
  language = "c"
