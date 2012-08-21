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

from aql_path_types import FilePath

class BuildPathMapper( object ):
  
  __slots__ = (
    'build_dir',
    'has_suffix',
  )
  
  def   __init__( self, build_dir_prefix, build_dir_name, build_dir_suffix ):
    
    self.build_dir  = FilePath( os.path.abspath( os.path.join( build_dir_prefix, build_dir_name, build_dir_suffix ) ) )
    self.has_suffix = bool(build_dir_suffix)
  
  #//-------------------------------------------------------//
  
  def   getBuildPath( self, src_path = None ):
    if src_path is None:
      return self.build_dir
    
    src_path = FilePath( src_path )
    
    if self.has_suffix:
      return os.path.join( self.build_dir, src_path.name_ext )
    
    return self.build_dir.mergePath( src_path )
  
  #//-------------------------------------------------------//
  
  def   getBuildPaths( self, src_paths ):
    return FilePaths( map(self.getBuildPath, toSequence( src_paths ) ) )

#//===========================================================================//

def   addPrefix( prefix, values ):
  return map( lambda v, prefix = prefix: prefix + v, values )

#//===========================================================================//

def   moveFile( src_file, dst_file ):
  dst_file = FilePath( dst_file )
  if not os.path.isdir( dst_file.dir ):
    os.makedirs( dst_file.dir )
  shutil.move( src_file, dst_file )

#//===========================================================================//

def   moveFiles( src_files, dst_files ):
  moved_files = FilePaths()
  for src_file, dst_file in zip( src_files, dst_files ):
    if os.path.isfile( src_file ):
      moveFile( src_file, dst_file )
      moved_files.append( dst_file )
  
  return moved_files
