#
# Copyright (c) 2011-2014 The developers of Aqualid project - http://aqualid.googlecode.com
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

__all__ = (
  'Builder', 'FileBuilder', 'BuildSingle', 'BuildBatch',
)

import os
import errno

from aql.util_types import isString, toSequence, FilePath
from aql.utils import simpleObjectSignature, simplifyValue, executeCommand, eventDebug, Chdir
from aql.values import ValueBase, FileValueBase, FileChecksumValue, FileTimestampValue, SimpleValue

#//===========================================================================//

@eventDebug
def   eventExecCmd( cmd, cwd, env ):
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

def   _fileSinature2Type( file_signature_type ):
  return FileTimestampValue if file_signature_type == 'timestamp' else FileChecksumValue

#//===========================================================================//

class BuilderInitiator( object ):
  
  __slots__ = ( 'is_initiated', 'builder', 'options', 'args', 'kw', 'cwd' )
  
  def   __init__( self, builder, options, args, kw ):
    
    self.is_initiated   = False
    self.builder        = builder
    self.options        = options
    self.args           = self.__storeArgs( args )
    self.kw             = self.__storeKw( kw )
    self.cwd            = os.path.abspath( os.getcwd() )
  
  #//=======================================================//
  
  def   __storeArgs( self, args ):
    return tuple( map( self.options._storeValue, args ) )
  
  #//=======================================================//
  
  def   __loadArgs( self ):
    return tuple( map( self.options._loadValue, self.args ) )
  
  #//=======================================================//
  
  def   __storeKw( self, kw ):
    storeValue = self.options._storeValue
    return { name: storeValue( value ) for name, value in kw.items() }
  
  #//=======================================================//
  
  def   __loadKw( self ):
    loadValue = self.options._loadValue
    return { name: loadValue( value ) for name, value in self.kw.items() }
  
  #//=======================================================//
  
  def   initiate( self ):
    
    if self.is_initiated:
      return self.builder
    
    builder = self.builder
    
    with Chdir( self.cwd ):
      
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
    return BuilderInitiator( self, options, args, kw )
  
  #//-------------------------------------------------------//
  
  def   _initAttrs(self, options ):
    self.build_dir = options.build_dir.get()
    self.build_path = options.build_path.get()
    self.relative_build_paths = options.relative_build_paths.get()
    self.file_value_type = _fileSinature2Type( options.file_signature.get() )
    self.env = options.env.get().dump()
  
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
  
  def   prebuild( self, node ):
    """
    Could be used to dynamically generate nodes which need to be built before the node
    Returns list of nodes or None
    """
    return None
  
  #//-------------------------------------------------------//
  
  def   prebuildFinished( self, node, prebuild_nodes ):
    """
    Called when all nodes returned by the prebuild() method have been built
    Returns True if node should not be built
    """
    return False
  
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
  
  def   getTargetValues( self, node ):
    """
    If it's possible returns target values of the node, otherwise None 
    """
    return None
  
  #//-------------------------------------------------------//
  
  def   getTraceName(self, brief ):
    return self.__class__.__name__
  
  #//-------------------------------------------------------//
  
  def   getTraceSources( self, node, brief, batch ):
    values = node.getBatchSourceValues() if batch else node.getSourceValues()
    return values
  
  #//-------------------------------------------------------//
  
  def   getTraceTargets( self, node, brief, batch ):
    values = node.getBatchTargetValues() if batch else node.getTargetValues()
    return values
  
  #//-------------------------------------------------------//
  
  def   getBuildStrArgs( self, node, brief, batch ):
    
    try:
      name = self.getTraceName( brief )
    except Exception:
      name = ''
    
    try:
      sources = self.getTraceSources( node, brief, batch )
    except Exception:
      sources = None

    try:
      targets = self.getTraceTargets( node, brief, batch )
    except Exception:
      targets = None
    
    return name, sources, targets
  
  #//-------------------------------------------------------//
  
  def   getBuildDir( self ):
    _makeBuildPath( self.build_dir )
    
    return self.build_dir
  
  #//-------------------------------------------------------//
  
  def   getBuildPath( self, src_path = None ):
    build_path = self.build_path
    
    if not src_path:
      filename = ''
    
    else:
      src_path = FilePath( src_path )
      filename = src_path.filename()
      
      if self.relative_build_paths:
        build_path = build_path.joinFromCommon( src_path.dirname() )
      
    _makeBuildPath( build_path )
    
    return build_path.join( filename )
  
  #//-------------------------------------------------------//
  
  def   fileValueType( self ):
    return self.file_value_type 
  
  #//-------------------------------------------------------//
  
  def   makeValue(self, value, use_cache = False ):
    if isinstance( value, ValueBase):
      return value
    
    if isinstance( value, FilePath ):
      return self.fileValueType()( name = value, use_cache = use_cache )
    
    return SimpleValue( value )
  
  #//-------------------------------------------------------//
  
  def   makeFileValue( self, value, use_cache = False ):
    if isinstance( value, ValueBase):
      return value
    
    return self.fileValueType()( name = value, use_cache = use_cache )
  
  #//-------------------------------------------------------//
  
  def   makeValues( self, values, use_cache = False ):
    return tuple( self.makeValue( value, use_cache = use_cache ) for value in toSequence(values) )
  
  #//-------------------------------------------------------//
  
  def   makeFileValues( self, values, use_cache = False ):
    
    file_type = self.fileValueType()
    file_values = []
    
    for value in toSequence(values):
      if not isinstance(value, ValueBase):
        value = file_type( name = value, use_cache = use_cache )
      
      file_values.append( value )
    
    return tuple( file_values )
  
  #//-------------------------------------------------------//
  
  def   execCmd(self, cmd, cwd = None, env = None, file_flag = None, stdin = None ):
    
    if env is None:
      env = self.env
    
    if cwd is None:
      cwd = self.getBuildPath()
    
    result = executeCommand( cmd, cwd = cwd, env = env, file_flag = file_flag, stdin = stdin )
    if result.failed():
      raise result
    
    eventExecCmd( cmd, cwd, env )
    
    return result.out

