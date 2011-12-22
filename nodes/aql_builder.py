
class Builder (object):
  """
  Base class for all builders
  """
  
  __slots__ = (
    'name'
    'long_name',
  )
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    if attr == 'long_name':
      pass
   
    raise Exception( "Abstract method. It should be implemented in a child class." )
   
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    """
    Builds the node and returns lists of values: target, intermediate targets, impicit dependencies
    """
    raise Exception( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   values( self ):
    """
    Returns builder values
    """
    raise Exception( "Abstract method. It should be implemented in a child class." )
