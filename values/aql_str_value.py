
from aql_value import Value
from aql_value_pickler import pickleable

#//===========================================================================//

StringContent = str

@pickleable
class   StringContentIgnoreCase (str):
  
  def   __eq__( self, other ):
    return type(self) == type(other) and \
      (self.lower() == other.lower())
  
  def   __ne__( self, other ):
    return not self.__eq__( other )

#//===========================================================================//

@pickleable
class StringValue (Value):
  def   __new__( cls, name, content = NotImplemented ):
    
    if isinstance( name, StringValue ):
      other = name
      name = other.name
      
      if content is NotImplemented:
        content = other.content
    
    return super(StringValue,cls).__new__(cls, name, content)

#//===========================================================================//
