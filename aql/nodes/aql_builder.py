#
# Copyright (c) 2011,2012 The developers of Aqualid project - http://aqualid.googlecode.com
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

from aql.utils import toSequence
from aql.types import FilePath, FilePaths
from aql.values import Value, FileValue

from .aql_node import NodeTargets

#//===========================================================================//

class RebuildNode( Exception ):
  pass

#//===========================================================================//

class Builder (object):
  """
  Base class for all builders
  """
  
  __slots__ = (
    'build_dir',
    'do_path_merge',
    'name',
    'signature',
    'scontent_type',
    'tcontent_type',
  )
   
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    
    if attr == 'name':
      cls = self.__class__
      self.name = '.'.join( [ cls.__module__, cls.__name__, str(self.build_dir), str(self.do_path_merge) ] )
      return self.name
    
    if attr == 'build_dir':
      self.build_dir = '.'
      return self.build_dir
    
    if attr == 'do_path_merge':
      self.do_path_merge = False
      return self.do_path_merge
    
    if attr == 'scontent_type':
      self.scontent_type = NotImplemented
      return self.scontent_type
    
    if attr == 'tcontent_type':
      self.tcontent_type = NotImplemented
      return self.tcontent_type
    
    if attr == 'signature':
      """
      Sets builder signature which uniquely identify builder's parameters
      """
      raise NotImplementedError( "Attribute '%s' must be set in a child class." % attr )
    
    raise AttributeError( self, attr )
  
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
  
  @staticmethod
  def   __makeDir( path_dir, _path_cache = set() ):
    if path_dir not in _path_cache:
      if not os.path.isdir( path_dir ):
        try:
          os.makedirs( path_dir )
        except OSError as e:
          if e.errno != errno.EEXIST:
            raise
      
      _path_cache.add( path_dir )
  
  #//-------------------------------------------------------//
  
  def   buildPath( self, src_path = None ):
    if src_path is None:
      build_path = self.build_dir
      self.__makeDir( build_path )
    else:
      src_path = FilePath( src_path )
      
      if self.do_path_merge:
        build_path = self.build_dir.merge( src_path )
      else:
        build_path = FilePath( os.path.join( self.build_dir, src_path.name_ext ) )
      
      self.__makeDir( build_path.dir )
    
    return build_path
  
  #//-------------------------------------------------------//
  
  def   buildPaths( self, src_paths ):
    return FilePaths( map(self.buildPath, toSequence( src_paths ) ) )
  
  #//-------------------------------------------------------//
  
  def   sourceValues( self, values, use_cache = True ):
    return [ self.sourceValue( value, use_cache ) for value in toSequence( values ) ]
  
  #//-------------------------------------------------------//
  
  def   sourceValue( self, value, use_cache = True ):
    if not isinstance( value, Value ):
      value = FileValue( value, content = self.scontent_type, use_cache = use_cache )
    
    return value
  
  #//-------------------------------------------------------//
  
  def   targetValues( self, values, use_cache = False ):
    content_type = self.tcontent_type
    dst_values = []
    for value in toSequence( values ):
      if not isinstance( value, Value ):
        value = FileValue( value, content = content_type, use_cache = use_cache )
      
      dst_values.append( value )
    
    return dst_values
  
  #//-------------------------------------------------------//
  
  def   nodeTargets( self, targets = None, itargets = None, ideps = None, use_cache = True ):
    target_values = self.targetValues( targets )
    itarget_values = self.targetValues( itargets )
    idep_values = self.targetValues( ideps, use_cache = use_cache )
    
    return NodeTargets( target_values, itarget_values, idep_values )

