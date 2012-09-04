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


from aql_errors import UnpickleableValue
from aql_value import Value, NoContent
from aql_value_pickler import pickleable

@pickleable
class DependsKeyContent (set):
  def   __new__( cls, values = None ):
    
    self = super(DependsKeyContent,cls).__new__(cls)
    if values is not None:
      self.update( values )
    return self
  
  def   __getnewargs__(self):
    return ( tuple(self), )

#//===========================================================================//

class   DependsValueContent (tuple):
  
  def   __new__( cls, values = None ):
    
    if isinstance( values, DependsValueContent ):
      return values
    
    if isinstance( values, DependsKeyContent ):
      return values
    
    if isinstance( values, NoContent ):
      return values
    
    if values is None:
      return NoContent()
    
    try:
      values = list(values)
    except TypeError:
      values = [values]
    
    values.sort( key = lambda value: value.name )
    
    self = super(DependsValueContent,cls).__new__(cls, tuple(values) )
    
    return self
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other ):
    return (type(self) == type(other)) and super(DependsValueContent,self).__eq__( other )
  
  #//-------------------------------------------------------//
  
  def   __ne__( self, other ):
    return not self.__eq__( other )
  
  #//-------------------------------------------------------//
  
  def   __getnewargs__(self):
    raise UnpickleableValue( self )
  
  #//-------------------------------------------------------//
  
  def   __getstate__( self ):
    raise UnpickleableValue( self )
  
  #//-------------------------------------------------------//
  
  def   __setstate__( self, state ):
    raise UnpickleableValue( self )


#//===========================================================================//

@pickleable
class   DependsValue (Value):
  
  def   __new__( cls, name, content = None, use_cache = False ):
    
    if isinstance( name, DependsValue ):
      other = name
      name = other.name
      
      if content is None:
        content = other.content
    
    content = DependsValueContent( content )
    
    return super(DependsValue,cls).__new__(cls, name, content )
  
  #//-------------------------------------------------------//
  
  def   actual( self ):
    try:
      for value in self.content:
        if not value.actual():
          return False
        
    except TypeError:
      return False
    
    return True

#//===========================================================================//
