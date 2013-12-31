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

__all__ = (
  'FilePath', 'FilePaths',
)

import os.path
import itertools

from .aql_simple_types import String, IgnoreCaseString
from .aql_list_types import UniqueList, ValueListType, toSequence

#//===========================================================================//

if os.path.normcase('ABC') == os.path.normcase('abc'):
  FilePathBase = IgnoreCaseString
else:
  FilePathBase = String

try:
  _splitunc = os.path.splitunc
except AttributeError:
  def _splitunc( path ):
    return str(), path

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class   FilePath (FilePathBase):
  
  #//-------------------------------------------------------//
  
  def     __new__(cls, path = None ):
    if type(path) is cls:
      return path
    
    if path is None:
        path = ''
    
    path = str(path)
    
    if path:
      path = os.path.normpath( path )
    
    return super(FilePath,cls).__new__( cls, path )
  
  #//-------------------------------------------------------//
  
  def   __getnewargs__(self):
    #noinspection PyRedundantParentheses
    return (str(self), )
  
  def   __getstate__(self):
    return {}
  def   __setstate__(self,state):
    pass
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __convert( other ):
    return other if isinstance( other, FilePath ) else FilePath( other )
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other ):
    return super(FilePath,self).__eq__( self.__convert( other ) )
  def   __ne__( self, other ):
    return super(FilePath,self).__ne__( self.__convert( other ) )
  def   __lt__( self, other ):
    return super(FilePath,self).__lt__( self.__convert( other ) )
  def   __le__( self, other ):
    return super(FilePath,self).__le__( self.__convert( other ) )
  def   __gt__( self, other ):
    return super(FilePath,self).__gt__( self.__convert( other ) )
  def   __ge__( self, other ):
    return super(FilePath,self).__ge__( self.__convert( other ) )
  
  #//-------------------------------------------------------//
  
  def   __hash__( self ):
    return super(FilePath, self).__hash__()
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    if attr in ['name_ext', 'dir']:
      self.dir, self.name_ext = map( FilePathBase, os.path.split( self ) )
      return getattr( self, attr )
    
    elif attr in ['name', 'ext']:
      self.name, self.ext = map( FilePathBase, os.path.splitext( self.name_ext ) )
      return getattr( self, attr )
    
    elif attr == 'dir_name':
      self.dir_name = FilePathBase( os.path.join( self.dir, self.name ) )
      return self.dir_name
    
    elif attr in ['seq', 'drive']:
      self.drive, self.seq = self.__makeSeq( self )
      return getattr( self, attr )
    
    raise AttributeError( "%s instance has no attribute '%s'" % (type(self), attr) )
  
  #//-------------------------------------------------------//
  
  def   change( self, dir = None, name = None, ext = None, prefix = None ):
    if dir is None: dir = self.dir
    if name is None: name = self.name
    if ext is None: ext = self.ext
    if prefix: name = prefix + name
    
    return FilePath( os.path.join( dir, name + ext ) )
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __makeSeq( path ):
    drive, path = os.path.splitdrive( path )
    if not drive:
      drive, path = _splitunc( path )
    
    path = tuple( map( FilePathBase, filter( None, path.split( os.path.sep ) ) ) )
    
    return drive, path
  
  #//-------------------------------------------------------//
  
  def   join( self, path, *paths ):
    paths = itertools.chain( toSequence( path ), paths )
    return FilePath( os.path.join( self, *paths ) )
  
  #//-------------------------------------------------------//
  
  def   abs( self ):
    return FilePath( os.path.abspath( self ) )
  
  #//-------------------------------------------------------//
  
  def   merge( self, other ):
    other = FilePath( other )
    
    seq = self.seq
    other_seq = other.seq
    
    path = self
    
    if self.drive == other.drive:
      i = 0
      for i, parts in enumerate( zip( seq, other.seq ) ):
        if parts[0] != parts[1]:
          break
      
      path = os.path.join( path, *other_seq[i:] )
      
    else:
      drive = other.drive.replace(':','')
      filter( None, drive.split( os.path.sep ) )
      path = os.path.join( path, *filter( None, drive.split( os.path.sep ) ) )
      path = os.path.join( path, *other_seq )
    
    return FilePath( path )

#//===========================================================================//

class   FilePaths( ValueListType( UniqueList, FilePath ) ):
  
  #//-------------------------------------------------------//
  
  def   change( self, dir = None, ext = None ):
    
    dirs = tuple( toSequence(dir) )
    if not dirs: dirs = (None,)
    
    exts = tuple( toSequence(ext) )
    if not exts: exts = (None,)
    
    count = len(dirs) * len(exts)
    
    paths = [FilePaths() for i in range(count) ]

    #noinspection PyTypeChecker
    for path in self:
      path_change = path.change
      i = 0
      for d in dirs:
        for ext in exts:
          paths[i].append( path_change( dir = d, ext = ext ) )
          i += 1
        
    
    if len(paths) == 1:
      return paths[0]
    
    return paths
  
  #//-------------------------------------------------------//
  
  def   add( self, suffix ):
    
    suffixes = tuple( toSequence(suffix) )
    if not suffixes: suffixes = ('',)
    
    paths = [FilePaths() for i in range(len(suffixes)) ]

    #noinspection PyTypeChecker
    for path in self:
      i = 0
      for suffix in suffixes:
        paths[i].append( path + suffix )
        i += 1
    
    if len(paths) == 1:
      return paths[0]
    
    return paths
  
  #//-------------------------------------------------------//
  
  def   groupUniqueNames( self, wish_groups = 1, max_group_size = -1 ):
    files = self
    wish_groups = max( 1, wish_groups )
    groups = []
    
    if max_group_size == -1:
      max_group_size = len(files)
    else:
      max_group_size = max(1,max_group_size)
    
    while files:
      group_names = set()
      group_files = FilePaths()
      rest_files = FilePaths()
      
      group_size = max(1, len(files) // max(1, wish_groups - len(groups) ) )
      group_size = min( max_group_size, group_size )

      #noinspection PyTypeChecker
      for filepath in files:
        if (len(group_files) >= group_size) or (filepath.name in group_names):
          rest_files.append( filepath )
        else:
          group_names.add( filepath.name )
          group_files.append( filepath )
      
      groups.append( group_files )
      
      files = rest_files
    
    return groups
  
  #//-------------------------------------------------------//
  
  def   groupByDir( self, wish_groups = 1, max_group_size = -1 ):
    
    wish_groups = max( 1, wish_groups )
    groups = []
    index_groups = []
    
    if max_group_size == -1:
      max_group_size = len(self)
    else:
      max_group_size = max(1,max_group_size)
    
    files = sorted( enumerate(self), key = lambda v:v[1] )
    
    last_dir = None
    group_files = FilePaths()
    group_indexes = []
    tail_size = len(files)
    
    group_size = max( 1, tail_size // wish_groups )
    group_size = min( max_group_size, group_size )
    
    for index, file_path in files:
      if (last_dir != file_path.dir) or (len(group_files) >= group_size):
        last_dir = file_path.dir
        
        if group_files:
          groups.append( group_files )
          index_groups.append( group_indexes )
          group_files = FilePaths()
          group_indexes = []
        
          group_size = max( 1, tail_size // max(1, wish_groups - len(groups) ) )
          group_size = min( max_group_size, group_size )
      
      tail_size -= 1
      group_files.append( file_path )
      group_indexes.append( index )
    
    if group_files:
      groups.append( group_files )
      index_groups.append( group_indexes )
    
    return groups, index_groups
