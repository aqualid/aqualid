import aql

"""
Unique Value - name + type

value
node

node = ExecuteCommand('gcc --help -v')

tools.cpp.cxx

node = ExecuteCommand( tools.cpp.cxx, '--help -v' )
node = ExecuteMethod( target = my_function )

side_node = SideEffects( prog_node )
dir_node = CopyFiles( prog_node, target = dir_name )
dir_node = CopyFilesAs( prog_node, target = dir_name )
dir_node = MoveFiles( prog_node,  )
dir_node = MoveFilesAs( prog_node )
dir_node = RemoveFiles( prog_node )
node = FindFiles( dir_node )

dir_node = FileDir( prog_node )



"""

class ExecuteCommand (aql.Builder):
  
  NAME_ATTRS = None
  SIGNATURE_ATTRS = ('env', )

  #//-------------------------------------------------------//
  
  def   __init__(self, options ):
    self.env = options.env.get().copy( value_type = str )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    cmd = node.sources()
    cwd = self.buildPath()
    
    result = aql.execCommand( cmd, env = self.env, cwd = cwd)
    
    if result.failed():
      raise result
    
    targets = ( result.out, result.err )
    
    node.setTargets( targets )
  
  #//-------------------------------------------------------//
  
  def   buildStr( self, node ):
    return ' '.join( self.cmd ) + ' ' + ' '.join( map( str, node.sources() ) )
