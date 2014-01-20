
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
  SIGNATURE_ATTRS = ('env_path', )

  #//-------------------------------------------------------//
  
  def   __init__(self, options ):
    self.env = options.env.get().copy( value_type = str )
    self.env_path = list( options.env['PATH'].get() )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    cmd = node.getSources()
    cwd = self.getBuildPath()
    
    result = execCommand( cmd, env = self.env, cwd = cwd )
    
    if result.failed():
      raise result
    
    self.setTargets( targets = [] )
  
  #//-------------------------------------------------------//
  
  def   getBuildStrArgs( self, node, detailed = False ):
    
    sources = node.getSources()
    
    if detailed:
      name    = ' '.join( self.cmd[:-2] )
      target = self.target
    else:
      name    = aql.FilePath(self.cmd[0]).name
      sources  = [ aql.FilePath(source).name_ext for source in sources ]
      target  = aql.FilePath(self.target).name_ext
    
    return name, sources, target

#//===========================================================================//

class BuiltinTool( Tool ):
  
  def   ExecuteCommand( self, options, with_output = False ):
    return ExecuteCommand( options, with_output = False )
  
  def   DirName(self, options):
    raise NotImplementedError()
  
  def   BaseName(self, options):
    raise NotImplementedError()
