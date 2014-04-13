#
# Copyright (c) 2011-2014 The developers of Aqualid project - http://aqualid.googlecode.com
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
  'AqlException','uStr', 'toUnicode', 'isString', 'toString', 'castStr', 'String', 'IgnoreCaseString', 'LowerCaseString', 'UpperCaseString', 'Version',
)

import re
import sys
import operator

#//===========================================================================//

class  AqlException (Exception):
  pass

#//===========================================================================//

try:
  uStr = unicode
  
  def   isString( value, uStr = uStr, str = str, isinstance = isinstance ):
    return isinstance( value, (uStr, str))
  
  def   toString( value, uStr = uStr, str = str, isinstance = isinstance ):
    if isinstance( value, (uStr, str)):
      return value
    return str( value )
  
  def castStr( obj, encoding = None, uStr = uStr, 
              _try_encodings = frozenset([ 'utf-8',
                                           sys.getdefaultencoding().lower(),
                                           sys.stdout.encoding.lower(),
                                           sys.getfilesystemencoding().lower() ]) ):
    if isinstance( obj, uStr ):
      if encoding:
        return obj.encode( encoding )
      else:
        for encoding in _try_encodings:
          try:
            return obj.encode( encoding )
          except UnicodeEncodeError:
            pass
    
    return str( obj )

  def toUnicode( obj, encoding = None,
                _try_encodings = frozenset([ 'utf-8',
                                             sys.getdefaultencoding().lower(),
                                             sys.stdout.encoding.lower(),
                                             sys.getfilesystemencoding().lower() ]) ):
    if isinstance( obj, (bytearray, bytes) ):
      if encoding:
        return uStr( obj, encoding )
      else:
        for encoding in _try_encodings:
          try:
            return uStr( obj, encoding )
          except UnicodeDecodeError:
            pass
    
    return uStr( obj )



except NameError:
  uStr = str
  toString = str
  castStr = str
  toUnicode = str
  
  def   isString( value, str = str, isinstance = isinstance ):
    return isinstance( value, str)

#//===========================================================================//

class   String (str):

  def     __new__( cls, value = None ):
    
    if type(value) is cls:
        return value
    
    if value is None:
        value = ''
    
    return super(String, cls).__new__(cls, value)

#//===========================================================================//
#//===========================================================================//

class   IgnoreCaseString (str):

  def     __new__(cls, value = None ):
    
    if type(value) is cls:
      return value
    
    if value is None:
      value = ''
        
    self = super(IgnoreCaseString, cls).__new__(cls, value)
    self.__value = self.lower()
    
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
    
    if type(value) is cls:
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
    
    if type(value) is cls:
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
    
    if type(version) is cls:
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
  
  def   _cmp( self, other, cmp_op ):
    self_ver = self.__version
    other_ver = self.__convert( other ).__version
    
    min_len = min( len(self_ver), len(other_ver) )
    self_ver = self_ver[:min_len]
    other_ver = other_ver[:min_len]
    
    return cmp_op( self_ver, other_ver )
  
  #//-------------------------------------------------------//
  
  def   __hash__(self):         return hash(self.__version)
  def   __eq__( self, other ):  return self._cmp( other, operator.eq )
  def   __ne__( self, other ):  return self._cmp( other, operator.ne )
  def   __lt__( self, other ):  return self._cmp( other, operator.lt )
  def   __le__( self, other ):  return self._cmp( other, operator.le )
  def   __gt__( self, other ):  return self._cmp( other, operator.gt )
  def   __ge__( self, other ):  return self._cmp( other, operator.ge )
