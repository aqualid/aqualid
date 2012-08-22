
from aql_node import Node
from aql_builder import Builder
from aql_value import Value, NoContent
from aql_file_value import FileValue
from aql_utils import toSequence, isSequence, execCommand
from aql_simple_types import FilePath
from aql_errors import InvalidSourceValueType

#//===========================================================================//

def   _addPrefix( prefix, values ):
  return map( lambda v, prefix = prefix: prefix + v, values )

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
    build_dir = outdir_mapper.getBuildPath()
    
    with Tempdir( dir = build_dir ) as tmp_dir:
      cwd = tmp_dir.path
      
      src_files = FilePaths( map(lambda node: node.sources()[0], src_nodes ) )
      
      cmd += src_files
      
      cmd = ' '.join( map(str, cmd ) )
      
      tmp_obj_files = src_files.replaceDirAndExt( cwd, '.o' )
      tmp_dep_files = tmp_obj_files.replaceExt( '.d' )
      
      obj_files = src_files.addExt( '.o' )
      obj_files = self.getBuildPaths( obj_files )
      
      result, out, err = execCommand( cmd, cwd = cwd, env = None )  # TODO: env = options.os_env
      
      targets = []
      itargets = []
      ideps = []
      
      for src_node, obj_file, tmp_obj_file, tmp_dep_file in zip( src_nodes, obj_files, tmp_obj_files, tmp_dep_files ):
        if os.path.isfile( tmp_obj_file ):
          self.moveFile( tmp_obj_file, obj_file )
          
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
            batch_src_files.add( src_file )
      
      src_files = rest_src_files
      src_nodes = rest_src_nodes
      
      if len(batch_src_files) > 1:
        tmp_targets, tmp_itargets, tmp_ideps = self.__buildManySources( vfile, cmd, batch_src_nodes )
      else:
        tmp_targets, tmp_itargets, tmp_ideps = self.__buildSingleSource( vfile, cmd, batch_src_nodes[0] )
      
      targets += tmp_targets
      itargets += tmp_itargets
      ideps += tmp_ideps
  
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
  
  def   build( self, build_manager, vfile, node ):
    
    cmd       = self.__cmd()
    src_files = FilePaths( node.sources() )
    
    targets, itargets, ideps = self.__buildSources( cmd, vfile, cmd, src_files )
    
    return targets, itargets, ideps
  
  #//-------------------------------------------------------//
  
  def   clear( self, node, target_values, itarget_values ):
    for value in target_values:
      value.remove()
    
    for value in itarget_values:
      value.remove()
  
  #//-------------------------------------------------------//
  
  def   signatures( self ):
    return hashlib.md5( ' '.join( map(str, self.__cmd() ) ) )
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    return ' '.join( self.long_name )

