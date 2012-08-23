import os
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
  
  dep_files = FilePaths()
  
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
  
  return dep_files

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
  
  __slots__ = ('cmd', )
  
  def   __init__(self, env, options ):
    
    self.name = "GccCppCompiler"
    self.env = env
    self.options = options
  
  #//-------------------------------------------------------//
  
  def   __buildSingleSource( self, vfile, cmd, src_node ):
    with Tempfile() as dep_file:
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
      
      src_node_targets = [ FileValue(obj_file) ]
      src_node_itargets = []
      src_node_ideps = [] # TODO add dependecies
      src_node.save( vfile, src_node_targets, src_node_itargets, src_node_ideps )
      
      return src_node_targets, src_node_itargets, src_node_ideps

  #//===========================================================================//

  def   __buildManySources( self, vfile, cmd, src_nodes ):
    build_dir = self.buildPath()
    
    with Tempdir( dir = build_dir ) as tmp_dir:
      cwd = FilePath( tmp_dir )
      
      src_files = FilePaths( map(lambda node: node.sources()[0], src_nodes ) )
      
      cmd += src_files
      
      cmd = ' '.join( map(str, cmd ) )
      
      print( src_files )
      
      tmp_obj_files = src_files.replaceDirAndExt( cwd, '.o' )
      tmp_dep_files = tmp_obj_files.replaceExt( '.d' )
      
      obj_files = src_files.addExt( '.o' )
      obj_files = self.buildPaths( obj_files )
      
      result, out, err = execCommand( cmd, cwd = cwd, env = None )  # TODO: env = options.os_env
      
      targets = []
      itargets = []
      ideps = []
      
      print( tmp_obj_files )
      print( obj_files )
      
      for src_node, obj_file, tmp_obj_file, tmp_dep_file in zip( src_nodes, obj_files, tmp_obj_files, tmp_dep_files ):
        if os.path.isfile( tmp_obj_file ):
          moveFile( tmp_obj_file, obj_file )
          moveFile( tmp_dep_file, obj_file.replaceExt('.d') )
          
          src_node_targets = [ FileValue(obj_file) ]
          src_node_itargets = []
          src_node_ideps = [] # TODO add dependecies
          src_node.save( vfile, src_node_targets, src_node_itargets, src_node_ideps )
          
          if not result:
            targets += src_node_targets
            ideps += src_node_ideps
        
      if result:
        raise BuildError( out + '\n' + err )
      
      return targets, itargets, ideps
  
  #//-------------------------------------------------------//
  
  def   __buildSources( self, vfile, cmd, src_files ):
    
    targets = []
    itargets = []
    ideps = []
    
    src_nodes = map( lambda src_file, builder = self: Node( builder, FileValue( src_file ) ), src_files )
    
    while src_files:
      batch_src_nodes = []
      batch_src_names = set()
      
      rest_src_files = FilePaths()
      rest_src_nodes = FilePaths()
      
      for src_file, src_node in zip( src_files, src_nodes ):
        if src_node.actual( vfile ):
          targets += src_node.target_values
          itargets += src_node.itarget_values
          ideps += src_node.idep_values
        
        else:
          if src_file.name in batch_src_names:
            rest_src_files.append( src_file )
            rest_src_nodes.append( src_node )
          else:
            batch_src_names.add( src_file.name )
            batch_src_nodes.append( src_node )
      
      src_files = rest_src_files
      src_nodes = rest_src_nodes
      
      if len(batch_src_nodes) > 1:
        tmp_targets, tmp_itargets, tmp_ideps = self.__buildManySources( vfile, cmd, batch_src_nodes )
      else:
        tmp_targets, tmp_itargets, tmp_ideps = self.__buildSingleSource( vfile, cmd, batch_src_nodes[0] )
      
      targets += tmp_targets
      itargets += tmp_itargets
      ideps += tmp_ideps
    
    return targets, itargets, ideps
  
  #//-------------------------------------------------------//
  
  def   __cmd( self ):
    options = self.options
    
    cmd = [options.cxx.value(), '-c', '-MD', '-x', 'c++']
    cmd += options.cxxflags.value()
    cmd += options.ccflags.value()
    cmd += _addPrefix( '-D', options.cppdefines.value() )
    cmd += _addPrefix( '-I', options.cpppath.value() )
    cmd += _addPrefix( '-I', options.ext_cpppath.value() )
    
    return cmd
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, vfile, node ):
    
    cmd       = self.__cmd()
    src_files = FilePaths( node.sources() )
    
    targets, itargets, ideps = self.__buildSources( vfile, cmd, src_files )
    
    return targets, itargets, ideps
  
  #//-------------------------------------------------------//
  
  def   clear( self, node, target_values, itarget_values ):
    for value in target_values:
      value.remove()
    
    for value in itarget_values:
      value.remove()
  
  #//-------------------------------------------------------//
  
  def   signature( self ):
    return hashlib.md5( ' '.join( map(str, self.__cmd() ) ) ).digest()
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    return self.name

