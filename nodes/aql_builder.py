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

import os

from aql_utils import toSequence
from aql_path_types import FilePath, FilePaths

class RebuildNode( Exception ):
  pass

#//===========================================================================//

class Builder (object):
  """
  Base class for all builders
  """
  
  __slots__ = (
    'env',
    'options',
    'build_dir',
    'do_path_merge',
  )
   
  #//-------------------------------------------------------//
  
  def   prebuild( self, vfile, node ):
    """
    Could be used to dynamically generate nodes which need to be built before the passed node
    """
    return None
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, vfile, node, prebuild_nodes = None ):
    """
    Builds the node and returns values: NodeTargets
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    
    if attr == 'build_dir':
      self.build_dir = self.options.build_dir.value()
      return self.build_dir
    
    if attr == 'do_path_merge':
      self.do_path_merge = self.options.do_build_path_merge.value()
      return self.do_path_merge
    
    raise AttributeError( self, attr )
  
  #//-------------------------------------------------------//
  
  def   name( self ):
    """
    Returns name of builder.By default it's <ModuleName>.<ClassName>
    """
    cls = self.__class__
    return cls.__module__ + '.' + cls.__name__
  
  #//-------------------------------------------------------//
  
  def   signature( self ):
    """
    Returns builder signature which uniquely identify builder's parameters
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
    return str(self) + ': ' + ','.join( map( str, node.sources() ) )
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    return self.name()
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __makeDir( path_dir, _path_cache = set() ):
    if path_dir not in _path_cache:
      if not os.path.isdir( path_dir ):
        os.makedirs( path_dir )
      
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
  

