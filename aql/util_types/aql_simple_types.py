#
# Copyright (c) 2011-2014 The developers of Aqualid project
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
  'AqlException','uStr', 'toUnicode', 'isUnicode', 'isString', 'toString', 'castStr', 'encodeStr', 'decodeBytes',
  'String', 'IgnoreCaseString', 'LowerCaseString', 'UpperCaseString',
  'Version', 'SIMPLE_TYPES_SET', 'SIMPLE_TYPES', 'isSimpleValue', 'isSimpleType'
)

import re
import sys
import locale
import operator

#//===========================================================================//

class  AqlException (Exception):
  pass

#//===========================================================================//

try:
  uStr = unicode
except NameError:
  uStr = str

#//===========================================================================//

_try_encodings = []
for enc in [
            'utf-8',
            sys.stdout.encoding,
            locale.getpreferredencoding(False),
            sys.getfilesystemencoding(),
            sys.getdefaultencoding(),
          ]:
  if enc:
    enc = enc.lower()
    if enc not in _try_encodings:
      _try_encodings.append( enc )

#//-------------------------------------------------------//

def   encodeStr( str, encoding = None ):
  if encoding:
    return str.encode( encoding )

  error = None
  for encoding in _try_encodings:
    try:
      return str.encode( encoding )
    except UnicodeEncodeError as ex:
      if error is None:
        error = ex

  raise error

#//===========================================================================//

def   decodeBytes( obj, encoding = None, _try_encodings = _try_encodings ):
  if encoding:
    return uStr( obj, encoding )

  error = None
  for encoding in _try_encodings:
    try:
      return uStr( obj, encoding )
    except UnicodeDecodeError as ex:
      if error is None:
        error = ex

  raise error

#//===========================================================================//

def toUnicode( obj, encoding = None ):
  if isinstance( obj, (bytearray, bytes) ):
    return decodeBytes( obj, encoding )

  return uStr( obj )

#//===========================================================================//

if uStr is not str:
  def   isUnicode( value, uStr = uStr, isinstance = isinstance ):
    return isinstance(value, uStr)

  def   isString( value, uStr = uStr, str = str, isinstance = isinstance ):
    return isinstance( value, (uStr, str))

  def   toString( value, uStr = uStr, str = str, isinstance = isinstance ):
    if isinstance( value, (uStr, str)):
      return value
    return str( value )

  #//-------------------------------------------------------//

  def castStr( obj, encoding = None, uStr = uStr ):
    if isinstance( obj, uStr ):
      return encodeStr( obj, encoding )

    return str( obj )

else:
  toString = toUnicode
  castStr = str

  def   isString( value, str = str, isinstance = isinstance ):
    return isinstance( value, str)

  isUnicode = isString

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

class   IgnoreCaseString (String):
  
  def   __hash__(self):
    return hash(self.lower())
  
  def   _cmp(self, other, op ):
    return op( self.lower(), str(other).lower())
  
  def   __eq__( self, other ):  return self._cmp( other, operator.eq )
  def   __ne__( self, other ):  return self._cmp( other, operator.ne )
  def   __lt__( self, other ):  return self._cmp( other, operator.lt )
  def   __le__( self, other ):  return self._cmp( other, operator.le )
  def   __gt__( self, other ):  return self._cmp( other, operator.gt )
  def   __ge__( self, other ):  return self._cmp( other, operator.ge )

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
    
    len_self = len(self_ver)
    len_other = len(other_ver)
    
    min_len = min( len_self, len_other )
    if min_len == 0:
      return cmp_op( len_self, len_other )
    
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

#//===========================================================================//

SIMPLE_TYPES_SET = frozenset( (uStr,str,int,float,complex,bool,bytes,bytearray) )
SIMPLE_TYPES = tuple(SIMPLE_TYPES_SET)

def isSimpleValue( value, _simple_types = SIMPLE_TYPES ):
  return isinstance( value, _simple_types )

def isSimpleType( value_type, _simple_types = SIMPLE_TYPES ):
  return issubclass( value_type, _simple_types )

