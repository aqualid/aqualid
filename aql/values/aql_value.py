#
# Copyright (c) 2011-2013 The developers of Aqualid project - http://aqualid.googlecode.com
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
  'NoContent', 'StringContent', 'IStringContent', 'BytesContent', 'Value', 'StringValue', 'IStringValue',
)

import hashlib

from aql.utils import strSignature, dataSignature
from .aql_value_pickler import pickleable

#//===========================================================================//

class   ErrorInvalidValueContentType( Exception ):
  def   __init__( self, content ):
    msg = "Value content type must be based on ContentBase, content type: '%s'" % str(type(content))
    self.content = content
    super(type(self), self).__init__( msg )

class   ErrorInvalidValueBytesContentType( Exception ):
  def   __init__( self, content ):
    msg = "Value content type must be bytes or  bytearray, content type: '%s'" % str(type(content))
    self.content = content
    super(type(self), self).__init__( msg )

#//===========================================================================//

class ContentBase( object ):
  
  __slots__ = ('data', 'signature')
  
  def   __new__( cls, *args, **kw ):
    return super(ContentBase,cls).__new__(cls)
  
  def   __init__( self, *args, **kw ):
    pass
  
  def   __eq__( self, other ):
    print(type(self))
    print(type(other))
    raise NotImplementedError("Abstract method should be implemented in child classes")
  
  def   __ne__( self, other ):
    return not self.__eq__( other )
  
  def   __bool__( self ):
    raise NotImplementedError("Abstract method should be implemented in child classes")
  
  def   __nonzero__( self ):
    return self.__bool__()
  
  def   __str__( self ):
    raise NotImplementedError("Abstract method should be implemented in child classes")
  
  def   __getnewargs__(self):
    raise NotImplementedError("Abstract method should be implemented in child classes")
  
  def   __getstate__(self):
    return {}
  def   __setstate__(self,state):
    pass
  
  def   __getattr__( self, attr ):
    if attr == 'signature':
      raise NotImplementedError("Attribute '%s' must be set by child classes" % str(attr))
    
    raise AttributeError( attr )

#//===========================================================================//

@pickleable
class _NoContent( ContentBase ):
  
  def   __new__( cls, *args ):
    self = super(_NoContent,cls).__new__(cls)
    self.data = None
    self.signature = bytearray()
    return self
  
  def   __eq__( self, other ):
    return False
  def   __bool__( self ):
    return False
  def   __str__( self ):
    return "<Not exists>"
  def   __getnewargs__(self):
    return ()

NoContent = _NoContent()

#//===========================================================================//

@pickleable
class   BytesContent ( ContentBase ):
  
  def   __new__(cls, data = None ):
    
    if type(data) is cls:
      return data
    
    if data is None:
      return NoContent
    
    if not isinstance( data, (bytes, bytearray) ):
      raise ErrorInvalidValueBytesContentType( data )
    
    self = super(BytesContent,cls).__new__(cls)
    
    self.data = data
    
    return self
  
  def   __eq__( self, other ):
    return type(self) == type(other) and (self.signature == other.signature)
  
  def   __bool__( self ):
    return True
  
  def   __str__( self ):
    return str(self.data)
  
  def   __getnewargs__(self):
    return (self.data, )
  
  def   __getattr__( self, attr ):
    if attr == 'signature':
      self.signature = dataSignature( self.data )
      return self.signature
    
    return super(BytesContent,self).__getattr__( attr )

#//===========================================================================//

@pickleable
class   StringContent ( ContentBase ):
  
  def   __new__(cls, data = None ):
    
    if type(data) is cls:
      return data
    
    if data is None:
      return NoContent
    
    self = super(StringContent,cls).__new__(cls)
    
    self.data = str(data)
    
    return self
  
  def   __eq__( self, other ):
    return type(self) == type(other) and (self.signature == other.signature)
  
  def   __bool__( self ):
    return True
  
  def   __str__( self ):
    return self.data
  
  def   __getnewargs__(self):
    return (self.data, )
  
  def   __getattr__( self, attr ):
    if attr == 'signature':
      self.signature = strSignature( self.data )
      return self.signature
    
    return super(StringContent,self).__getattr__( attr )

#//===========================================================================//

@pickleable
class   IStringContent ( StringContent ):
  
  __slots__ = ('low_case_str')
  
  def   __eq__( self, other ):
    return type(self) == type(other) and (self.signature == other.signature)
  
  def   __getattr__( self, attr ):
    if attr == 'low_case_str':
      self.low_case_str = data.lower()
      return self.low_case_str
    
    if attr == 'signature':
      self.signature = strSignature( self.low_case_str )
      return self.signature
    
    return super(IStringContent,self).__getattr__( attr )

#//===========================================================================//

@pickleable
class   Value (object):
  
  __slots__ = ( 'name', 'content', 'data', 'signature' )
  
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
      content = NoContent
    
    if not isinstance( content, ContentBase ):
      if isinstance( content, str):
        content = StringContent( content )
      elif isinstance( content, (bytes, bytearray)):
        content = BytesContent( content )
      else:
        raise ErrorInvalidValueContentType( content )
    
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
  
  def   __bool__( self ):
    return bool(self.content)
  
  #//-------------------------------------------------------//
  
  def   actual( self, use_cache = True ):
    return bool(self.content)
  
  #//-------------------------------------------------------//
  
  def   remove( self ):
    pass
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    if attr == 'data':
      self.data = self.content.data
      return self.data
    
    if attr == 'signature':
      self.signature = self.content.signature
      return self.signature
    
    raise AttributeError( attr )
  
#//===========================================================================//

@pickleable
class   StringValue (Value):
  
  def   __new__( cls, name, content = NotImplemented ):
    
    if (content is not NotImplemented) and not isinstance( content, StringContent ):
      content = StringContent( content )
    
    return super(StringValue,cls).__new__( cls, name, content )

#//===========================================================================//

@pickleable
class   IStringValue (Value):
  
  def   __new__( cls, name, content = NotImplemented ):
    
    if (content is not NotImplemented) and not isinstance( content,IStringContent ):
      content = IStringContent( content )
    
    return super(IStringValue,cls).__new__( cls, name, content )
