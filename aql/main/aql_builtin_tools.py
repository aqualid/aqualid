
import sys
import io
import os
import os.path
import shutil
import zipfile
import tarfile
import itertools

from aql.util_types import isUnicode, encodeStr, decodeBytes, isString, toSequence
from aql.utils import openFile
from aql.entity import FileEntityBase
from aql.nodes import Builder, FileBuilder
from .aql_tools import Tool

__all__ = (
  "BuiltinTool",
)

class   ErrorDistCommandInvalid( Exception ):
  def   __init__( self, command ):
    msg = "distutils command '%s' is not supported" % (command,)
    super(ErrorDistCommandInvalid, self).__init__(msg)

#//===========================================================================//

class ExecuteCommand (Builder):
  
  NAME_ATTRS = ('targets',)
  
  def   __init__(self, options, target = None, target_flag = None ):
    
    self.targets = [ self.getTargetFilePath( target ) for target in toSequence(target) ]
    self.target_flag = target_flag
  
  #//-------------------------------------------------------//
  
  def   _getTargetsCmd( self ):
    
    targets = self.targets
    
    prefix = self.target_flag
    if not prefix:
      return tuple(targets)
    
    prefix = prefix.lstrip()
    
    if not prefix:
      return tuple(targets)
    
    rprefix = prefix.rstrip()
    
    if prefix != rprefix:
      return tuple( itertools.chain( *((rprefix, target) for target in targets )) )
    
    return tuple( "%s%s" % (prefix, target) for target in targets ) 
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    cmd = node.getSources()
    
    targets = self._getTargetsCmd()
    if targets:
      cmd += targets
    
    out = self.execCmd( cmd )
    
    targets = self.makeFileEntities( targets )
    
    node.addTargets( targets )
    
    return out
  
  #//-------------------------------------------------------//
  
  def   getTargetEntities( self, source_entities ):
    file_type = self.file_entity_type
    return [ file_type( target, signature = None ) for target in self.targets ]
  
  #//-------------------------------------------------------//
  
  def   getBuildStrArgs( self, node, brief ):
    sources = node.getSourceEntities()
    
    try:
      name = sources[0]
    except Exception:
      name = ''
    
    try:
      targets = self.getTargetEntities( sources )
    except Exception:
      targets = None
    
    try:
      sources = sources[1:]
    except Exception:
      sources = None
    
    return name, sources, targets


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
  
  def   getTargetEntities( self, source_entities ):
    return self.target

#//===========================================================================//

class TarFilesBuilder (FileBuilder):
  
  NAME_ATTRS = ['target']
  SIGNATURE_ATTRS = ['rename', 'basedir']
  
  def   __init__(self, options, target, mode, rename, basedir, ext ):
    
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
    self.basedir = os.path.normcase(os.path.normpath(basedir)) if basedir else None
  
  #//-------------------------------------------------------//
  
  def __getArcname( self, file_path ):
    for arc_name, path in self.rename:
      if file_path == path:
        return arc_name
    
    basedir = self.basedir
    if basedir:
      if file_path.startswith( basedir ):
        return file_path[ len(basedir) : ]
    
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
  
  def   getTargetEntities( self, source_entities ):
    return self.target

#//===========================================================================//
 
class ZipFilesBuilder (FileBuilder):
  
  NAME_ATTRS = ['target']
  SIGNATURE_ATTRS = ['rename', 'basedir']
  
  def   __init__(self, options, target, rename, basedir, ext ):
    
    if ext is None:
      ext = ".zip"
    
    self.target = self.getTargetFilePath( target, ext = ext )
    self.rename = rename if rename else tuple()
    self.basedir = os.path.normcase(os.path.normpath(basedir)) if basedir else None
  
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
    
    basedir = self.basedir
    if basedir:
      if file_path.startswith( basedir ):
        return file_path[ len(basedir) : ]
    
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
  
  def   getTargetEntities( self, source_entities ):
    return self.target

#//===========================================================================//

class DistBuilder (FileBuilder):

  NAME_ATTRS = ('target', 'command', 'formats')
  SIGNATURE_ATTRS = ('script_args', )

  def   __init__(self, options, command, args, target ):

    target = self.getTargetDirPath( target )

    script_args = [ command ]

    if command.startswith('bdist'):
      temp_dir = self.getBuildPath()
      script_args += [ '--bdist-base', temp_dir ]

    elif command != 'sdist':
      raise ErrorDistCommandInvalid( command )
    
    formats = set()
    
    if args:
      if isString( args ):
        args = args.split()
      else:
        args = toSequence( args )
      
      script_args += args
      
      for arg in args:
        if command.startswith('bdist'):
          if arg.startswith( '--formats=' ):
            v = arg[len('--formats='):].split(',')
            formats.update( v )
          
          elif arg.startswith( '--plat-name=' ):
            v = arg[len('--plat-name='):]
            formats.add( v )
    
    script_args += [ '--dist-dir', target ]
    
    self.command = command
    self.target = target
    self.script_args = script_args
    self.formats = formats

  #//-------------------------------------------------------//

  def   getTraceName(self, brief ):
    return "distutils %s" % ' '.join(self.script_args)

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
  
  def   ExecuteCommand( self, options, target = None, target_flag = None ):
    return ExecuteCommand( options, target = target, target_flag = target_flag )
  
  def   CopyFiles(self, options, target ):
    return CopyFilesBuilder( options, target )
  
  def   CopyFileAs(self, options, target ):
    return CopyFileAsBuilder( options, target )
  
  def   WriteFile(self, options, target, binary = False, encoding = None ):
    return WriteFileBuilder( options, target, binary = binary, encoding = encoding )

  def   CreateDist( self, options, target, command, args = None ):
    return DistBuilder( options, target = target, command = command, args = args )
  
  def   InstallDist( self, options, user = True ):
    return InstallDistBuilder( options, user = user )
  
  def   CreateZip(self, options, target, rename = None, basedir = None, ext = None ):
    return ZipFilesBuilder( options, target = target, rename = rename, basedir = basedir, ext = ext )
  
  def   CreateTar(self, options, target, mode = None, rename = None, basedir = None, ext = None ):
    return TarFilesBuilder( options, target = target, mode = mode, rename = rename, basedir = basedir, ext = ext )
