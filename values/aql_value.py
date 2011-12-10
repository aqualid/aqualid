from aql_value_pickler import pickleable

#//===========================================================================//

@pickleable
class NoContent( object ):
  
  def   __new__( cls, *args ):
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
    return True
  
  #//-------------------------------------------------------//
