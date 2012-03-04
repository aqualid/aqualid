
class RebuildNode( Exception ):
  pass

#//===========================================================================//

class Builder (object):
  """
  Base class for all builders
  """
  
  __slots__ = (
    'env',
    'options',
    'name',
    'long_name',
  )
   
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    """
    Builds the node and returns values: targets, intermediate targets, impicit dependencies
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   values( self ):
    """
    Returns builder values
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   clean( self, node, target_values, itarget_values ):
    """
    Cleans produced values
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
