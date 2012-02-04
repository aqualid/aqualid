
from aql_logging import logInfo,logWarning

#//===========================================================================//

info_events     = set()
debug_events    = set()
status_events   = set()
warning_events  = set()

def   _info( event_method ):    info_events.add( event_method.__name__ );     return event_method
def   _debug( event_method ):   debug_events.add( event_method.__name__ );    return event_method
def   _status( event_method ):  status_events.add( event_method.__name__ );   return event_method
def   _warning( event_method ): warning_events.add( event_method.__name__ );  return event_method

#//===========================================================================//

class EventHandler( object ):
  
  #//-------------------------------------------------------//
  @_warning
  def   eventDataFileIsNotSync( self, filename ):
    """
    Inconsistency state of Data file. Either internal error or external corruption.
    """
    logWarning("Internal error: DataFile is unsynchronized")
  
  #//-------------------------------------------------------//
  @_warning
  def   eventDepValueIsCyclic( self, value ):
    logWarning("Internal error: Cyclic dependency value: %s" % value )
  
  #//-------------------------------------------------------//
  @_warning
  def   eventUnknownValue( self, value ):
    logWarning("Internal error: Unknown value: %s " % value )
  
  #//-------------------------------------------------------//
  
  @_info
  def   eventOutdatedNode( self, node ):
    """
    Node needs to be rebuilt.
    """
    logInfo("Outdated node: %s" % node )
  
  #//-------------------------------------------------------//
  
  @_info
  def   eventActualNode( self, node ):
    """
    Node needs to be rebuilt.
    """
    logInfo("Actual node: %s" % node )
  
  #//-------------------------------------------------------//
  
  @_warning
  def   eventTargetIsBuiltTwiceByNodes( self, value, node1, node2 ):
    logWarning("Target '%s' is built by different nodes: '%s', '%s' " % ( value.name, node1, node2 ) )
  
  #//-------------------------------------------------------//
  
  @_debug
  def   eventBuildingNodes( self, nodes ):
    logDebug("Target '%s' is built by different nodes: '%s', '%s' " % ( value.name, node1, node2 ) )

#//===========================================================================//

info_events     = frozenset( info_events )
debug_events    = frozenset( debug_events )
status_events   = frozenset( status_events )
warning_events  = frozenset( warning_events )
all_events      = frozenset( warning_events | info_events | debug_events | status_events )
