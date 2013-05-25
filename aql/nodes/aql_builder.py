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
  'Builder', 'RebuildNode',
)

import os
import errno

from aql.types import toSequence, FilePath, FilePaths
from aql.values import Value, FileValue, FileContentChecksum, FileContentTimeStamp
from .aql_node import Node, NodeTargets

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
  
  filename = ''
  
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

class RebuildNode( Exception ):
  pass

#//===========================================================================//

class Builder (object):
  """
  Base class for all builders
  """
  
  __slots__ = (
    'options',
    'name',
    'signature',
  )
   
  #//-------------------------------------------------------//
  
  def   __new__(cls, options, *args, **kw):
    
    self = super(Builder,cls).__new__(cls)
    self.options = options
    
    return self
  
  #//-------------------------------------------------------//
  
  def getName( self ):
      cls = self.__class__
      build_dir = self.buildPath()
      return '.'.join( [ cls.__module__, cls.__name__, str(build_dir) ] )
      return self.name
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    
    if attr == 'name':
      self.name = name = self.getName()
      return name
    
    elif attr == 'signature':
      """
      Sets builder signature which uniquely identify builder's parameters
      """
      raise NotImplementedError( "Attribute '%s' must be set in a child class." % attr )
    
    raise AttributeError( "%s instance has no attribute '%s'" % (type(self), attr) )
  
  #//-------------------------------------------------------//
  
  def   prebuild( self, build_manager, vfile, node ):
    """
    Could be used to dynamically generate nodes which need to be built before the passed node
    Returns list of nodes
    """
    return None
  
  #//-------------------------------------------------------//
  
  def   prebuildFinished( self, build_manager, vfile, node, prebuild_nodes ):
    """
    Called when all node returned by the prebuild() methods has been built
    """
    pass
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, vfile, node, prebuild_nodes = None ):
    """
    Builds the node and returns a <NodeTargets> object.
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   clear( self, node, target_values, itarget_values ):
    """
    Cleans produced values
    """
    for value in target_values:
      value.remove()
    
    for value in itarget_values:
      value.remove()
  
  #//-------------------------------------------------------//
  
  def   buildStr( self, node ):
    """
    Returns user friendly builder action string
    """
    return str(self) + ': ' + ', '.join( map( str, node.sources() ) )
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    return self.name
  
  #//-------------------------------------------------------//
  
  def   buildPath( self, src_path = None ):
    options = self.options
    return _buildPath( options.build_path.value(), bool(options.build_dir_suffix.value()), src_path )
  
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
  
  def   makeSourceValues( self, values ):
    return makeFileValues( values )
  
  #//-------------------------------------------------------//
  
  def   makeFileValues( self, values, use_cache = True ):
    content_type = self.__fileContentType()
    return _makeFileValues( content_type, values, use_cache )
  
  #//-------------------------------------------------------//
  
  def   makeNodeFileTargets( self, targets = None, itargets = None, ideps = None, use_cache = True ):
    
    content_type = self.__fileContentType()
    
    target_values = _makeFileValues( content_type, targets, use_cache = False )
    itarget_values = _makeFileValues( content_type, itargets, use_cache = False )
    idep_values = _makeFileValues( content_type, ideps, use_cache = use_cache )
    
    return NodeTargets( target_values, itarget_values, idep_values )

