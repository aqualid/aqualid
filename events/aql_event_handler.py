
#~ from aql_logging import logInfo,logWarning,logError

#//===========================================================================//

_events = set()

def   _event( event_method ):
  print( event_method )
  print( dir(event_method) )
  _events.add( event_method )

#//-------------------------------------------------------//
def   verifyHandler( handler ):
  for event_method in _events:
    try:
      handler_method = handler.getattr( event_method.__name__ )
      if not equalFunctionArgs( event_method, handler_method ):
        raise InvalidHandlerMethodArgs( event_method )
    except AttributeError:
      raise InvalidHandlerNoMethod( event_method )
    
  
#//===========================================================================//

class EventHandler( object ):
  
  #//-------------------------------------------------------//
  
  @_event
  def   outdatedNode( self, node ):
    logInfo("Outdated node: %s" % node )
  
  #//-------------------------------------------------------//
  @_event
  def   dataFileIsNotSync( self, filename ):
    logWarning("Internal error: DataFile is unsynchronized")
  
  #//-------------------------------------------------------//
  @_event
  def   depValueIsCyclic( self, value ):
    logWarning("Internal error: Cyclic dependency value: %s" % value )
  
  #//-------------------------------------------------------//
  @_event
  def   unknownValue( self, value ):
    logWarning("Internal error: Unknown value: %s " % value )
  
  #//-------------------------------------------------------//
