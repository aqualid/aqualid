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
  'EntityBase', 'SignatureEntity', 'SimpleEntity', 'NullEntity',
)

from aql.util_types import toSequence, castStr, AqlException
from aql.utils import simpleObjectSignature
from .aql_entity_pickler import pickleable

#//===========================================================================//

class   ErrorEntityNameEmpty( AqlException ):
  def   __init__( self ):
    msg = "Entity name is empty"
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorSignatureEntityInvalidDataType( AqlException ):
  def   __init__( self, data ):
    msg = "Signature data type must be bytes or bytearray, actual type: '%s'" % (type(data),)
    super(type(self), self).__init__( msg )

class   ErrorTextEntityInvalidDataType( AqlException ):
  def   __init__( self, text ):
    msg = "Text data type must be string, actual type: '%s'" % (type(text),)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   EntityBase (object):
  
  __slots__ = ( 'id', 'name', 'signature', 'tags' )
  
  #//-------------------------------------------------------//
  
  def   __new__( cls, name, signature, tags = None ):
    
    self = super(EntityBase,cls).__new__(cls)
    
    if name is not NotImplemented:
      if not name:
        raise ErrorEntityNameEmpty()
      self.name = name
    
    if signature is not NotImplemented:
      self.signature = signature
    
    self.tags = frozenset( toSequence(tags) ) if tags else None
    
    return self
  
  #//-------------------------------------------------------//
  
  def   __hash__(self):
    return hash( self.id )
  
  #//-------------------------------------------------------//
  
  def   get(self):
    """
    Returns value of the entity
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  
  def   getId(self):
    cls = self.__class__
    return simpleObjectSignature( (self.name, cls.__name__, cls.__module__) )
  #//-------------------------------------------------------//
  
  def   getName(self):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  #//-------------------------------------------------------//
  
  def   getSignature(self):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   __getattr__(self, attr):
    if attr == 'signature':
      self.signature = signature = self.getSignature()
      return signature
    elif attr == 'name':
      self.name = name = self.getName()
      return name
    elif attr == 'id':
      self.name = name = self.getName()
      return name
    
    raise AttributeError("Unknown attribute: '%s'" % (attr,))
  
  #//-------------------------------------------------------//
  
  def     __getnewargs__(self):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   isActual( self ):
    """
    Checks whether the entity is actual or not
    """
    return bool(self.signature)
  
  #//-------------------------------------------------------//
  
  def   getActual( self ):
    """
    Returns an actual entity. If the current entity is actual then it will be simply returned 
    """
    return self
  
  #//-------------------------------------------------------//

  def   __getstate__(self):
    return {}
  
  def   __setstate__(self, state):
    pass
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other):
    return (self.id == other.id) and \
           (self.signature == other.signature)
  
  def   __ne__( self, other ):
    return not self.__eq__( other )
  
  #//-------------------------------------------------------//

  def   __str__(self):
    return castStr(self.get())
  
  #//-------------------------------------------------------//
  
  def   remove( self ):
    pass


#//===========================================================================//

@pickleable
class   SimpleEntity ( EntityBase ):
  
  __slots__ = ('data', )
  
  def   __new__(cls, data = None, name = None, signature = None, tags = None ):
    
    if data is None:
      signature = None
    else:
      if signature is None:
        signature = simpleObjectSignature( data )
    
    if not name:
      name = signature
    
    self = super(SimpleEntity, cls).__new__( cls, name, signature, tags )
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
    
    name = self.name
    if name == self.signature:
      name = None
    
    return self.data, name, self.signature, tags

#//===========================================================================//

@pickleable
class   NullEntity ( EntityBase ):
  
  def   __new__(cls):
    
    name = 'N'
    signature = None
    
    return super(NullEntity, cls).__new__( cls, name, signature )
  
  #//-------------------------------------------------------//

  def   get(self):
    return None
  
  #//-------------------------------------------------------//
  
  def     __getnewargs__(self):
    return tuple()
  
  #//-------------------------------------------------------//
  
  def   isActual( self ):
    return False
  

#//===========================================================================//

@pickleable
class   SignatureEntity (EntityBase):
  
  def   __new__( cls, data = None, name = None, tags = None ):
    
    if data is not None:
      if not isinstance( data, (bytes, bytearray) ):
        raise ErrorSignatureEntityInvalidDataType( data )
    
    if not name:
      name = data
    
    return super(SignatureEntity, cls).__new__( cls, name, data, tags )
  
  #//-------------------------------------------------------//

  def   get(self):
    return self.signature

  #//-------------------------------------------------------//
  
  def     __getnewargs__(self):
    tags = self.tags
    if not tags:
      tags = None
    
    name = self.name
    if name == self.signature:
      name = None
    
    return self.signature, name, tags
  

#//===========================================================================//
