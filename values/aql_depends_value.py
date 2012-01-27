
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
    
    values.sort( key = lambda value: str(value.name) )
    
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
  
  def   __new__( cls, name, content = None ):
    
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
