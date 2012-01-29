import threading

from aql_task_manager import TaskManager
from aql_event_handler import EventHandler

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
    self.handlers = set()
    self.tm = TaskManager( 0 )
  
  #//-------------------------------------------------------//
  
  def   addHandler( self, handler ):
    with self.lock:
      handlers = self.handlers
      handlers.add( handler )
      self.tm.start( len(handlers) )
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    def   _handleEvent( *args, **kw ):
      self.handleEvent( attr, *args, **kw )
    
    return _handleEvent
  
  #//-------------------------------------------------------//
  
  def   handleEvent( self, handler_method, *args, **kw ):
    with self.lock:
      addTask = self.tm.addTask
      for handler in self.handlers:
        task = getattr( handler, handler_method )
        addTask( 0, task, *args, **kw )
  
  #//-------------------------------------------------------//
  
  def   reset( self ):
    with self.lock:
      self.handlers.clear()
      self.tm.stop()
