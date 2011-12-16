from aql_value_pickler import pickleable

#//===========================================================================//

@pickleable
class NoContent( object ):
  
  def   __new__( cls, *args ):
    return super(NoContent,cls).__new__(cls)
  
  def   __init__(self, *args ):     pass
  def   __eq__( self, other ):      return False
  def   __ne__( self, other ):      return True
  def   __bool__( self ):           return False
  def   __str__( self ):            return "<Not exist>"
  def   __getnewargs__(self):       return ()
  def   __getstate__(self):         return {}
  def   __setstate__(self,state):   pass

#//===========================================================================//

@pickleable
class   IgnoreCaseStringContent (str):
  
  def   __eq__( self, other ):
    return type(self) == type(other) and \
      (self.lower() == other.lower())
  
  def   __ne__( self, other ):
    return not self.__eq__( other )

#//===========================================================================//

@pickleable
class   Value (object):
  
  __slots__ = ( 'name', 'content' )
  
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
  
  def   __getstate__(self):         return {}
  def   __setstate__(self,state):   pass
  
  #//-------------------------------------------------------//
  
  def   __copy__( self ):
    raise Exception("Coping is not allowed")
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other):   return (self.name == other.name) and (self.content == other.content)
  def   __ne__( self, other):   return (self.name != other.name) or (self.content != other.content)
  
  #//-------------------------------------------------------//
  
  def   __str__(self):
    return str(self.name)
  
  #//-------------------------------------------------------//
  
  def   exists( self ):
    return type(self.content) is not NoContent
  
  #//-------------------------------------------------------//
  
  def   actual( self ):
    return not isinstance( self.content, NoContent )
  
  #//-------------------------------------------------------//
