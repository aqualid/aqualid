import threading

from aql_utils import checkFunctionArgs
from aql_task_manager import TaskManager
from aql_event_handler import EventHandler, verifyHandler

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
    verifyHandler( handler )
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
    
    if __debug__:
      check_args = [ None ]
      check_args += args
    
    with self.lock:
      addTask = self.tm.addTask
      for handler in self.handlers:
        try:
          task = getattr( handler, handler_method )
          
          if __debug__:
            if not checkFunctionArgs( task, check_args, kw ):
              raise InvalidHandlerMethodArgs( handler_method )
        
        except AttributeError:
          raise InvalidHandlerNoMethod( handler_method )
        
        addTask( None, task, *args, **kw )
  
  #//-------------------------------------------------------//
  
  def   reset( self ):
    with self.lock:
      self.handlers.clear()
      self.tm.stop()
