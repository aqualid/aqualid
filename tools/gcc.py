import os
import re
import shutil
import hashlib

from aql_builder import Builder
from aql_utils import execCommand, readTextFile
from aql_path_types import FilePath, FilePaths
from aql_errors import InvalidSourceValueType, BuildError
from aql_options import Options
from aql_temp_file import Tempfile, Tempdir
from aql_option_types import OptionType, BoolOptionType, EnumOptionType, RangeOptionType, ListOptionType, PathOptionType, StrOptionType, VersionOptionType

#//===========================================================================//

def   _readDeps( dep_file, _space_splitter_re = re.compile(r'(?<!\\)\s+') ):
  
  deps = readTextFile( dep_file )
  
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
    
    dep_files += tmp_dep_files
  
  return dep_files[1:]  # skip the source file

#//===========================================================================//

def   _addPrefix( prefix, values ):
  return map( lambda v, prefix = prefix: prefix + v, values )

#//===========================================================================//

def   _cppCompilerOptions():
  
  options = Options()
  
  options.cc = PathOptionType( description = "C compiler program" )
  options.cxx = PathOptionType( description = "C++ compiler program" )
  options.cflags = ListOptionType( description = "C compiler options" )
  options.ccflags = ListOptionType( description = "Common C/C++ compiler options" )
  options.cxxflags = ListOptionType( description = "C++ compiler options" )
  
  options.ocflags = ListOptionType( description = "C compiler optimization options" )
  options.occflags = ListOptionType( description = "Common C/C++ compiler optimization options" )
  options.ocxxflags = ListOptionType( description = "C++ compiler optimization options" )
  
  options.cflags += options.ocflags
  options.ccflags += options.occflags
  options.cxxflags += options.ocxxflags
  
  options.cc_name = StrOptionType( ignore_case = True, description = "C/C++ compiler name" )
  options.cc_ver = VersionOptionType( description = "C/C++ compiler version" )
  
  options.cppdefines = ListOptionType( unique = True, description = "C/C++ preprocessor defines" )
  options.defines = options.cppdefines
  
  options.cpppath = ListOptionType( value_type = FilePath, unique = True, description = "C/C++ preprocessor paths to headers" )
  options.include = options.cpppath
  
  options.ext_cpppath = ListOptionType( value_type = FilePath, unique = True, description = "C/C++ preprocessor path to extenal headers" )
  
  options.no_rtti = BoolOptionType( description = 'Disable C++ realtime type information' )
  options.no_exceptions = BoolOptionType( description = 'Disable C++ exceptions' )
  
  return options

#//===========================================================================//

def   _linkerOptions():
  
  options = Options()
  
  options.linkflags = ListOptionType( description = "Linker options" )
  options.libflags = ListOptionType( description = "Archiver options" )
  
  options.olinkflags = ListOptionType( description = "Linker optimization options" )
  options.olibflags = ListOptionType( description = "Archiver optimization options" )
  
  options.linkflags += options.olinkflags
  options.libflags += options.olibflags
  
  options.libpath = ListOptionType( value_type = FilePath, unique = True, description = "Paths to extenal libraries" )
  options.libs = ListOptionType( value_type = FilePath, unique = True, description = "Linking extenal libraries" )
  
  return options

#//===========================================================================//

def   gccOptions():
  options = Options()
  
  options.gcc_path = PathOptionType()
  options.gcc_target = StrOptionType( ignore_case = True )
  options.gcc_prefix = StrOptionType( description = "GCC C/C++ compiler prefix" )
  options.gcc_suffix = StrOptionType( description = "GCC C/C++ compiler suffix" )
  
  options.update( _cppCompilerOptions() )
  options.update( _linkerOptions() )
  
  options.setGroup( "C/C++ compiler" )
  
  return options

#//===========================================================================//

def   execCmd( compiler, cl_options, cwd ):
  if len( args_str ) > 4096:
    cmd_file = Tempfile( suffix = '.cmd.args' )
    cl_options = cl_options.replace('\\', '/')
    cmd_file.write( cl_options )
    cmd_file.close()
    cmd = compiler +' @' + cmd_file.name
  else:
    cmd = compiler + ' ' + cl_options
    cmd_file = None
  
  try:
    result, out, err = execCommand( cmd, cwd = cwd, env = None, stdout = None, stderr = None )    # TODO: env = options.os_env
    if result:
      return BuildError( out, err )
  finally:
    if cmd_file is not None:
      cmd_file.remove()
  
  return None

#//===========================================================================//

