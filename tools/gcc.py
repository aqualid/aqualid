import os
import re
import hashlib

from aql_node import Node
from aql_builder import Builder
from aql_value import Value, NoContent
from aql_file_value import FileValue
from aql_utils import toSequence, isSequence, execCommand, moveFile, readTextFile
from aql_path_types import FilePath, FilePaths
from aql_errors import InvalidSourceValueType
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

class _GccCompileCppBuilderImpl (Builder):
  
  __slots__ = ('cmd', '_signature')
  
  def   __init__( self, cmd, signature, env, options ):
    
    self.cmd = cmd
    self._signature = cmd
    self.env = env
    self.options = options
  
  #//-------------------------------------------------------//
  
  def   __buildSingleSource( self, vfile, cmd, src_node ):
    with Tempfile() as dep_file:
      
      cmd = list(self.cmd)
      
      cmd += [ '-MF', dep_file ]
      
      src_file = FilePath( src_node.sources()[0] )
      
      obj_file = self.buildPath( src_file ) + '.o'
      cmd += [ '-o', obj_file ]
      cmd += [ src_file ]
      
      cmd = ' '.join( map(str, cmd ) )
      
      cwd = self.buildPath()
      
      result, out, err = execCommand( cmd, cwd = cwd, env = None )    # TODO: env = options.os_env
      if result:
        raise BuildError( out + '\n' + err )
      
      targets = [ FileValue(obj_file) ]
      itargets = []
      ideps = list( map( FileValue, _readDeps( dep_file.name ) ) )
      
      return src_node_targets, src_node_itargets, src_node_ideps

  #//===========================================================================//

  def   __buildManySources( self, vfile, src_nodes ):
    build_dir = self.buildPath()
    
    cmd = list(self.cmd)
    
    with Tempdir( dir = build_dir ) as tmp_dir:
      cwd = FilePath( tmp_dir )
      
      src_files = FilePaths( map(lambda node: node.sources()[0], src_nodes ) )
      
      cmd += src_files
      
      cmd = ' '.join( map(str, cmd ) )
      
      tmp_obj_files = src_files.replaceDirAndExt( cwd, '.o' )
      tmp_dep_files = tmp_obj_files.replaceExt( '.d' )
      
      obj_files = src_files.addExt( '.o' )
      obj_files = self.buildPaths( obj_files )
      
      result, out, err = execCommand( cmd, cwd = cwd, env = None )  # TODO: env = options.os_env
      
      targets = []
      itargets = []
      ideps = []
      
      for src_node, obj_file, tmp_obj_file, tmp_dep_file in zip( src_nodes, obj_files, tmp_obj_files, tmp_dep_files ):
        if os.path.isfile( tmp_obj_file ):
          moveFile( tmp_obj_file, obj_file )
          
          src_node_targets = [ FileValue(obj_file) ]
          src_node_itargets = []
          src_node_ideps = list( map( FileValue, _readDeps( tmp_dep_file ) ) )
          
          src_node.save( vfile, src_node_targets, src_node_itargets, src_node_ideps )
          
          if not result:
            targets += src_node_targets
            ideps += src_node_ideps
        
      if result:
        raise BuildError( out + '\n' + err )
      
      return targets, itargets, ideps
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, vfile, node ):
    
    targets = []
    itargets = []
    ideps = []
    
    src_nodes = []
    
    for src_file_value in node.sources():
      src_node = Node( self, src_file_value )
      if not src_node.actual( vfile ):
        src_nodes.append( src_node )
    
    if len(src_nodes) > 1:
      tmp_targets, tmp_itargets, tmp_ideps = self.__buildManySources( vfile, src_files )
    else:
      tmp_targets, tmp_itargets, tmp_ideps = self.__buildSingleSource( vfile, src_file )
    
    targets += tmp_targets
    itargets += tmp_itarget_values
    ideps += tmp_idep_values

  
  #//-------------------------------------------------------//
  
  def   signature( self ):
    return self._signature
  
  #//-------------------------------------------------------//

#//===========================================================================//

class GccCompileCppBuilder (Builder):
  
  __slots__ = ('cmd', '_signature')
  
  def   __init__(self, env, options ):
    
    self.env = env
    self.options = options
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    
    if attr == 'cmd':
      self.cmd = self.__cmd()
      return self.cmd
    
    if attr == '_signature':
      self._signature = self.__signature()
      return self._signature
    
    return super(GccCompileCppBuilder,self).__getattr__( attr )
  
  #//-------------------------------------------------------//
  
  def   __cmd( self ):
    options = self.options
    
    cmd = [options.cxx.value(), '-c', '-MMD', '-x', 'c++']
    cmd += options.cxxflags.value()
    cmd += options.ccflags.value()
    cmd += _addPrefix( '-D', options.cppdefines.value() )
    cmd += _addPrefix( '-I', options.cpppath.value() )
    cmd += _addPrefix( '-I', options.ext_cpppath.value() )
    
    return cmd
  
  #//-------------------------------------------------------//
  
  def   __signature( self ):
    values = list( self.cmd )
    values.append( self.build_dir )
    values.append( self.do_path_merge )
    values = ''.join( map( str, values ) )
    
    return hashlib.md5( values ).digest()
  
  #//-------------------------------------------------------//
  
  def   signature( self ):
    return self._signature;
  
  #//-------------------------------------------------------//
  
  def   __makeNodes( self, src_files ):
    nodes = []
    
    builder = _GccCompileCppBuilderImpl( self.cmd, self._signature, self.env, self.options )
    
    for src_files in src_files.groupUniqueNames():
      node = Node( builder, map( FileValue, src_files ) )
      nodes.append( node )
    
    return nodes
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, vfile, node ):
    targets = []
    itargets = []
    ideps = []
    
    src_files = FilePaths( node.sources() )
    src_nodes = self.__makeNodes( src_files )
    
    while src_nodes:
      src_node = src_nodes.pop()
      if not src_node.actual( vfile ):
        break
      
      targets += src_node.target_values
      itargets += src_node.itarget_values
      ideps += src_node.idep_values
    else:
      return targets, itargets, ideps
    
    if src_nodes:
      build_manager.addDeps( node, src_nodes )
    
    tmp_targets, tmp_itargets, tmp_ideps = src_node.build( build_manager, vfile )
    
    targets += src_node.target_values
    itargets += src_node.itarget_values
    ideps += src_node.idep_values
    
    if src_nodes:
      raise RebuildNode()
    
    return targets, itargets, ideps
  
  #//-------------------------------------------------------//
  
  def   buildStr( self, node ):
    return self.options.cxx.value() + ': ' + ' '.join( map( str, node.sources() ) )
