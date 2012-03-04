from aql_builder import Builder

#//===========================================================================//

class MetaBuilder (Builder):
  
  __slots__ = (
    'builder',
  )
   
  #//-------------------------------------------------------//
  
  def   build( self, node ):
  
  #//-------------------------------------------------------//
  
  def   values( self ):
    return []
  
  #//-------------------------------------------------------//
  
  def   clean( self, node, target_values, itarget_values ):
    pass
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
