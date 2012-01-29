
from aql_logging import logInfo,logWarning,logError

#//===========================================================================//

class EventHandler( object ):
  
  #//-------------------------------------------------------//
  
  def   outdatedNode( self, node ):
    logInfo("Outdated node: %s" % node )
  
  #//-------------------------------------------------------//
  
  def   dataFileIsNotSync( self, filename ):
    logWarning("Internal error: DataFile is unsynchronized")
  
  #//-------------------------------------------------------//
  
  def   depValueIsCyclic( self, value ):
    logWarning("Internal error: Cyclic dependency value: %s" % value )
  
  #//-------------------------------------------------------//
  
  def   unknownValue( self, value ):
    logWarning("Internal error: Unknown value: %s " % value )
  
  #//-------------------------------------------------------//
