
from aql_value import Value
from aql_logging import logError
from aql_utils import toSequence

class Builder (object):
  
  __slots__ = \
  (
    'name',
    'long_name',
    'options',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, options ):
    
    self.options = options
    
  #//-------------------------------------------------------//
  
  def   scan( self, node ):
    """
    Returns impicit dependencies values of the node
    """
    raise Exception( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    """
    Builds the node and returns list of target values and list of side effect values
    """
    raise Exception( "Abstract method. It should be implemented in a child class." )
