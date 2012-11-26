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
import itertools

from aql_utils import toSequence
from aql_simple_types import IgnoreCaseString
from aql_list_types import UniqueList, ValueListType
from aql_file_value import FileValue

#//===========================================================================//

if os.path.normcase('ABC') == os.path.normcase('abc'):
  FilePathBase = IgnoreCaseString
else:
  FilePathBase = str

class   FilePath (FilePathBase):
  
  #//-------------------------------------------------------//
  
  def     __new__(cls, path = None ):
    if (cls is FilePath) and (type(path) is cls):
      return path
    
    if path is None:
        path = ''
    
    if isinstance( path, FileValue ):
      path = path.name
    
    path = str(path)
    
    if path:
      path = os.path.normpath( path )
    
    return super(FilePath,cls).__new__( cls, path )
  
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
    if attr == 'name_ext':
      self.name_ext = FilePathBase( os.path.basename(self) )
      return self.name_ext
    
    elif attr in ['name', 'ext']:
      self.name, self.ext = map( FilePathBase, os.path.splitext( self.name_ext ) )
      return getattr( self, attr )
    
    elif attr == 'dir':
      self.dir = FilePathBase( os.path.dirname( self ) )
      return self.dir
    
    elif attr == 'dir_name':
      self.dir_name = FilePathBase( os.path.join( self.dir, self.name ) )
      return self.dir_name
    
    elif attr in ['seq', 'drive']:
      self.drive, self.seq = self.__makeSeq( self )
      return getattr( self, attr )
    
    raise AttributeError( attr )
  
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
      drive, path = os.path.splitunc( path )
    
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
    
    for path in self:
      path_change = path.change
      i = 0
      for dir in dirs:
        for ext in exts:
          paths[i].append( path_change( dir = dir, ext = ext ) )
          i += 1
        
    
    if len(paths) == 1:
      return paths[0]
    
    return paths
  
  #//-------------------------------------------------------//
  
  def   add( self, suffix ):
    
    suffixes = tuple( toSequence(suffix) )
    if not suffixes: suffixes = ('',)
    
    paths = [FilePaths() for i in range(len(suffixes)) ]
    
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
      
      for file in files:
        if (len(group_files) >= group_size) or (file.name in group_names):
          rest_files.append( file )
        else:
          group_names.add( file.name )
          group_files.append( file )
      
      groups.append( group_files )
      
      files = rest_files
    
    return groups
