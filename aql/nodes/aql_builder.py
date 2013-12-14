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
  'Builder',
)

import os
import errno

from aql.util_types import toSequence, FilePath, FilePaths
from aql.values import Value, FileValue, FileContentChecksum, FileContentTimeStamp

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

def   _buildPath( build_path, strip_src_path, src_path = None ):
  
  if not src_path:
    filename = ''
  
  else:
    src_path = FilePath( src_path )
    filename = src_path.name_ext
    
    if not strip_src_path:
      build_path = build_path.merge( src_path.dir )
    
  _makeDir( build_path )
  
  return build_path.join( filename )

#//===========================================================================//

def   _makeFileValues( content_type, values, use_cache ):
  
  file_values = []
  values = toSequence( values )
  for value in values:
    if not isinstance( value, Value ):
      value = FileValue( value, content = content_type, use_cache = use_cache )
    file_values.append( value )
  
  return file_values

#//===========================================================================//

# noinspection PyAttributeOutsideInit
class Builder (object):
  """
  Base class for all builders
  
  'options' - builder's options
  'name' - uniquely identifies builder
  'signature' - uniquely identifies builder's parameters
  
  """
  
  __slots__ = (
    'options',
    'name',
    'signature',
  )
   
  #//-------------------------------------------------------//
  
  def   __new__(cls, options, *args, **kw):
    
    self = super(Builder, cls).__new__(cls)
    self.options = options
    
    return self
  
  #//-------------------------------------------------------//
  
  def getName( self ):
      cls = self.__class__
      build_dir = self.options.build_path.get()
      return '.'.join( [ cls.__module__, cls.__name__, str(build_dir) ] )
  
  #//-------------------------------------------------------//
  
  def   getSignature( self ):
    raise NotImplementedError( "Must be implemented in a child class.")
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    
    if attr == 'name':
      self.name = name = self.getName()
      return name
    
    elif attr == 'signature':
      self.signature = signature = self.getSignature()
      return signature
    
    raise AttributeError( "%s instance has no attribute '%s'" % (type(self), attr) )
  
  #//-------------------------------------------------------//
  
  def   actual( self, vfile, node ):
    return node.actual( vfile )

  #//-------------------------------------------------------//

  # noinspection PyMethodMayBeStatic
  def   save( self, vfile, node ):
    vfile.addValues( node.values() )
  
  #//-------------------------------------------------------//
  
  def   prebuild( self, vfile, node ):
    """
    Could be used to dynamically generate nodes which need to be built before the passed node
    Returns list of nodes
    """
    return None
  
  #//-------------------------------------------------------//
  
  def   prebuildFinished( self, vfile, node, prebuild_nodes ):
    """
    Called when all node returned by the prebuild() method has been built
    """
    pass
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    """
    Builds a node
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//

  # noinspection PyMethodMayBeStatic
  def   clear( self, vfile, node ):
    """
    Cleans produced values
    """
    node.load( vfile )
    
    for value in node.targets():
      value.remove()
    
    for value in node.sideEffects():
      value.remove()
    
    vfile.removeValues( node.values() )
  
  #//-------------------------------------------------------//
  
  def   buildStr( self, node ):
    """
    Returns user friendly builder action string
    """
    file_names = tuple( src.get() for src in node.sources() )
    return str(self) + ': ' + ', '.join( file_names )
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    return self.name
  
  #//-------------------------------------------------------//
  
  def   buildPath( self, src_path = None ):
    options = self.options
    return _buildPath( options.build_path.get(), bool(options.build_dir_suffix.get()), src_path )
  
  #//-------------------------------------------------------//
  
  def   buildPaths( self, src_paths ):
    return FilePaths( map(self.buildPath, toSequence( src_paths ) ) )
  
  #//-------------------------------------------------------//
  
  def   __fileContentType( self ):
    content_type = NotImplemented
    
    file_signature = self.options.file_signature
    
    if file_signature == 'checksum':
      content_type = FileContentChecksum
    
    elif file_signature == 'timestamp':
      content_type = FileContentTimeStamp
    
    return content_type
  
  #//-------------------------------------------------------//
  
  def   makeValues( self, values, use_cache = False ):
    return self.makeFileValues( values, use_cache )
  
  #//-------------------------------------------------------//
  
  def   makeFileValues( self, values, use_cache = False ):
    content_type = self.__fileContentType()
    return _makeFileValues( content_type, values, use_cache )
  

