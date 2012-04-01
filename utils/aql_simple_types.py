import re
import os.path

#//===========================================================================//
#//===========================================================================//

class   IgnoreCaseString (str):

  def     __new__(cls, value = None ):
    
    if isinstance(value, IgnoreCaseString):
        return value
    
    if value is None:
        value = ''
    else:
        value = str(value)
    
    self = super(IgnoreCaseString, cls).__new__(cls, value)
    self.__value = value.lower()
    
    return self
  
  #//-------------------------------------------------------//
  
  def   __hash__(self):         return hash(self.__value)
  
  def   __eq__( self, other):   return self.__value == IgnoreCaseString( other ).__value
  def   __ne__( self, other):   return self.__value != IgnoreCaseString( other ).__value
  def   __lt__( self, other):   return self.__value <  IgnoreCaseString( other ).__value
  def   __le__( self, other):   return self.__value <= IgnoreCaseString( other ).__value
  def   __gt__( self, other):   return self.__value >  IgnoreCaseString( other ).__value
  def   __ge__( self, other):   return self.__value >= IgnoreCaseString( other ).__value

#//===========================================================================//
#//===========================================================================//

class   LowerCaseString (str):

  def     __new__(cls, value = None ):
    
    if isinstance(value, cls):
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
    
    if isinstance(value, cls):
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
    
    if isinstance(version, cls):
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
  
  def   __hash__(self):         return hash(self.__version)
  
  def   __eq__( self, other):   return self.__version == Version( other ).__version
  def   __lt__( self, other):   return self.__version <  Version( other ).__version
  def   __le__( self, other):   return self.__version <= Version( other ).__version
  def   __ne__( self, other):   return self.__version != Version( other ).__version
  def   __gt__( self, other):   return self.__version >  Version( other ).__version
  def   __ge__( self, other):   return self.__version >= Version( other ).__version

#//===========================================================================//

if os.path.normcase('ABC') == os.path.normcase('abc'):
  FilePathBase = IgnoreCaseString
else:
  FilePathBase = str

class   FilePath (FilePathBase):
  
  #//-------------------------------------------------------//
  
  def     __new__(cls, value = None ):
    if isinstance( value, cls ):
      return value
    
    if value is None:
        value = ''
    
    value = os.path.normpath( str(value) )
    
    return super(FilePath,cls).__new__( cls, value )
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other ):  return super(FilePath,self).__eq__( FilePath( other ) )
  def   __ne__( self, other ):  return super(FilePath,self).__ne__( FilePath( other ) )
  def   __lt__( self, other ):  return super(FilePath,self).__lt__( FilePath( other ) )
  def   __le__( self, other ):  return super(FilePath,self).__le__( FilePath( other ) )
  def   __gt__( self, other ):  return super(FilePath,self).__gt__( FilePath( other ) )
  def   __ge__( self, other ):  return super(FilePath,self).__ge__( FilePath( other ) )

