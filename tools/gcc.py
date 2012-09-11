import os
import re
import shutil
import hashlib

from aql_node import Node, FileNodeTargets
from aql_builder import Builder
from aql_value import Value, NoContent
from aql_file_value import FileValue, FileContentChecksum, FileContentTimeStamp
from aql_utils import toSequence, isSequence, execCommand, readTextFile
from aql_path_types import FilePath, FilePaths
from aql_errors import InvalidSourceValueType, BuildError
from aql_options import Options
from aql_temp_file import Tempfile, Tempdir
from aql_option_types import OptionType, BoolOptionType, EnumOptionType, RangeOptionType, ListOptionType, PathOptionType, StrOptionType, VersionOptionType

FileContentType = FileContentChecksum

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

class GccCompileCppBuilder (Builder):
  
  __slots__ = ('cmd', '_signature')
  
  def   __init__(self, env, options ):
    
    self.env = env
    self.options = options
  
  #//-------------------------------------------------------//
  
  def   __exec( self, cmd, cwd ):
    if len( cmd ) > 4096:
      cmd_file = Tempfile( suffix = '.gcc.args')
      cmd = cmd.replace('\\', '/')
      cmd_file.write( cmd )
      cmd_file.close()
      cmd = self.options.cxx.value() +' @' + cmd_file.name
    else:
      cmd = self.options.cxx.value() + ' ' + cmd
      cmd_file = None
    
    try:
      result, out, err = execCommand( cmd, cwd = cwd, env = None, stdout = None, stderr = None )    # TODO: env = options.os_env
      if result:
        return BuildError( out, err )
    finally:
      if cmd_file is not None:
        cmd_file.remove()
    
    return None
  
  #//-------------------------------------------------------//
  
  def   __buildSingleSource( self, vfile, cmd, src_node, targets ):
    with Tempfile( suffix = '.d' ) as dep_file:
      
      cmd = list(cmd)
      
      cmd += [ '-MF', dep_file.name ]
      
      src_file = FilePath( src_node.sources()[0] )
      
      obj_file = self.buildPath( src_file ) + '.o'
      cmd += [ '-o', obj_file ]
      cmd += [ src_file ]
      
      cmd = ' '.join( map(str, cmd ) )
      
      cwd = self.buildPath()
      
      err = self.__exec( cmd, cwd )
      if err: raise err
      
      node_targets = FileNodeTargets( obj_file, ideps = _readDeps( dep_file.name ), content_type = FileContentType )
      
      src_node.save( vfile, node_targets )
      
      targets += node_targets

  #//===========================================================================//

  def   __buildManySources( self, vfile, cmd, src_nodes, targets ):
    build_dir = self.buildPath()
    
    cmd = list(cmd)
    
    with Tempdir( dir = build_dir ) as tmp_dir:
      cwd = FilePath( tmp_dir )
      
      src_files = FilePaths( map(lambda node: node.sources()[0], src_nodes ) )
      
      cmd += src_files
      
      cmd = ' '.join( map(str, cmd ) )
      
      tmp_obj_files = src_files.replaceDirAndExt( cwd, '.o' )
      tmp_dep_files = tmp_obj_files.replaceExt( '.d' )
      
      obj_files = src_files.addExt( '.o' )
      obj_files = self.buildPaths( obj_files )
      
      err = self.__exec( cmd, cwd )
      
      move_file = os.rename
      
      for src_node, obj_file, tmp_obj_file, tmp_dep_file in zip( src_nodes, obj_files, tmp_obj_files, tmp_dep_files ):
        if os.path.isfile( tmp_obj_file ):
          if os.path.isfile( obj_file ):
            os.remove( obj_file )
          move_file( tmp_obj_file, obj_file )
          
          node_targets = FileNodeTargets( targets = obj_file, ideps = _readDeps( tmp_dep_file ), content_type = FileContentType )
          
          src_node.save( vfile, node_targets )
          
          if not err:
            targets += node_targets
      
      if err: raise err
  
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
    
    cmd = ['-c', '-pipe', '-MMD', '-x', 'c++']
    cmd += options.cxxflags.value()
    cmd += options.ccflags.value()
    cmd += _addPrefix( '-D', options.cppdefines.value() )
    cmd += _addPrefix( '-I', options.cpppath.value() )
    cmd += _addPrefix( '-I', options.ext_cpppath.value() )
    
    return [ ' '.join( cmd ) ]
  
  #//-------------------------------------------------------//
  
  def   __signature( self ):
    values = list( self.cmd )
    values.append( self.build_dir )
    values.append( self.do_path_merge )
    values = ''.join( map( str, values ) )
    
    return hashlib.md5( values.encode('utf-8') ).digest()
  
  #//-------------------------------------------------------//
  
  def   signature( self ):
    return self._signature;
  
  #//-------------------------------------------------------//
  
  def   __makeSrcNodes( self, vfile, node, targets ):
    
    src_nodes = {}
    for src_file_value in node.sources():
      node = Node( self, src_file_value )
      
      if node.actual( vfile ):
        targets += node.nodeTargets()
      else:
        src_nodes[ src_file_value.name ] = node
    
    return src_nodes
  
  #//-------------------------------------------------------//
  
  def   __groupSrcNodes( self, src_nodes ):
    src_file_groups = FilePaths( src_nodes ).groupUniqueNames()
    
    groups = []
    
    for src_files in src_file_groups:
      groups.append( [ src_nodes[ src_file ] for src_file in src_files ] )
    
    return groups
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, vfile, node ):
    
    targets = FileNodeTargets()
    
    src_nodes = self.__makeSrcNodes( vfile, node, targets )
    src_node_groups = self.__groupSrcNodes( src_nodes )
    
    cmd = self.cmd
    
    for src_nodes in src_node_groups:
      if len(src_nodes) == 1:
        self.__buildSingleSource( vfile, cmd,  src_nodes[0], targets )
      else:
        self.__buildManySources( vfile, cmd,  src_nodes, targets )
    
    return targets
  
  #//-------------------------------------------------------//
  
  def   buildStr( self, node ):
    return self.options.cxx.value() + ': ' + ' '.join( map( str, node.sources() ) )

