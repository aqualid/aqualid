class EventHandler( object ):
  
  #//-------------------------------------------------------//
  
  def   outdatedNode( self, node ):
    logInfo("Outdated node: %s" % node )
  
  #//-------------------------------------------------------//
  
  def   data( self, event_id, **kw ):
    with self.lock:
      handlers = self.handlers.get( event_id, [] )
    
    addTask = self.tm.addTask
    for handler in handlers:
      addTask( 0, handler, kw )
  
  #//-------------------------------------------------------//
  
  def   release( self ):
    self.tm.stop()
