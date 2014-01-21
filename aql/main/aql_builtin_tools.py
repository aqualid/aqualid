
from aql.util_types import FilePath
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
  
  def   build( self, node ):
    cmd = node.getSources()
    out = self.execCmd( cmd )
    return out
  
  #//-------------------------------------------------------//
  
  def   getBuildStrArgs( self, node, detailed = False ):
    cmd = ' '.join( node.getSources() )
    return cmd

#//===========================================================================//

class BuiltinTool( Tool ):
  
  def   ExecuteCommand( self, options, with_output = False ):
    return ExecuteCommand( options, with_output = False )
  
  def   DirName(self, options):
    raise NotImplementedError()
  
  def   BaseName(self, options):
    raise NotImplementedError()
