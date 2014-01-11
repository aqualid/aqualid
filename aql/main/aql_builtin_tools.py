
from aql.utils import execCommand
from aql.nodes import Builder

from .aql_tools import Tool

__all__ = ( "ExecuteCommand",
            "BuiltinTool"
          )

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

class ExecuteCommand (Builder):
  
  NAME_ATTRS = None
  SIGNATURE_ATTRS = ('env_path', 'with_output' )

  #//-------------------------------------------------------//
  
  def   __init__(self, options, with_output = False ):
    self.with_output = with_output
    self.env = options.env.get().copy( value_type = str )
    self.env_path = list( options.env['PATH'].get() )
    
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    cmd = node.sources()
    cwd = self.buildPath()
    
    result = execCommand( cmd, env = self.env, cwd = cwd)
    
    if result.failed():
      raise result
    
    if self.with_output:
      targets = [ ( result.out, result.err ) ]
    else:
      targets = []
      
    node.setTargets( targets )
  
  #//-------------------------------------------------------//
  
  def   buildStr( self, node ):
    return ' '.join( map( str, node.sources() ) )

#//===========================================================================//

class BuiltinTool( Tool ):
  
  def   ExecuteCommand( self, options, with_output = False ):
    return ExecuteCommand( options, with_output = False )
  
  def   DirName(self, options):
    raise NotImplementedError()
  
  def   BaseName(self, options):
    raise NotImplementedError()
