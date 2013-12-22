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
  
  __slots__ = ('args',)

  __id_keys__ = tuple()
  __signature_keys__ = ('env',)

  #//-------------------------------------------------------//
  
  def   __init__(self, options, args ):
    self.args = args
  
  #//-------------------------------------------------------//

  def   getSignature( self ):
    return bytearray()
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    cmd = list( node.sources() )
    
    env = self.options.env.get().copy( value_type = str )
    
    result = aql.execCommand( cmd, env = env )
    
    value = aql.Value( value_name, [result.returncode, result.out, result.err] )
    node.setTargets( value )
  
  #//-------------------------------------------------------//
  
  def   buildStr( self, node ):
    return ' '.join( self.cmd ) + ' ' + ' '.join( map( str, node.sources() ) )

  def   makeValues( self, values, use_cache = False ):
    return map( aql.StringValue, values )
