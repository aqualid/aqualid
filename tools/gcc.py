
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
  
  def   __init__(self, name, env, options ):
    
    self.name = [ name ]
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
      
      #~ result = execCommand( cmd, cwd = cwd, env = options.os_env )
      result, out, err = execCommand( cmd, cwd = cwd, env = None )
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
          moveFile( tmp_obj_file, obj_file )
          
          src_node_targets = [ FileValue(obj_file) ]
          src_node_itargets = []
          src_node_ideps = [] # TODO add dependecies
          src_node.save( vfile, src_node_targets, src_node_itargets, src_node_ideps )
          
          if not result:
            targets += src_node_targets
            ideps += src_node_ideps
        
      if result:
        raise BuildError( out + '\n' + err )
      
      #TODO: add dependecies
      
      return targets, itargets, ideps
  
  #//-------------------------------------------------------//
  
  def   __buildSources( self, cmd, node, vfile ):
    src_files = FilePaths( node.sources() )
    
    targets = []
    itargets = []
    ideps = []
    
    src_nodes = map( lambda src_file, builder = self: Node( builder, FileValue( src_file) ), src_files )
    
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
    
    src_nodes = list( map( lambda src_file, builder = self: Node( builder, FileValue( src_file) ), src_files ))
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, node ):
    
    options = self.options
    
    cmd = [options.cxx.value(), '-c', '-MMD', '-x', 'c++']
    cmd += options.cxxflags.value()
    cmd += options.ccflags.value()
    cmd += _addPrefix( '-D', options.cppdefines.value() )
    cmd += _addPrefix( '-I', options.cpppath.value() )
    cmd += _addPrefix( '-I', options.ext_cpppath.value() )
    
    node
    
    with Tempfiles() as dep_files:
      src_files = _getSourceFiles( node.sources() )
      if len(src_files) == 1:
        src_file = src_files[0]
        dep_files.append( Tempfile().close().name )
        cmd += [ '-MF', dep_files[0] ]
        cmd += [ '-o', dep_files[0] ]
    
    
    # > cd C:\work\src\sbe\build_dir\tmp_1234
    # > g++ -c -MMD -O3 tests\list\test_list.cpp sbe\path_finder\foo.cpp sbe\path_finder\bar.cpp
    # > mv test_list.o tests\list\test_list.o
    # > mv foo.o sbe\path_finder\foo.o
    # > mv bar.o sbe\path_finder\bar.o
    # > g++ -c -MMD -O3 tests\list\test_list.cpp sbe\path_finder\foo.cpp sbe\path_finder\bar.cpp
    
    cmd += src_files
    
    cmd = ' '.join( map(str, cmd ) )
    
    cwd = options.build_dir.value()
    
    #~ result = execCommand( cmd, cwd = cwd, env = options.os_env )
    result = execCommand( cmd, cwd = cwd, env = None )
    
    target_values = []
    
    sub_nodes = []
    
    for source_value in node.sources():
      
      n = Node( self.builder, source_value )
      if n.actual( vfile ):
        target_values += n.targets()
      else:
        sub_nodes.append( n )
    
    if sub_nodes:
      bm.addDeps( node, sub_nodes ); bm.selfTest()
      raise RebuildNode()
    
    return target_values, [], []
  
  #//-------------------------------------------------------//
  
  def   clear( self, node, target_values, itarget_values ):
    for value in target_values:
      value.remove()
  
  #//-------------------------------------------------------//
  
  def   values( self ):
    return self.builder.values()
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    return ' '.join( self.long_name )

