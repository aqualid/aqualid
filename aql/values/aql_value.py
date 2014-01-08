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
  'ContentBase', 'NoContent', 'StringContent', 'IStringContent', 'BytesContent', 'SignatureContent',
  'Value', 'StringValue', 'IStringValue', 'SignatureValue', 'makeContent',
)

from aql.utils import strSignature, dataSignature, dumpData
from .aql_value_pickler import pickleable

#//===========================================================================//

class   ErrorInvalidValueBytesContentType( Exception ):
  def   __init__( self, content ):
    msg = "Value content type must be bytes or bytearray, content type: '%s'" % str(type(content))
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
    return type(self) == type(other) and (self.signature == other.signature)
  
  def   __bool__( self ):
    return True
  
  def   __str__( self ):
    return str(self.data)
  
  def   __getnewargs__(self):
    #noinspection PyRedundantParentheses
    return (self.data, )
  
  def   __ne__( self, other ):
    return not self.__eq__( other )
  
  def   __nonzero__( self ):
    return self.__bool__()
  
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
    return tuple()

NoContent = _NoContent()

#//===========================================================================//

@pickleable
class   SignatureContent( ContentBase ):
  
  def   __new__( cls, data = None ):
    
    if isinstance(data, ContentBase ):
      return data
    
    if data is None:
      return NoContent
    
    if not isinstance( data, (bytes, bytearray) ):
      raise ErrorInvalidValueBytesContentType( data )
    
    self = super(SignatureContent,cls).__new__(cls)
    
    self.data = data
    self.signature = data
    
    return self
  
#//===========================================================================//

#noinspection PyAttributeOutsideInit
@pickleable
class   BytesContent ( ContentBase ):
  
  def   __new__( cls, data = None ):
    
    if isinstance(data, ContentBase ):
      return data
    
    if data is None:
      return NoContent
    
    if not isinstance( data, (bytes, bytearray) ):
      raise ErrorInvalidValueBytesContentType( data )
    
    self = super(BytesContent,cls).__new__(cls)
    
    self.data = data
    
    return self
  
  def   __getattr__( self, attr ):
    if attr == 'signature':
      self.signature = dataSignature( self.data )
      return self.signature
    
    return super(BytesContent,self).__getattr__( attr )

#//===========================================================================//

#noinspection PyAttributeOutsideInit
@pickleable
class   StringContent ( ContentBase ):
  
  def   __new__(cls, data = None ):
    
    if isinstance(data, ContentBase ):
      return data
    
    if data is None:
      return NoContent
    
    self = super(StringContent,cls).__new__(cls)
    
    self.data = str(data)
    
    return self
  
  def   __getattr__( self, attr ):
    if attr == 'signature':
      self.signature = strSignature( self.data )
      return self.signature
    
    return super(StringContent,self).__getattr__( attr )

#//============================signature===============================================//

#noinspection PyAttributeOutsideInit
@pickleable
class   IStringContent ( StringContent ):
  
  __slots__ = ('low_case_str',)
  
  def   __getattr__( self, attr ):
    if attr == 'low_case_str':
      self.low_case_str = self.data.lower()
      return self.low_case_str
    
    if attr == 'signature':
      self.signature = strSignature( self.low_case_str )
      return self.signature
    
    return super(IStringContent,self).__getattr__( attr )

#//===========================================================================//

#noinspection PyAttributeOutsideInit
@pickleable
class   OtherContent ( ContentBase ):
  
  def   __new__( cls, data = None ):
    
    if isinstance(data, ContentBase ):
      return data
    
    if data is None:
      return NoContent
    
    self = super(OtherContent,cls).__new__(cls)
    
    self.data = data
    
    return self
  
  def   __getattr__( self, attr ):
    if attr == 'signature':
      bytes_data = dumpData( self.data )
      self.signature = dataSignature( bytes_data )
      return self.signature
    
    return super(OtherContent,self).__getattr__( attr )

#//===========================================================================//

def   makeContent( content ):
  if (content is NotImplemented) or (content is None):
    content = NoContent
  
  if not isinstance( content, ContentBase ):
    if isinstance( content, (bytes, bytearray)):
      content = BytesContent( content )
    elif isinstance( content, str):
      content = StringContent( content )
    else:
      content = OtherContent( content )
  
  return content

#//===========================================================================//

#noinspection PyAttributeOutsideInit,PyMethodMayBeStatic
@pickleable
class   Value (object):
  
  __slots__ = ( 'name', 'content', 'data', 'signature' )
  
  #//-------------------------------------------------------//
  
  def   __new__( cls, content = NotImplemented, name = None ):
    
    if isinstance( content, Value ):
      other = content
      if name is None:
        name = other.name
      
      return type(content)( content = other.content, name = name )
    
    self = super(Value,cls).__new__(cls)
    
    content = makeContent( content )
    
    if name is None:
      name = content.signature
    
    self.name = name
    self.content = content
    
    return self
  
  #//-------------------------------------------------------//
  
  def     __getnewargs__(self):
    return self.content, self.name
  
  #//-------------------------------------------------------//

  def   __getstate__(self):
    return {}
  
  def   __setstate__(self, state):
    pass
  
  #//-------------------------------------------------------//
  
  def   copy( self ):
    return type(self)( content = self.content, name = self.name )
  
  #//-------------------------------------------------------//
  
  def   __copy__( self ):
    return self.copy()
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other):
    return (type(self) == type(other)) and (self.name == other.name) and (self.content == other.content)
  
  def   __ne__( self, other):
    return not self.__eq__( other )
  
  #//-------------------------------------------------------//

  def   get(self):
    return self.content.data

  #//-------------------------------------------------------//

  def   __str__(self):
    return str(self.name)
  
  #//-------------------------------------------------------//
  
  def   __bool__( self ):
    return bool(self.content)
  
  #//-------------------------------------------------------//
  
  def   __nonzero__( self ):
    return bool(self.content)
  
  #//-------------------------------------------------------//
  
  def   actual( self, use_cache = True ):
    return bool(self.content)
  
  #//-------------------------------------------------------//
  
  def   remove( self ):
    pass
  
  #//-------------------------------------------------------//
  
  # def   __getattr__( self, attr ):
  #   if attr == 'data':
  #     self.data = self.content.data
  #     return self.data
  #   
  #   if attr == 'signature':
  #     self.signature = self.content.signature
  #     return self.signature
  #   
  #   raise AttributeError( attr )
  
#//===========================================================================//

@pickleable
class   StringValue (Value):
  
  def   __new__( cls, content = NotImplemented, name = None ):
    
    content = StringContent( content )
    
    return super(StringValue,cls).__new__( cls, content = content, name = name )

#//===========================================================================//

@pickleable
class   IStringValue (Value):
  
  def   __new__( cls, content = NotImplemented, name = None ):
    
    content = IStringContent( content )
    
    return super(IStringValue,cls).__new__( cls, content = content, name = name )

#//===========================================================================//

@pickleable
class   SignatureValue (Value):
  
  def   __new__( cls, content = NotImplemented, name = None ):
    
    content = SignatureContent( content )
    return super(SignatureValue,cls).__new__( cls, content = content, name = name )
