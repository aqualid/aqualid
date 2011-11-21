
from aql_value import Value, NoContent
from aql_value_pickler import pickleable

#//===========================================================================//

class   DependsValueContent (tuple):
  
  def   __new__( cls, values = None ):
    
    if isinstance( values, DependsValueContent ):
      return values
    
    if isinstance( values, NoContent ):
      return values
    
    if values is None:
      return NoContent()
    
    try:
      values_list = []
      for value in values:
        if not isinstance( value, Value ):
          return values
        values_list.append( value )
      
      if not values_list:
        return values
      
      values = values_list
      
    except TypeError:
      values = [values]
    
    values.sort()
    
    self = super(DependsValueContent,cls).__new__(cls, tuple(values) )
    
    return self
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other ):
    if (type(self) != type(other)) or \
      super(DependsValueContent,self).__ne__(self, other ):
      return False
    
    for value1, value2 in zip( self, other ):
      if value1.content != value2.content:
        return False
    
    return True
  
  #//-------------------------------------------------------//
  
  def   __ne__( self, other ):
    return not self.__eq__( other )
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    return str(self.values)
  
  #//-------------------------------------------------------//
  
  def   __getnewargs__(self):
    raise Exception( "Object '%s' can't be serialized." % type(self).__name__ )
  
  #//-------------------------------------------------------//
  
  def   __getstate__( self ):
    raise Exception( "Object '%s' can't be serialized." % type(self).__name__ )
  
  #//-------------------------------------------------------//
  
  def   __setstate__( self, state ):
    raise Exception( "Object '%s' can't be de-serialized." % type(self).__name__ )


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

#//===========================================================================//
