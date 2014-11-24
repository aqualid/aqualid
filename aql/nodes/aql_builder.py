#
# Copyright (c) 2011-2014 The developers of Aqualid project
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
from aql.util_types.aql_list_types import toSequence

__all__ = (
  'Builder', 'FileBuilder'
)

import os
import errno
import operator

from aql.util_types import FilePath
from aql.utils import simpleObjectSignature, simplifyValue, executeCommand, eventDebug, groupPathsByDir, groupItems, relativeJoin, relativeJoinList
from aql.values import ValueBase, FileChecksumValue, FileTimestampValue, SimpleValue

#//===========================================================================//

@eventDebug
def   eventExecCmd( settings, cmd, cwd, env ):
  # from aql.utils import logDebug
  # cmd = ' '.join( cmd )
  # logDebug("EXEC: %s" % (cmd, ) )
  pass

#//===========================================================================//

def   _makeBuildPath( path_dir, _path_cache = set() ):
  if path_dir not in _path_cache:
    if not os.path.isdir( path_dir ):
      try:
        os.makedirs( path_dir )
      except OSError as e:
        if e.errno != errno.EEXIST:
          raise
    
    _path_cache.add( path_dir )

#//===========================================================================//

def   _makeBuildPaths( dirnames ):
  for dirname in dirnames:
    _makeBuildPath( dirname )

#//===========================================================================//

def   _splitFileName( file_path, ext = None, prefix = None, suffix = None ):
  if isinstance( file_path, ValueBase ):
    file_path = file_path.get()
  
  dirname, filename = os.path.split( file_path )
  
  name, path_ext = os.path.splitext( filename )
  if ext is None: ext = path_ext
  if prefix: name = prefix + name
  if suffix: name += suffix
  filename = name + ext
  
  return dirname, filename

#//===========================================================================//

def   _splitFileNames( file_paths, ext = None, prefix = None, suffix = None ):
  dirnames = []
  filenames = []
  for file_path in file_paths:
    dirname, filename = _splitFileName( file_path, ext, prefix, suffix )
    dirnames.append( dirname )
    filenames.append( filename )
  
  return dirnames, filenames

#//===========================================================================//

def   _fileSinature2Type( file_signature_type ):
  return FileTimestampValue if file_signature_type == 'timestamp' else FileChecksumValue

#//===========================================================================//

class BuilderInitiator( object ):
  
  __slots__ = ( 'is_initiated', 'builder', 'options', 'args', 'kw' )
  
  def   __init__( self, builder, options, args, kw ):
    
    self.is_initiated   = False
    self.builder        = builder
    self.options        = options
    self.args           = self.__storeArgs( args )
    self.kw             = self.__storeKw( kw )
  
  #//=======================================================//
  
  def   __storeArgs( self, args ):
    return tuple( map( self.options._storeValue, args ) )
  
  #//=======================================================//
  
  def   __loadArgs( self ):
    return tuple( map( self.options._loadValue, self.args ) )
  
  #//=======================================================//
  
  def   __storeKw( self, kw ):
    storeValue = self.options._storeValue
    return dict( (name, storeValue( value )) for name, value in kw.items() )
  
  #//=======================================================//
  
  def   __loadKw( self ):
    loadValue = self.options._loadValue
    return dict( (name, loadValue( value )) for name, value in self.kw.items() )
  
  #//=======================================================//
  
  def   initiate( self ):
    
    if self.is_initiated:
      return self.builder
    
    builder = self.builder
    
    kw = self.__loadKw()
    args = self.__loadArgs()
    
    options = self.options
    
    builder._initAttrs( options )
    
    builder.__init__( options, *args, **kw )
    
    if not hasattr( builder, 'name' ):
      builder.setName()
    
    if not hasattr( builder, 'signature' ):
      builder.setSignature()
    
    self.is_initiated = True
    
    return builder
  
  #//=======================================================//
  
  def   canBuildBatch(self):
    return self.builder.canBuildBatch()
  
  def   canBuild(self):
    return self.builder.canBuild()
  
  def   isBatch(self):
    return self.builder.isBatch()
  
#//===========================================================================//

