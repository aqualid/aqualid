from aql_value_pickler import pickleable

#//===========================================================================//

@pickleable
class NoContent( object ):
  
  def   __new__( cls ):
    return super(NoContent,cls).__new__(cls)
  
  def   __init__(self, *args ):     pass
  def   __eq__( self, other ):      return False
  def   __ne__( self, other ):      return True
  def   __str__( self ):            return "<Not exist>"
  def   __getnewargs__(self):       return ()
  def   __getstate__(self):         return {}
  def   __setstate__(self,state):   pass

#//===========================================================================//

@pickleable
class   Value (object):
  
  __slots__ = ( 'name', 'content' )
  
  #//-------------------------------------------------------//
  
  def   __new__( cls, name, content = None ):
    
    self = super(Value,cls).__new__(cls)
    
    if content is None:
      content = NoContent()
    
    self.name = name
    self.content = content
    
    return self
  
  #//-------------------------------------------------------//
  
  def     __getnewargs__(self):
    content = self.content
    if content is None:
      content = None
    
    return ( self.name, content )
  
  #//-------------------------------------------------------//
  
  def   __getstate__(self):         return {}
  def   __setstate__(self,state):   pass
  
  #//-------------------------------------------------------//
  
  def   __copy__( self ):
    raise Exception("Coping is not allowed")
  
  #//-------------------------------------------------------//
  
  def   __hash__(self):             return hash(self.name)
  def   __lt__( self, other):       return self.name < other.name
  def   __le__( self, other):       return self.name <= other.name
  def   __eq__( self, other):       return self.name == other.name
  def   __ne__( self, other):       return self.name != other.name
  def   __gt__( self, other):       return self.name > other.name
  def   __ge__( self, other):       return self.name >= other.name
  
  #//-------------------------------------------------------//
  
  def   __str__(self):
    return str(self.name)
  
  #//-------------------------------------------------------//
  
  def   exists( self ):
    return type(self.content) is not NoContent
  
  #//-------------------------------------------------------//
