#
# Copyright (c) 2011-2013 The developers of Aqualid project
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
  'ValueBase', 'SignatureValue', 'SimpleValue', 'NullValue',
)

from aql.util_types import toSequence, castStr, AqlException
from aql.utils import simpleObjectSignature, dumpSimpleObject
from .aql_value_pickler import pickleable

#//===========================================================================//

class   ErrorValueNameEmpty( AqlException ):
  def   __init__( self ):
    msg = "Vale name is empty"
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorSignatureValueInvalidDataType( AqlException ):
  def   __init__( self, data ):
    msg = "Signature value data type must be bytes or bytearray, actual type: '%s'" % (type(data),)
    super(type(self), self).__init__( msg )

class   ErrorTextValueInvalidDataType( AqlException ):
  def   __init__( self, text ):
    msg = "Text value data type must be string, actual type: '%s'" % (type(text),)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ValueBase (object):
  
  IS_SIZE_FIXED = False
  
  __slots__ = ( 'name', 'signature', 'tags' )
  
  #//-------------------------------------------------------//
  
  def   __new__( cls, name, signature, tags = None ):
    
    if not name:
      raise ErrorValueNameEmpty()
    
    self = super(ValueBase,cls).__new__(cls)
    self.name = name
    self.signature = signature
    self.tags = frozenset( toSequence(tags) ) if tags else None
    
    return self
  
  #//-------------------------------------------------------//
  
  def   valueId(self):
    return self.name, self.__class__
  
  #//-------------------------------------------------------//
  
  def   dumpId(self):
    cls = self.__class__
    return dumpSimpleObject(self.name), cls.__name__, cls.__module__
  
  #//-------------------------------------------------------//
  
  def   __hash__(self):
    return hash( self.valueId() )
  
  #//-------------------------------------------------------//
  
  def   get(self):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def     __getnewargs__(self):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   isActual( self ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   getActual( self ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//

  # noinspection PyMethodMayBeStatic
  def   __getstate__(self):
    return {}
  
  def   __setstate__(self, state):
    pass
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other):
    return (type(self) == type(other)) and \
           (self.name == other.name) and \
           (self.signature == other.signature)
  
  def   __ne__( self, other):
    return not self.__eq__( other )
  
  #//-------------------------------------------------------//

  def   __str__(self):
    return castStr(self.get())
  
  #//-------------------------------------------------------//
  
  def   isNull( self ):
    return self.signature is None
  
  #//-------------------------------------------------------//
  
  def   remove( self ):
    pass

#//===========================================================================//

# noinspection PyUnresolvedReferences
@pickleable
class   SimpleValue ( ValueBase ):
  
  __slots__ = ('data', )
  
  def   __new__(cls, data = None, name = None, signature = None, tags = None ):
    
    if data is None:
      signature = None
    else:
      if signature is None:
        signature = simpleObjectSignature( data )
    
    if not name:
      name = signature
    
    self = super(SimpleValue, cls).__new__( cls, name, signature, tags )
    self.data = data
    
    return self
  
  #//-------------------------------------------------------//

  def   get(self):
    return self.data
  
  #//-------------------------------------------------------//
  
  def     __getnewargs__(self):
    tags = self.tags
    if not tags:
      tags = None
    
    return self.data, self.name, self.signature, tags
  
  #//-------------------------------------------------------//
  
  def   isActual( self ):
    return bool(self.signature)
  
  #//-------------------------------------------------------//
  
  def   getActual( self ):
    return self

#//===========================================================================//

# noinspection PyUnresolvedReferences
@pickleable
class   NullValue ( ValueBase ):
  
  def   __new__(cls):
    
    name = 'N'
    signature = None
    
    return super(NullValue, cls).__new__( cls, name, signature )
  
  #//-------------------------------------------------------//

  def   get(self):
    return None
  
  #//-------------------------------------------------------//
  
  def     __getnewargs__(self):
    return tuple()
  
  #//-------------------------------------------------------//
  
  def   isActual( self ):
    return False
  
  #//-------------------------------------------------------//
  
  def   getActual( self ):
    return self


#//===========================================================================//

@pickleable
class   SignatureValue (ValueBase):
  
  IS_SIZE_FIXED = True
  
  def   __new__( cls, data = None, name = None ):
    
    if data is not None:
      if not isinstance( data, (bytes, bytearray) ):
        raise ErrorSignatureValueInvalidDataType( data )
    
    if not name:
      name = data
    
    return super(SignatureValue, cls).__new__( cls, name, data )
  
  #//-------------------------------------------------------//

  def   get(self):
    return self.signature

  #//-------------------------------------------------------//
  
  def     __getnewargs__(self):
    return self.signature, self.name
  
  #//-------------------------------------------------------//
  
  def   isActual( self ):
    return bool(self.signature)
  
  #//-------------------------------------------------------//
  
  def   getActual( self ):
    return self


#//===========================================================================//