# noinspection PyAttributeOutsideInit
class Builder (object):
  """
  Base class for all builders
  
  'name' - uniquely identifies builder
  'signature' - uniquely identifies builder's parameters
  
  """
  
  NAME_ATTRS = None
  SIGNATURE_ATTRS = None
  
  #//-------------------------------------------------------//
        
  def   __new__(cls, options, *args, **kw):
    
    self = super(Builder, cls).__new__(cls)
    self.makeValue = self.makeSimpleValue
    self.default_value_type = SimpleValue
    
    self.__is_batch = (options.batch_build.get() or not self.canBuild()) and self.canBuildBatch()
    
    return BuilderInitiator( self, options, args, kw )
  
  #//-------------------------------------------------------//
  
  def   _initAttrs( self, options ):
    self.build_dir = options.build_dir.get()
    self.build_path = options.build_path.get()
    self.relative_build_paths = options.relative_build_paths.get()
    self.file_value_type = _fileSinature2Type( options.file_signature.get() )
    self.env = options.env.get().dump()
  
  #//-------------------------------------------------------//
  
  def   canBuildBatch(self):
    return self.__class__.buildBatch != Builder.buildBatch
  
  #//-------------------------------------------------------//
  
  def   canBuild(self):
    return self.__class__.build != Builder.build
  
  #//-------------------------------------------------------//
  
  def   isBatch(self):
    return self.__is_batch
  
  #//-------------------------------------------------------//
  
  def   initiate( self ):
    return self
  
  #//-------------------------------------------------------//

  def setName( self ):
    
    cls = self.__class__
    name = [ cls.__module__, cls.__name__, simplifyValue( self.build_path ), bool(self.relative_build_paths) ]
    
    if self.NAME_ATTRS:
      for attr_name in self.NAME_ATTRS:
        value = getattr( self, attr_name )
        value = simplifyValue( value )
        name.append( value )
            
    self.name = simpleObjectSignature( name )
  
  #//-------------------------------------------------------//
  
  def   setSignature( self ):
    sign = []
    
    if self.SIGNATURE_ATTRS:
      for attr_name in self.SIGNATURE_ATTRS:
        value = getattr( self, attr_name )
        value = simplifyValue( value )
        sign.append( value )
    
    self.signature = simpleObjectSignature( sign )
  
  #//-------------------------------------------------------//

  def   clear( self, node ):
    node.removeTargets()
  
  #//-------------------------------------------------------//
  
  def   depends( self, node ):
    """
    Could be used to dynamically generate dependency nodes 
    Returns list of dependency nodes or None
    """
    return None
  
  #//-------------------------------------------------------//
  
  def   replace( self, node ):
    """
    Could be used to dynamically replace sources
    Returns list of nodes/values or None (if sources are not changed)
    """
    return None
  
  #//-------------------------------------------------------//
  
  def   split( self, node ):
    """
    Could be used to dynamically split building sources to several nodes
    Returns list of nodes or None
    """
    return None
  
  #//-------------------------------------------------------//
  
  def   splitSingle( self, node ):
    """
    Splits each source to separate nodes 
    Returns list of nodes or None
    """
    source_values = node.getSourceValues()
    if len(source_values) < 2:
      return None
    
    return tuple( node.split( src_value ) for src_value in source_values )
  
  #//-------------------------------------------------------//
  
  def   splitBatchByBuildDir( self, node ):
    src_groups = self.groupSourcesByBuildDir( node )
    if len(src_groups) < 2:
      return None
    
    return tuple( node.split( src_group ) for src_group in src_groups )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    """
    Builds a node
    Returns a build output string or None
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   buildBatch( self, node ):
    """
    Builds a node
    Returns a build output string or None
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   getTargetValues( self, source_values ):
    """
    If it's possible returns target values of the node, otherwise None 
    """
    return None
  
  #//-------------------------------------------------------//
  
  def   getTraceName(self, brief ):
    return self.__class__.__name__
  
  #//-------------------------------------------------------//
  
  def   getTraceSources( self, node, brief ):
    return node.getSourceValues()

  #//-------------------------------------------------------//
  
  def   getTraceTargets( self, node, brief ):
    return node.getBuildTargetValues()

  #//-------------------------------------------------------//
  
  def   getBuildStrArgs( self, node, brief ):
    
    try:
      name = self.getTraceName( brief )
    except Exception:
      name = ''
    
    try:
      sources = self.getTraceSources( node, brief )
    except Exception:
      sources = None

    try:
      targets = self.getTraceTargets( node, brief )
    except Exception:
      targets = None
    
    return name, sources, targets
  
  #//-------------------------------------------------------//
  
  def   getBuildDir( self ):
    _makeBuildPath( self.build_dir )
    
    return self.build_dir
  
  #//-------------------------------------------------------//
  
  def   getBuildPath( self ):
    _makeBuildPath( self.build_path )
    return self.build_path
  
  #//-------------------------------------------------------//
  
  def   getFileBuildPath( self, file_path, ext = None, prefix = None, suffix = None ):
    build_path = self.build_path
    
    dirname, filename = _splitFileName( file_path, ext, prefix, suffix )
    
    if self.relative_build_paths:
      build_path = relativeJoin( build_path, dirname )
    
    _makeBuildPath( build_path )
    
    build_path = os.path.join( build_path, filename )
    
    return FilePath( build_path )
  
  #//-------------------------------------------------------//
  
  def   getFileBuildPaths( self, file_paths, ext = None, prefix = None, suffix = None ):
    build_path = self.build_path
    
    dirnames, filenames = _splitFileNames( file_paths, ext, prefix, suffix )
    
    if self.relative_build_paths:
      dirnames = relativeJoinList( build_path, dirnames )
      _makeBuildPaths( dirnames )
     
      build_paths = [ FilePath( os.path.join( dirname, filename ) ) for dirname, filename in zip( dirnames, filenames ) ]
    
    else:
      _makeBuildPath( build_path )
      
      build_paths = [ FilePath( os.path.join( build_path, filename ) ) for filename in filenames ]
    
    return build_paths
  
  #//-------------------------------------------------------//
  
  def   groupSourcesByBuildDir( self, node ):
    src_files = node.getSourceValues()
    
    num_groups = node.options.batch_groups.get()
    group_size = node.options.batch_size.get()
    
    if self.relative_build_paths:
      groups = groupPathsByDir( src_files, num_groups, group_size, pathGetter = operator.methodcaller('get') )
    else:
      groups = groupItems( src_files, num_groups, group_size )
    
    return groups
  
  #//-------------------------------------------------------//
  
  def   getDefaultValueType( self ):
    return self.default_value_type 
  
  #//-------------------------------------------------------//
  
  def   getFileValueType( self ):
    return self.file_value_type 
  
  #//-------------------------------------------------------//
  
  def   makeSimpleValue(self, value, tags = None, use_cache = False ):
    if isinstance( value, ValueBase):
      return value
    
    if isinstance( value, FilePath ):
      return self.file_value_type( name = value, tags = tags, use_cache = use_cache )
    
    return SimpleValue( value )
  
  #//-------------------------------------------------------//
  
  def   makeFileValue( self, value, tags = None, use_cache = False ):
    if isinstance( value, ValueBase ):
      return value
    
    return self.file_value_type( name = value, tags = tags, use_cache = use_cache )
  
  #//-------------------------------------------------------//
  
  def   makeFileValues( self, values, tags = None, use_cache = False ):
    make_value = self.makeFileValue
    return [ make_value( value, tags = tags, use_cache = use_cache ) for value in toSequence( values ) ]
  
  #//-------------------------------------------------------//
  
  def   execCmd(self, cmd, cwd = None, env = None, file_flag = None, stdin = None ):
    
    result = self.execCmdResult( cmd, cwd = cwd, env = env, file_flag = file_flag, stdin = stdin )
    if result.failed():
      raise result
    
    return result.output
  
  #//-------------------------------------------------------//
  
  def   execCmdResult(self, cmd, cwd = None, env = None, file_flag = None, stdin = None ):
    
    if env is None:
      env = self.env
    
    if cwd is None:
      cwd = self.getBuildPath()
    
    result = executeCommand( cmd, cwd = cwd, env = env, file_flag = file_flag, stdin = stdin )
    
    eventExecCmd( cmd, cwd, env )
    
    return result

#//===========================================================================//

class FileBuilder (Builder):
  def   _initAttrs( self, options ):
    super(FileBuilder,self)._initAttrs( options )
    self.makeValue = self.makeFileValue
    self.default_value_type = self.file_value_type
