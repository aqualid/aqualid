
import sys
import os
import os.path
import shutil
import errno

from aql.util_types import isUnicode, encodeStr, decodeBytes
from aql.utils import openFile
from aql.nodes import Builder, FileBuilder
from .aql_tools import Tool

__all__ = (
  "BuiltinTool",
)

"""
Unique Value - name + type

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

class   ErrorDistCommandInvalid( Exception ):
  def   __init__( self, command ):
    msg = "distutils command '%s' is not supported" % (command,)
    super(ErrorDistCommandInvalid, self).__init__(msg)

#//===========================================================================//

def   _makeTargetDirs( path_dir ):
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
  
  def   getTraceName(self, brief ):
    return "Execute"
  
  #//-------------------------------------------------------//
  
  def   getBuildStrArgs( self, node, brief ):
    cmd = node.getSourceValues()
    return (cmd,)

#//===========================================================================//

class CopyFilesBuilder (FileBuilder):
  
  NAME_ATTRS = ['target']
  
  def   __init__(self, options, target ):
    self.target = os.path.abspath( target )
    self.split = self.splitBatch
  
  #//-------------------------------------------------------//
  
  def   buildBatch( self, node ):
    target = self.target
    
    _makeTargetDirs( target )
    
    for src_value in node.getSourceValues():
      src = src_value.get()
      
      dst = os.path.join( target, os.path.basename( src ) )
      shutil.copyfile( src, dst )
      shutil.copymode( src, dst )
      
      node.addSourceTargets( src_value, dst )
  
  #//-------------------------------------------------------//
  
  def   getTraceName(self, brief ):
    return "Copy files"
  
  #//-------------------------------------------------------//
  
  def   getTraceTargets( self, node, brief ):
    return self.target
  
  #//-------------------------------------------------------//
  
  def   getTargetValues( self, source_values ):
    src = source_values[0].get()
    return ( os.path.join( self.target, os.path.basename(src) ), )

#//===========================================================================//
 
class CopyFileAsBuilder (FileBuilder):
  
  NAME_ATTRS = ['target']
  
  def   __init__(self, options, target ):
    self.target = os.path.abspath( target )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    target = self.target
    
    target_dir = os.path.dirname( target )
    _makeTargetDirs( target_dir )
    
    source = node.getSources()[0]
    
    shutil.copyfile( source, target )
    shutil.copymode( source, target )
    
    node.addTargets( target )
  
  #//-------------------------------------------------------//
  
  def   getTraceName(self, brief ):
    return "Copy file"
  
  #//-------------------------------------------------------//
  
  def   getTraceTargets( self, node, brief ):
    return self.target
  
  #//-------------------------------------------------------//
  
  def   getTargetValues( self, source_values ):
    return self.target

#//===========================================================================//
 
class WriteFileBuilder (Builder):
  
  NAME_ATTRS = ['target']
  
  def   __init__(self, options, target, binary = False, encoding = None ):
    self.binary = binary
    self.encoding = encoding
    self.target = os.path.abspath( target )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    target = self.target
    
    target_dir = os.path.dirname( target )
    _makeTargetDirs( target_dir )
    
    with openFile( target, write = True, binary = self.binary, encoding = self.encoding ) as f:
      f.truncate()
      for src in node.getSources():
        if self.binary:
          if isUnicode( src ):
            src = encodeStr( src, self.encoding )
        else:
          if isinstance( src, (bytearray, bytes) ):
            src = decodeBytes( src, self.encoding )

        f.write( src )
    
    node.addTargets( self.makeFileValue( target ) )
  
  #//-------------------------------------------------------//
  
  def   getTraceName(self, brief ):
    return "Writing content"
  
  #//-------------------------------------------------------//
  
  def   getTraceTargets( self, node, brief ):
    return self.target
  
  #//-------------------------------------------------------//
  
  def   getTargetValues( self, source_values ):
    return self.target

#//===========================================================================//

class DistBuilder (FileBuilder):

  NAME_ATTRS = ('target',)
  signature = None  # TODO: Build Always. Add parsing of setup.py output
                    # copying <filepath> -> <detination dir>

  def   __init__(self, options, command, formats, target ):

    target = os.path.abspath( target )

    script_args = [ command ]

    if command.startswith('bdist'):
      temp_dir = self.getBuildPath()
      script_args += [ '--bdist-base', temp_dir ]

    elif command != 'sdist':
      raise ErrorDistCommandInvalid( command )

    script_args += [ '--formats', formats, '--dist-dir', target ]
    
    self.command = command
    self.target = target
    self.script_args = script_args

  #//-------------------------------------------------------//

  def   getTraceName(self, brief ):
    return "distutils %s" % (self.command)

  #//-------------------------------------------------------//

  def   build( self, node ):

    script = node.getSources()[0]

    cmd = [sys.executable, script ]
    cmd += self.script_args

    script_dir = os.path.dirname( script )
    out = self.execCmd( cmd, script_dir )

    node.setNoTargets()

    return out

#//===========================================================================//

class BuiltinTool( Tool ):
  
  def   ExecuteCommand( self, options ):
    return ExecuteCommand( options )
  
  def   CopyFiles(self, options, target ):
    return CopyFilesBuilder( options, target )
  
  def   CopyFileAs(self, options, target ):
    return CopyFileAsBuilder( options, target )
  
  def   WriteFile(self, options, target, binary = False, encoding = None ):
    return WriteFileBuilder( options, target, binary = binary, encoding = encoding )

  def   CreateDist(self, options, target, command, formats ):
    return DistBuilder( options, command = command, target = target, formats = formats )

  def   DirName(self, options):
    raise NotImplementedError()
  
  def   BaseName(self, options):
    raise NotImplementedError()
