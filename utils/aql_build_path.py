#
# Copyright (c) 2012 The developers of Aqualid project - http://aqualid.googlecode.com
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

import os.path

from aql_simple_types import FilePath

class BuildPathMapper( object ):
  
  __slots__ = (
    'build_dir',
    'build_dir_seq',
    'has_suffix',
  )
  
  def   __init__( self, build_dir_prefix, build_dir_name, build_dir_suffix ):
    
    build_dir = os.path.abspath( os.path.join( build_dir_prefix, build_dir_name, build_dir_suffix ) )
    
    self.build_dir      = build_dir
    self.build_dir_seq  = self.__seqPath( build_dir )
    self.has_suffix     = bool(build_dir_suffix)
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __seqPath( path ):
    path = path.replace(':', os.path.sep)
    path = list( map( FilePath, filter( None, path.split( os.path.sep ) ) ) )
    
    return path
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def __commonSeqPathSize( seq_path1, seq_path2 ):
    for i, parts in enumerate( zip( seq_path1, seq_path2 ) ):
      if parts[0] != parts[1]:
        return i
    
    return i + 1
  
  #//-------------------------------------------------------//
  
  def   getBuildPath( self, src_path = None ):
    if src_path is None:
      return self.build_dir
    
    if self.has_suffix:
      return os.path.join( self.build_dir, os.path.basename( src_path ) )
    
    src_path = os.path.abspath( src_path )
    src_path_seq = self.__seqPath( src_path )
    
    common_size = self.__commonSeqPathSize( self.build_dir_seq, src_path_seq )
    
    src_path_seq[ 0 : common_size ] = [ self.build_dir ]
    src_build_path = os.path.join( *src_path_seq )
    
    return src_build_path
