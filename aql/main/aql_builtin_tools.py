
import sys
import io
import os
import os.path
import shutil
import zipfile
import tarfile

from aql.util_types import isUnicode, encodeStr, decodeBytes
from aql.utils import openFile
from aql.values import FileEntityBase
from aql.nodes import Builder, FileBuilder
from .aql_tools import Tool

__all__ = (
  "BuiltinTool",
)

"""
Unique Entity - name + type

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
    cmd = node.getSourceEntities()
    return (cmd,)

#//===========================================================================//

class CopyFilesBuilder (FileBuilder):
  
  NAME_ATTRS = ['target']
  
  def   __init__(self, options, target ):
    self.target = self.getTargetDirPath( target )
    self.split = self.splitBatch
  
  #//-------------------------------------------------------//
  
  def   buildBatch( self, node ):
    target = self.target
    
    for src_entity in node.getSourceEntities():
      src = src_entity.get()
      
      dst = os.path.join( target, os.path.basename( src ) )
      shutil.copyfile( src, dst )
      shutil.copymode( src, dst )
      
      node.addSourceTargets( src_entity, dst )
  
  #//-------------------------------------------------------//
  
  def   getTraceName(self, brief ):
    return "Copy files"
  
  #//-------------------------------------------------------//
  
  def   getTraceTargets( self, node, brief ):
    return self.target
  
  #//-------------------------------------------------------//
  
  def   getTargetEntities( self, source_entities ):
    src = source_entities[0].get()
    return ( os.path.join( self.target, os.path.basename(src) ), )

#//===========================================================================//
 
class CopyFileAsBuilder (FileBuilder):
  
  NAME_ATTRS = ['target']
  
  def   __init__(self, options, target ):
    self.target = self.getTargetFilePath( target )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    source = node.getSources()[0]
    target = self.target
    
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
  
  def   getTargetEntities( self, source_entities ):
    return self.target

#//===========================================================================//

class TarFilesBuilder (FileBuilder):
  
  NAME_ATTRS = ['target']
  SIGNATURE_ATTRS = ['rename']
  
  def   __init__(self, options, target, mode, rename, ext ):
    
    if not mode:
      mode = "w:bz2"
    
    if not ext:
      if mode == "w:bz2":
        ext = ".tar.bz2"
      elif mode == "w:gz":
        ext = ".tar.gz"
      elif mode == "w":
        ext = ".tar"
    
    self.target = self.getTargetFilePath( target, ext )
    self.mode = mode
    self.rename = rename if rename else tuple()
  
  #//-------------------------------------------------------//
  
  def __getArcname( self, file_path ):
    for arc_name, path in self.rename:
      if file_path == path:
        return arc_name
    
    return os.path.basename( file_path )
  
  #//-------------------------------------------------------//
  
  def   __addFile( self, arch, filepath ):
    arcname = self.__getArcname( filepath )
    arch.add( filepath, arcname )
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __addEntity( arch, entity ):
    arcname = entity.name
    data = entity.get()
    if isUnicode( data ):
      data = encodeStr( data )
  
    tinfo = tarfile.TarInfo(arcname)
    tinfo.size = len(data)
    arch.addfile( tinfo, io.BytesIO(data) )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    target = self.target
    
    arch = tarfile.open( name = self.target, mode = self.mode )
    try:
      for entity in node.getSourceEntities():
        if isinstance( entity, FileEntityBase ):
          self.__addFile( arch, entity.get() )
        else:
          self.__addEntity( arch, entity )
      
    finally:
      arch.close()
      
    node.addTargets( target )
  
  #//-------------------------------------------------------//
  
  def   getTraceName(self, brief ):
    return "Create Tar"
  
  #//-------------------------------------------------------//
  
  def   getTraceTargets( self, node, brief ):
    return self.target
  
  #//-------------------------------------------------------//
  
  def   getTargetEntities( self, source_entities ):
    return self.target

#//===========================================================================//
 
class ZipFilesBuilder (FileBuilder):
  
  NAME_ATTRS = ['target']
  SIGNATURE_ATTRS = ['rename']
  
  def   __init__(self, options, target, rename, ext = None ):
    
    if ext is None:
      ext = ".zip"
    
    self.target = self.getTargetFilePath( target, ext = ext )
    self.rename = rename if rename else tuple()
  
  #//-------------------------------------------------------//
  
  def   __openArch( self, large = False ):
    try:
      return zipfile.ZipFile( self.target, "w", zipfile.ZIP_DEFLATED, large )
    except RuntimeError:
      pass
    
    return zipfile.ZipFile( self.target, "w", zipfile.ZIP_STORED, large )
  
  #//-------------------------------------------------------//
  
  def __getArcname( self, file_path ):
    for arc_name, path in self.rename:
      if file_path == path:
        return arc_name
    
    return os.path.basename( file_path )
  
  #//-------------------------------------------------------//
  
  def   __addFiles( self, arch, source_entities ):
    for entity in source_entities:
      if isinstance( entity, FileEntityBase ):
        filepath = entity.get()
        arcname = self.__getArcname( filepath )
        arch.write( filepath, arcname )
      else:
        arcname = entity.name
        data = entity.get()
        if isUnicode( data ):
          data = encodeStr( data )
        
        arch.writestr( arcname, data )

  #//-------------------------------------------------------//
  
  def   build( self, node ):
    target = self.target
    
    source_entities = node.getSourceEntities()
    
    arch = self.__openArch()
    
    try:
      self.__addFiles( arch, source_entities )
    except zipfile.LargeZipFile:
      arch.close()
      arch = None
      arch = self.__openArch( large = True )
      
      self.__addFiles( arch, source_entities )
    finally:
      if arch is not None:
        arch.close()
      
    node.addTargets( target )
  
  #//-------------------------------------------------------//
  
  def   getTraceName(self, brief ):
    return "Create Zip"
  
  #//-------------------------------------------------------//
  
  def   getTraceTargets( self, node, brief ):
    return self.target
  
  #//-------------------------------------------------------//
  
  def   getTargetEntities( self, source_entities ):
    return self.target

#//===========================================================================//
 
class WriteFileBuilder (Builder):
  
  NAME_ATTRS = ['target']
  
  def   __init__(self, options, target, binary = False, encoding = None ):
    self.binary = binary
    self.encoding = encoding
    self.target = self.getTargetFilePath( target )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    target = self.target
    
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
    
    node.addTargets( self.makeFileEntity( target ) )
  
  #//-------------------------------------------------------//
  
  def   getTraceName(self, brief ):
    return "Writing content"
  
  #//-------------------------------------------------------//
  
  def   getTraceTargets( self, node, brief ):
    return self.target
  
  #//-------------------------------------------------------//
  
  def   getTargetEntities( self, source_entities ):
    return self.target

#//===========================================================================//

class DistBuilder (FileBuilder):

  NAME_ATTRS = ('target',)

  def   __init__(self, options, command, formats, target ):

    target = self.getTargetDirPath( target )

    script_args = [ command ]

    if command.startswith('bdist'):
      temp_dir = self.getBuildPath()
      script_args += [ '--bdist-base', temp_dir ]

    elif command != 'sdist':
      raise ErrorDistCommandInvalid( command )
    
    if formats:
      script_args += [ '--formats', formats ]
    
    script_args += [ '--dist-dir', target ]
    
    self.command = command
    self.target = target
    self.script_args = script_args

  #//-------------------------------------------------------//

  def   getTraceName(self, brief ):
    return "distutils %s" % (self.command)

  #//-------------------------------------------------------//

  def   build( self, node ):

    script = node.getSources()[0]

    cmd = [ sys.executable, script ]
    cmd += self.script_args

    script_dir = os.path.dirname( script )
    out = self.execCmd( cmd, script_dir )
    
    # TODO: Add parsing of setup.py output "copying <filepath> -> <detination dir>"
    node.setNoTargets()

    return out

#//===========================================================================//

class   InstallDistBuilder (FileBuilder):

  NAME_ATTRS = ('user',)

  def   __init__(self, options, user ):

    self.user = user

  #//-------------------------------------------------------//

  def   getTraceName(self, brief ):
    return "distutils install"

  #//-------------------------------------------------------//

  def   build( self, node ):

    script = node.getSources()[0]

    cmd = [ sys.executable, script, "install" ]
    if self.user:
      cmd.append( "--user" )

    script_dir = os.path.dirname( script )
    out = self.execCmd( cmd, script_dir )
    
    # TODO: Add parsing of setup.py output "copying <filepath> -> <detination dir>"
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

  def   CreateDist( self, options, target, command, formats = None ):
    return DistBuilder( options, command = command, target = target, formats = formats )
  
  def   InstallDist( self, options, user = True ):
    return InstallDistBuilder( options, user = user )
  
  def   CreateZip(self, options, target, rename = None, ext = None ):
    return ZipFilesBuilder( options, target = target, rename = rename, ext = ext )
  
  def   CreateTar(self, options, target, mode = None, rename = None, ext = None ):
    return TarFilesBuilder( options, target = target, mode = mode, rename = rename, ext = ext )
  
  def   DirName(self, options):
    raise NotImplementedError()
  
  def   BaseName(self, options):
    raise NotImplementedError()
