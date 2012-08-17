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


import re
import os.path

#//===========================================================================//
#//===========================================================================//

class   IgnoreCaseString (str):

  def     __new__(cls, value = None ):
    
    if (cls is IgnoreCaseString) and (type(value) is cls):
        return value
    
    if value is None:
        value = ''
    else:
        value = str(value)
    
    self = super(IgnoreCaseString, cls).__new__(cls, value)
    self.__value = value.lower()
    
    return self
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __convert(other ):
    return other if isinstance( other, IgnoreCaseString ) else IgnoreCaseString( other )
  
  #//-------------------------------------------------------//
  
  def   __hash__(self):
    return hash(self.__value)
  
  def   __eq__( self, other):
    return self.__value == self.__convert( other ).__value
  def   __ne__( self, other):
    return self.__value != self.__convert( other ).__value
  def   __lt__( self, other):
    return self.__value <  self.__convert( other ).__value
  def   __le__( self, other):
    return self.__value <= self.__convert( other ).__value
  def   __gt__( self, other):
    return self.__value >  self.__convert( other ).__value
  def   __ge__( self, other):
    return self.__value >= self.__convert( other ).__value

#//===========================================================================//
#//===========================================================================//

class   LowerCaseString (str):

  def     __new__(cls, value = None ):
    
    if (cls is LowerCaseString) and (type(value) is cls):
        return value
    
    if value is None:
        value = ''
    else:
        value = str(value)
    
    return super(LowerCaseString, cls).__new__(cls, value.lower())

#//===========================================================================//
#//===========================================================================//

class   UpperCaseString (str):

  def     __new__(cls, value = None ):
    
    if (cls is UpperCaseString) and (type(value) is cls):
        return value
    
    if value is None:
        value = ''
    else:
        value = str(value)
    
    return super(UpperCaseString, cls).__new__(cls, value.upper())

#//===========================================================================//
#//===========================================================================//

class   Version (str):

  __ver_re = re.compile(r'[0-9]+[a-zA-Z]*(\.[0-9]+[a-zA-Z]*)*')
  
  def     __new__(cls, version = None, _ver_re = __ver_re ):
    
    if (cls is Version) and (type(version) is cls):
        return version
    
    if version is None:
        ver_str = ''
    else:
        ver_str = str(version)
    
    match = _ver_re.search( ver_str )
    if match:
        ver_str = match.group()
        ver_list = re.findall(r'[0-9]+|[a-zA-Z]+', ver_str )
    else:
        ver_str = ''
        ver_list = []
    
    self = super(Version, cls).__new__(cls, ver_str )
    conv_ver_list = []
    
    for v in ver_list:
        if v.isdigit():
            v = int(v)
        conv_ver_list.append( v )
    
    self.__version = tuple(conv_ver_list)
    
    return self
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __convert( other ):
    return other if isinstance( other, Version ) else Version( other )
  
  #//-------------------------------------------------------//
  
  def   __hash__(self):
    return hash(self.__version)
  
  def   __eq__( self, other):
    return self.__version == self.__convert( other ).__version
  def   __lt__( self, other):
    return self.__version <  self.__convert( other ).__version
  def   __le__( self, other):
    return self.__version <= self.__convert( other ).__version
  def   __ne__( self, other):
    return self.__version != self.__convert( other ).__version
  def   __gt__( self, other):
    return self.__version >  self.__convert( other ).__version
  def   __ge__( self, other):
    return self.__version >= self.__convert( other ).__version

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
    
    elif attr == 'ext':
      self.ext = FilePathBase( os.path.splitext( self.name_ext )[1] )
      return self.ext
    
    elif attr == 'name':
      self.name = FilePathBase( os.path.splitext( self.name_ext )[0] )
      return self.name
    
    elif attr == 'dir':
      self.dir = FilePathBase( os.path.dirname( self ) )
      return self.dir
    
    elif attr in ['seq', 'drive']:
      self.drive, self.seq = self.__makeSeq( self )
      return getattr( self, attr )
    
    raise AttributeError( attr )
  
  #//-------------------------------------------------------//
  
  def   replaceExt( self, new_ext ):
    return FilePath( os.path.join( self.dir, self.name + new_ext ) )
  
  #//-------------------------------------------------------//
  
  def   replaceDir( self, files ):
    if isSequence( files ):
      return map( lambda f, d = self.dir : FilePath( os.path.join( d, FilePath(f).name_ext ) ), toSequence( files ) )
    
    return FilePath( os.path.join( self.dir, files.name_ext) ) )
  
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
