import threading

from aql_task_manager import TaskManager

class EventManager( object ):
  
  __slots__ = \
  (
    'lock',
    'handlers',
    'tm',
  )
  
  #//-------------------------------------------------------//

  def   __init__(self):
    self.lock = threading.Lock()
    self.handlers = {}
    self.tm = TaskManager( 0 )
  
  #//-------------------------------------------------------//
  
  def   addHandler( self, event_id, handler ):
    with self.lock:
      handlers = self.handlers.setdefault( event_id, [] )
      handlers.append( handler )
      
      self.tm.start( len(handlers) )
  
  #//-------------------------------------------------------//
  
  def   sendEvent( self, event_id, **kw ):
    with self.lock:
      handlers = self.handlers.get( event_id, [] )
    
    addTask = self.tm.addTask
    for handler in handlers:
      addTask( 0, handler, kw )
  
  #//-------------------------------------------------------//
  
  def   release( self ):
    self.tm.stop()
