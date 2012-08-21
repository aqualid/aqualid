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

import hashlib

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
    'name',
    'name_key',
    'build_dir',
    'do_path_merge',
  )
   
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, node ):
    """
    Builds the node and returns values: targets, intermediate targets, impicit dependencies
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    if attr == 'name_key':
      chcksum = hashlib.md5()
      
      for name in toSequence( self.name ):
        chcksum.update( name.encode() )
      
      name_key = chcksum.digest()
      
      self.name_key = name_key
      return name_key
    
    if attr = 'build_dir':
      build_dir_prefix  = self.options.build_dir_prefix.value()
      build_dir_name    = self.options.build_dir_name.value()
      build_dir_suffix  = self.options.build_dir_suffix.value()
      self.build_dir = FilePath( os.path.abspath( os.path.join( build_dir_prefix, build_dir_name, build_dir_suffix ) ) )
      self.do_path_merge = not build_dir_suffix
      return self.build_dir
    
    raise UnknownAttribute( self, attr )
  
  #//-------------------------------------------------------//
  
  def   values( self ):
    """
    Returns builder values
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   clean( self, node, target_values, itarget_values ):
    """
    Cleans produced values
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   buildPath( self, src_path ):
    if src_path is None:
      return self.build_dir
    
    src_path = FilePath( src_path )
    
    if self.do_path_merge:
      return self.build_dir.mergePath( src_path )
    
    return FilePath( os.path.join( self.build_dir, src_path.name_ext ) )
  
  #//-------------------------------------------------------//
  
  def   buildPaths( self, src_paths ):
    return FilePaths( map(self.getBuildPath, toSequence( src_paths ) ) )