#//===========================================================================//

class FileBuilder (Builder):
  def   _initAttrs( self, options ):
    super(FileBuilder,self)._initAttrs( options )
    self.makeValue  = self.makeFileValue
    self.makeValues = self.makeFileValues

#//===========================================================================//  

class BuildSingle(object):
  
  def   __init__(self, builder ):
    self.builder = builder
  
  #//-------------------------------------------------------//
  
  def   initiate( self ):
    self.builder = self.builder.initiate()
    return self
  
  #//-------------------------------------------------------//
  
  def   __getattr__(self, attr ):
    value = getattr(self.builder, attr )
    setattr( self, attr, value )
    return value
  
  #//-------------------------------------------------------//
  
  def   clear( self, node ):
    pass
  
  #//-------------------------------------------------------//
  
  def   prebuild( self, node ):
    
    sources = node.getSourceValues()
    if len(sources) > 1:
      return node.split( self.builder )
    
    node.builder = self.builder
    return None
  
  #//-------------------------------------------------------//
  
  def   prebuildFinished( self, node, pre_nodes ):
    
    targets = []
    for pre_node in pre_nodes:
      targets += pre_node.getTargetValues()
    
    node.setTargets( targets )
    
    return True

#//===========================================================================//  

class BuildBatch(object):
  
  def   __init__(self, builder ):
    self.builder = builder
  
  #//-------------------------------------------------------//
  
  def   initiate( self ):
    builder = self.builder
    self.builder = builder = builder.initiate()
    return builder
  
  #//-------------------------------------------------------//
  
  def   __getattr__(self, attr ):
    value = getattr(self.builder, attr )
    setattr( self, attr, value )
    return value