class GccCompilerImpl (Builder):
  
  __slots__ = ('options', 'compiler', 'cl_options')
  
  def   __init__(self, options, language, scontent_type = NotImplemented, tcontent_type = NotImplemented ):
    
    self.options = options
    self.build_dir = options.build_dir.value()
    self.do_path_merge = options.do_build_path_merge.value()
    self.scontent_type = scontent_type
    self.tcontent_type = tcontent_type
    
    self.compiler, self.cl_options = self.__cmdOptions( language )
    self.signature = self.__signature()
  
  #//-------------------------------------------------------//
  
  def   __cmdOptions( self, language ):
    
    options = self.options
    
    cl_options = ['-c', '-pipe', '-MMD', '-x', language ]
    if language == 'c++':
      cl_options += options.cxxflags.value()
      compiler = options.cxx.value()
    else:
      cl_options += options.cflags.value()
      compiler = options.cc.value()
    
    cl_options += options.ccflags.value()
    cl_options += _addPrefix( '-D', options.cppdefines.value() )
    cl_options += _addPrefix( '-I', options.cpppath.value() )
    cl_options += _addPrefix( '-I', options.ext_cpppath.value() )
    
    return compiler, ' '.join( cl_options )
  
  #//-------------------------------------------------------//
  
  def   __signature( self ):
    values = ''.join( [ self.compiler, self.cl_options ] )
    return hashlib.md5( values.encode('utf-8') ).digest()
  
  #//-------------------------------------------------------//
  
  def   __buildOne( self, vfile, src_file_value ):
    with Tempfile( suffix = '.d' ) as dep_file:
      
      src_file = src_file_value.name
      
      args = [self.cl_options]
      
      args += [ '-MF', dep_file.name ]
      
      obj_file = self.buildPath( src_file ) + '.o'
      args += [ '-o', obj_file ]
      args += [ src_file ]
      
      args = ' '.join( map(str, cmd ) )
      
      cwd = self.buildPath()
      
      err = execCmd( self.cmd, args, cwd )
      if err: raise err
      
      return self.nodeTargets( obj_file, ideps = _readDeps( dep_file.name ) )
  
  #//===========================================================================//

  def   __buildMany( self, vfile, src_file_values, src_nodes ):
    
    targets = self.nodeTargets()
    
    build_dir = self.buildPath()
    
    src_files = FilePaths( src_file_values )
    
    with Tempdir( dir = build_dir ) as tmp_dir:
      cwd = FilePath( tmp_dir )
      
      args = [self.cl_options]
      args += src_files
      
      args = ' '.join( args )
      
      tmp_obj_files, tmp_dep_files = src_files.change( dir = cwd, ext = ['.o','.d'] )
      
      obj_files = self.buildPaths( src_files ).add('.o')
      
      err = self.__exec( cmd, cwd )
      
      move_file = os.rename
      
      for src_node, obj_file, tmp_obj_file, tmp_dep_file in zip( src_nodes, obj_files, tmp_obj_files, tmp_dep_files ):
        
        if not os.path.isfile( tmp_obj_file ):
          continue
        
        if os.path.isfile( obj_file ):
          os.remove( obj_file )
        move_file( tmp_obj_file, obj_file )
        
        node_targets = self.nodeTargets( obj_file, ideps = _readDeps( tmp_dep_file ) )
        
        src_node.save( vfile, node_targets )
        
        if not err:
          targets += node_targets
      
      if err: raise err
    
    return node_targets
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, vfile, node ):
    
    src_file_values = node.sources()
    src_nodes = node.targetNodes()
    
    if len(src_file_values) == 1:
      targets = self.__buildOne( vfile, cmd, src_file_values[0] )
    else:
      targets = self.__buildMany( vfile, cmd, src_file_values, src_nodes )
      node.setTargetNodes( None )
    
    return targets
  
  #//-------------------------------------------------------//
  
  def   buildStr( self, node ):
    return self.compiler + ': ' + ' '.join( map( str, node.sources() ) )

#//===========================================================================//

class GccCompiler(Builder):
  
  __slots__ = ('compiler')
  
  def   __init__(self, options, language, scontent_type = NotImplemented, tcontent_type = NotImplemented ):
    self.compiler = GccCompilerImpl( options, language, scontent_type, tcontent_type )
    self.signature = self.compiler.signature
  
  #//-------------------------------------------------------//
  
  def   __makeSrcNodes( self, vfile, src_file_values, targets ):
    
    compiler = self.compiler
    
    src_nodes = {}
    for src_file_value in src_file_values:
      node = Node( compiler, src_file_value )
      
      if node.actual( vfile ):
        targets += node.nodeTargets()
      else:
        src_nodes[ FilePath( src_file_value ) ] = [node, src_file_value]
    
    return src_nodes
  
  #//-------------------------------------------------------//
  
  def   __groupSrcNodes( self, src_nodes ):
    src_file_groups = FilePaths( src_nodes ).groupUniqueNames()
    
    groups = []
    
    for src_files in src_file_groups:
      nodes = []
      values = []
      for src_file in src_files:
        nodes.append( src_nodes[ src_file ][0] )
        values.append( src_nodes[ src_file ][1] )
      
      groups.append( (nodes, values) )
    
    return groups
  
  #//-------------------------------------------------------//
  
  def   prebuild( self, vfile, node ):
    
    targets = self.nodeTargets()
    
    src_nodes = self.__makeSrcNodes( vfile, node, targets )
    src_node_groups = self.__groupSrcNodes( src_nodes )
    
    node.setTargets( targets )
    
    pre_nodes = []
    
    for src_nodes, src_values in src_node_groups:
      if len(src_values) == 1:
        tnode = src_nodes[0]
      else:
        tnode = Node( compiler, src_values )
        tnode.setTargetNodes( src_nodes )
      
      pre_node.append( tnode )
    
    return pre_nodes
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, vfile, node, pre_nodes ):
    
    targets = node.nodeTargets()
    
    for pre_node in pre_nodes:
      targets += pre_node.nodeTargets()
    
    return targets
  
  #//-------------------------------------------------------//
  
  def   buildStr( self, node ):
    return self.compiler.buildStr( node )

