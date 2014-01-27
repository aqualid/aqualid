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
  'DependsValue', 'DependsValueContent', 'DependsKeyContent', 'ErrorValueUnpickleable',
)

from .aql_value import Value, ContentBase, NoContent
from .aql_value_pickler import pickleable

#//===========================================================================//

class   ErrorValueUnpickleable ( Exception ):
  def   __init__( self, value ):
    msg = "Value '%s' can't be serialized." % type(value).__name__ 
    super(type(self), self).__init__( msg )

class   ErrorNoDependsValues( Exception ):
  def   __init__( self ):
    msg = "No depends values."
    super(type(self), self).__init__( msg )

#//===========================================================================//

@pickleable
class DependsKeyContent (ContentBase):
  def   __new__( cls, values = None ):
    
    self = super(DependsKeyContent,cls).__new__(cls)
    
    self.data = frozenset( values ) if values is not None else frozenset()
    
    return self
  
  #//-------------------------------------------------------//
  
  def   __bool__( self ):
    return True
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other ):
    return (type(self) == type(other)) and  (self.data == other.data)
  
  #//-------------------------------------------------------//
  
  def   __getnewargs__(self):
    return ( tuple(self.data), )

#//===========================================================================//

class   DependsValueContent (ContentBase):
  
  def   __new__( cls, values = None ):
    
    if isinstance( values, DependsValueContent ):
      return values
    
    if isinstance( values, DependsKeyContent ):
      return values
    
    if isinstance(values, ContentBase) and not values:
      return NoContent
    
    if values is None:
      return NoContent
    
    try:
      values = list(values)
    except TypeError:
      values = [values]
    
    values.sort( key = lambda value: value.name )
    
    self = super(DependsValueContent,cls).__new__(cls)
    self.data = tuple( values )
    
    return self
  
  #//-------------------------------------------------------//
  
  def   get( self ):
    return self.data
  
  #//-------------------------------------------------------//
  
  def   __bool__( self ):
    return True
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other ):
    return (type(self) == type(other)) and  (self.data == other.data)
  
  #//-------------------------------------------------------//
  
  def   __getnewargs__(self):
    raise ErrorValueUnpickleable( self )
  
  #//-------------------------------------------------------//
  
  def   __getstate__( self ):
    raise ErrorValueUnpickleable( self )
  
  #//-------------------------------------------------------//
  
  def   __setstate__( self, state ):
    raise ErrorValueUnpickleable( self )


#//===========================================================================//

@pickleable
class   DependsValue (Value):
  
  def   __new__( cls, content = None, name = None ):
    
    if isinstance( content, DependsValue ):
      
      if (name is None) or (name == content.name):
        return content
      
      name = content.name
      content = content.content
    
    else:
      content = DependsValueContent( content )
    
    return super(DependsValue,cls).__new__(cls, name = name, content = content )
  
  #//-------------------------------------------------------//

  def get(self):
    values = self.content.get()
    if values is None:
      raise ErrorNoDependsValues()

    return [ v.get() for v in values ]

  #//-------------------------------------------------------//

  def   actual( self ):
    values = self.content.get()
    if values is None:
      # if __debug__:
      #   print("DependsValue.actual(): non-actual value: %s" % (value,))
      return False
    
    for value in values:
      if not value.actual():
        # if __debug__:
        #   print("DependsValue.actual(): non-actual value: %s" % (value,))
        return False
    
    return True

#//===========================================================================//
