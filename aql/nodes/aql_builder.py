#
# Copyright (c) 2011-2013 The developers of Aqualid project - http://aqualid.googlecode.com
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
  'Builder', 'BuildSplitter',
)

import os
import errno

from aql.util_types import toSequence, FilePath, UniqueList
from aql.utils import dumpData, newHash, executeCommand
from aql.values import Value, FileValue, FileName
from aql.values import FileContentChecksum, FileContentTimeStamp

from .aql_node import Node

#//===========================================================================//

def   _makeDir( path_dir, _path_cache = set() ):
  if path_dir not in _path_cache:
    if not os.path.isdir( path_dir ):
      try:
        os.makedirs( path_dir )
      except OSError as e:
        if e.errno != errno.EEXIST:
          raise
    
    _path_cache.add( path_dir )

#//===========================================================================//

_SIMPLE_TYPES = (str,int,float,complex,bool,bytes,bytearray)

def  _evaluateValue( value, simple_types = _SIMPLE_TYPES ):
  
  if isinstance( value, simple_types ):
    return value
  
  if isinstance( value, (list, tuple, UniqueList, set, frozenset) ):
    result = []
    
    for v in value:
      result.append( _evaluateValue( v ) )
          
    return result
  
  if isinstance( value, dict ):
    result = {}
    
    for key,v in value.items():
      result[ key ] = _evaluateValue( v )
    
    return result
  
  if isinstance( value, Value ):
    return value.get()
  
  if isinstance( value, Node ):
    return value.get()
  
  return value

#//===========================================================================//

