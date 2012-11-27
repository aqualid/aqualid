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
__all__ = (
  'NoContent', 'IgnoreCaseStringContent', 'Value',
)

import hashlib

from aql_value_pickler import pickleable

#//===========================================================================//

@pickleable
class NoContent( object ):
  
  def   __new__( cls, *args ):
    self = super(NoContent,cls).__new__(cls)
    self.signature = bytearray()
    return self
  
  def   __init__(self, *args ):
    pass
  def   __eq__( self, other ):
    return False
  def   __ne__( self, other ):
    return True
  def   __bool__( self ):
    return False
  def   __nonzero__( self ):
    return False
  def   __str__( self ):
    return "<Not exist>"
  def   __getnewargs__(self):
    return ()
  def   __getstate__(self):
    return {}
  def   __setstate__(self,state):
    pass

#//===========================================================================//

@pickleable
class   IgnoreCaseStringContent (str):
  
  def     __new__(cls, value = None ):
    
    if (cls is IgnoreCaseStringContent) and (type(value) is cls):
      return value
    
    if value is None:
      return NoContent()
    else:
      value = str(value)
    
    self = super(IgnoreCaseStringContent, cls).__new__(cls, value)
    self.__value = value.lower()
    
    return self
  
  def   __eq__( self, other ):
    return type(self) == type(other) and (self.__value == other.__value)
  
  def   __ne__( self, other ):
    return not self.__eq__( other )
  
  def   __getattr__( self, attr ):
    if attr == 'signature':
      self.signature = self.__signature()
      return self.signature
    
    return super(IgnoreCaseStringContent,self).__getattr__( attr )
  
  def   __signature( self ):
    buf = self.__value.encode('utf-8')
    hash = hashlib.md5()
    
    if len(buf) > hash.digest_size:
      return hash.update( buf ).digest()
    return buf

#//===========================================================================//

@pickleable
class   Value (object):
  
  __slots__ = ( 'name', 'content', 'signature' )
  
  #//-------------------------------------------------------//
  
  def   __new__( cls, name, content = NotImplemented ):
    
    if isinstance( name, Value ):
      other = name
      name = other.name
      
      if content is NotImplemented:
        content = other.content
      
      return type(other)( name, content )
    
    self = super(Value,cls).__new__(cls)
    
    if (content is NotImplemented) or (content is None):
      content = NoContent()
    
    self.name = name
    self.content = content
    
    return self
  
  #//-------------------------------------------------------//
  
  def     __getnewargs__(self):
    return ( self.name, self.content )
  
  #//-------------------------------------------------------//
  
  def   __getstate__(self):
    return {}
  
  def   __setstate__(self, state):
    pass
  
  #//-------------------------------------------------------//
  
  def   copy( self ):
    return type(self)( self.name, self.content )
  
  #//-------------------------------------------------------//
  
  def   __copy__( self ):
    return self.copy()
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other):
    return (self.name == other.name) and (self.content == other.content)
  
  def   __ne__( self, other):
    return (self.name != other.name) or (self.content != other.content)
  
  #//-------------------------------------------------------//
  
  def   __str__(self):
    return str(self.name)
  
  #//-------------------------------------------------------//
  
  def   exists( self ):
    return type(self.content) is not NoContent
  
  #//-------------------------------------------------------//
  
  def   actual( self, use_cache = True ):
    return not isinstance( self.content, NoContent )
  
  #//-------------------------------------------------------//
  
  def   remove( self ):
    pass
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    if attr == 'signature':
      self.signature = self.__signature()
      return self.signature
    
    return super(Value,self).__getattr__( attr )
  
  #//-------------------------------------------------------//
  
  def   __signature( self ):
    content = self.content
    
    try:
      return content.signature
    except AttributeError:
      pass
    
    buf = content.__str__().encode('utf-8')
    hash = hashlib.md5()
    
    if len(buf) > hash.digest_size:
      hash.update( buf )
      return hash.digest()
    
    return buf
  
  #//-------------------------------------------------------//
