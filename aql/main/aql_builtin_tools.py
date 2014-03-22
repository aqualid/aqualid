
import os.path
import shutil
import errno

from aql.nodes import Builder, FileBuilder
from .aql_tools import Tool

__all__ = ( "ExecuteCommand",
            "InstallBuilder",
            "BuiltinTool",
          )

"""
Unique Value - name + type

value
node

node = ExecuteCommand('gcc --help -v')

tools.cpp.cxx

node = ExecuteCommand( tools.cpp.cxx, '--help -v' )
node = ExecuteMethod( target = my_function )

dir_node = CopyFiles( prog_node, target = dir_name )
dir_node = CopyFilesAs( prog_node, target = dir_name )
dir_node = MoveFiles( prog_node,  )
dir_node = MoveFilesAs( prog_node )
dir_node = RemoveFiles( prog_node )
node = FindFiles( dir_node )

dir_node = FileDir( prog_node )
"""

def   _makeTagetDirs( path_dir ):
  try:
    os.makedirs( path_dir )
  except OSError as e:
    if e.errno != errno.EEXIST:
      raise

#//===========================================================================//

class ExecuteCommand (Builder):
  
  def   build( self, node ):
    cmd = node.getSources()
    out = self.execCmd( cmd )
    
    node.setNoTargets()
    
    return out
  
  #//-------------------------------------------------------//
  
  def   getBuildStrArgs( self, node, brief ):
    cmd = ' '.join( node.getSources() )
    return cmd

#//===========================================================================//

class InstallBuilder (FileBuilder):
  
  def   __init__(self, options, target ):
    self.target = os.path.abspath( target )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    sources = node.getSources()
    
    target = self.target
    
    _makeTagetDirs( target )
    
    for source in sources:
      if os.path.isfile( source ):
        shutil.copy( source, target )
    
    node.setNoTargets()
  
  #//-------------------------------------------------------//
  
  def   getBuildStrArgs( self, node, brief = True ):
    name = self.__class__.__name__
    sources = node.getSources()
    target = self.target
    
    if brief:
      sources = tuple( map( os.path.basename, sources ) )
    
    return name, sources, target

#//===========================================================================//

class BuiltinTool( Tool ):
  
  def   ExecuteCommand( self, options ):
    return ExecuteCommand( options )
  
  def   Install(self, options, target ):
    return InstallBuilder( options, target )
  
  def   DirName(self, options):
    raise NotImplementedError()
  
  def   BaseName(self, options):
    raise NotImplementedError()