class BuilderInitiator( object ):
  
  __slots__ = ( 'is_initiated', 'builder', 'options', 'args', 'kw', 'options_kw' )
  
  def   __init__( self, builder, options, args, kw ):
    
    self.is_initiated   = False
    self.builder        = builder
    self.options        = options
    self.args           = args
    self.kw             = kw
    self.options_kw     = None
  
  #//=======================================================//
  
  def   setOptionsKw(self, options_kw ):
    self.options_kw = options_kw
  
  #//=======================================================//
  
  @staticmethod
  def   __evalKW( kw, _evalValue = _evaluateValue ):
    return { name: _evalValue( value ) for name, value in kw.items() }
  
  #//=======================================================//
  
  def   initiate( self ):
    if self.is_initiated:
      return self.builder
    
    kw = self.__evalKW( self.kw )
    args = map( _evaluateValue, self.args )
    
    options = self.options
    
    options_kw = self.options_kw
    if options_kw:
      options = options.override()
      options_kw = self.__evalKW( options_kw )
      options.update( options_kw )
    
    builder = self.builder
    
    builder.build_path = options.build_path.get()
    builder.strip_src_dir = bool(options.build_dir_suffix.get())
    builder.file_signature_type = options.file_signature.get()
    builder.env = options.env.get().dump()
    
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
  
  def   initiate( self ):
    return self
  
  #//-------------------------------------------------------//

  def setName( self ):
    
    cls = self.__class__
    name = [ cls.__module__, cls.__name__, self.build_path, self.strip_src_dir ]
    
    if self.NAME_ATTRS:
      for attr_name in self.NAME_ATTRS:
        value = getattr( self, attr_name )
        name.append( value )
            
    self.name = tuple( name )
  
  #//-------------------------------------------------------//
  
  def   setSignature( self ):
    sign = []
    
    if self.SIGNATURE_ATTRS:
      for attr_name in self.SIGNATURE_ATTRS:
        value = getattr( self, attr_name )
        sign.append( value )
    
    sign = dumpData( sign )
    
    self.signature = newHash( sign ).digest()
  
  #//-------------------------------------------------------//
  
  def   actual( self, vfile, node ):
    
    result = node.actual( vfile )
    
    if  __debug__:
      print("builder.actual(): result: %s, node: %s" % (result, node.getName()))
    
    return result

  #//-------------------------------------------------------//

  # noinspection PyMethodMayBeStatic
  def   save( self, vfile, node ):
    if  __debug__:
      print("builder.save(): node: %s" % (node.getName(), ))
    node.save( vfile )
  
  #//-------------------------------------------------------//
  
  def   prebuild( self, vfile, node ):
    """
    Could be used to dynamically generate nodes which need to be built before the node
    Returns list of nodes
    """
    return None
  
  #//-------------------------------------------------------//
  
  def   prebuildFinished( self, vfile, node, prebuild_nodes ):
    """
    Called when all nodes returned by the prebuild() method have been built
    """
    pass
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    """
    Builds a node
    Returns a string of stdout/stderr or None
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   clear( self, node ):
    node.removeTargets()
  
  #//-------------------------------------------------------//

  def   getTargetValues( self, node ):
    """
    If it's possible returns target values of the node, otherwise None 
    """
    return None
  
  #//-------------------------------------------------------//
  
  def   getBuildStrArgs( self, node, detailed = False ):
    
    name = self.__class__.__name__
    sources = node.getSources()
    targets = node.getTargets()
    
    return name, sources, targets
  
  #//-------------------------------------------------------//
  
  def   getBuildPath( self, src_path = None ):
    build_path = self.build_path
    
    if not src_path:
      filename = ''
    
    else:
      src_path = FilePath( src_path )
      filename = src_path.name_ext
      
      if not self.strip_src_dir:
        build_path = build_path.merge( src_path.dir )
      
    _makeDir( build_path )
    
    return build_path.join( filename )
  
  #//-------------------------------------------------------//
  
  def   fileContentType( self ):
    content_type = NotImplemented
    
    file_signature = self.file_signature_type
    
    if file_signature == 'checksum':
      content_type = FileContentChecksum
    
    elif file_signature == 'timestamp':
      content_type = FileContentTimeStamp
    
    return content_type
  
  #//-------------------------------------------------------//
  
  def   makeValue(self, value, use_cache = False ):
    if isinstance( value, Value):
      return value
    
    if isinstance( value, (FileName, FilePath) ):
      return FileValue( name = value, content = self.fileContentType(), use_cache = use_cache )
      
    return Value( content = value, name = None )
  
  #//-------------------------------------------------------//
  
  def   makeFileValue( self, value, use_cache = False ):
    if isinstance( value, Value):
      return value
    
    return FileValue( name = value, content = self.fileContentType(), use_cache = use_cache )
  
  #//-------------------------------------------------------//
  
  def   makeValues( self, values, use_cache = False ):
    return tuple( self.makeValue( value, use_cache = use_cache ) for value in toSequence(values) )
  
  #//-------------------------------------------------------//
  
  def   makeFileValues( self, values, use_cache = False ):
    
    content_type = self.fileContentType()
    file_values = []
    
    for value in toSequence(values):
      if not isinstance(value, Value):
        value = FileValue( name = value, content = content_type, use_cache = use_cache )
      
      file_values.append( value )
    
    return tuple( file_values )
  
  #//-------------------------------------------------------//
  
  def   execCmd(self, cmd, cwd = None, env = None, file_flag = None ):
    
    if env is None:
      env = self.env
    
    if cwd is None:
      cwd = self.getBuildPath()
    
    result = executeCommand( cmd, cwd = cwd, env = env, file_flag = file_flag )
    if result.failed():
      raise result
    
    return result.out + '\n' + result.err

#//===========================================================================//  

class BuildSplitter(Builder):
  
  __slots__ = ('builder',)
  
  def   __init__( self, options, builder ):
    self.builder = builder.initiate()
    self.makeValue = self.builder.makeValue
  
  #//-------------------------------------------------------//
  
  def setName( self ):
      self.name = self.builder.name
  
  #//-------------------------------------------------------//
  
  def setSignature( self ):
      self.signature = self.builder.signature
  
  #//-------------------------------------------------------//
  
  def   save( self, vfile, node ):
    pass
  
  #//-------------------------------------------------------//
  
  def   actual( self, vfile, node ):
    return True
  
  #//-------------------------------------------------------//
  
  def   prebuild( self, vfile, node ):
    return node.split( self.builder )
  
  #//-------------------------------------------------------//
  
  def   prebuildFinished( self, vfile, node, pre_nodes ):
    
    targets = []
    for pre_node in pre_nodes:
      targets += pre_node.getTargetValues()
    
    node.setTargets( targets )
