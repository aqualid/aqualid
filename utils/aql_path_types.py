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

from aql_simple_types import IgnoreCaseString
from aql_list_types import ValueListType

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
    
    path = os.path.normpath( str(path) )
    
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
      self.dir_name = os.path.join( self.dir, self.name )
      return self.dir_name
    
    elif attr in ['seq', 'drive']:
      self.drive, self.seq = self.__makeSeq( self )
      return getattr( self, attr )
    
    raise AttributeError( attr )
  
  #//-------------------------------------------------------//
  
  def   replaceExt( self, new_ext ):
    return FilePath( self.dir_name + new_ext )
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __makeSeq( path ):
    drive, path = os.path.splitdrive( path )
    if not drive:
      drive, path = os.path.splitunc( path )
    
    path = tuple( map( FilePathBase, filter( None, path.split( os.path.sep ) ) ) )
    
    return drive, path
  
  #//-------------------------------------------------------//
  
  def   mergePaths( self, other ):
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
  
  def   replaceDir( self, new_dir ):
    paths = FilePaths()
    
    for path in self:
      paths.append( os.path.join( new_dir, path.name_ext ) )
    
    return paths
  
  #//-------------------------------------------------------//
  
  def   replaceExt( self, new_ext ):
    paths = FilePaths()
    
    for path in self:
      paths.append( path.dir_name + new_ext )
    
    return paths
