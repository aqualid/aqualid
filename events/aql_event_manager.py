import threading

from aql_logging import logWarning
from aql_utils import toSequence, equalFunctionArgs, checkFunctionArgs
from aql_task_manager import TaskManager
from aql_errors import InvalidHandlerMethodArgs
from aql_event_handler import EventHandler, warning_events, info_events, debug_events, status_events, all_events

#//===========================================================================//

def   _verifyHandler( handler, verbose ):
  if type(handler) is not EventHandler:
    
    for event_method in all_events:
      handler_method = getattr( handler, event_method, None )
      if handler_method is None:
        if verbose:
          logWarning( "Handler doesn't have method: '%s'" % str(event_method) )
      else:
        method = getattr(EventHandler, event_method)
        if not equalFunctionArgs( method, handler_method ):
          raise InvalidHandlerMethodArgs( event_method )


#//===========================================================================//

class EventManager( object ):
  
  __slots__ = \
  (
    'lock',
    'tm',
    'handlers',
    'ignored_events',
  )
  
  #//-------------------------------------------------------//

  def   __init__(self):
    self.lock = threading.Lock()
    self.handlers = set()
    self.tm = TaskManager( 0 )
    self.ignored_events = set()
  
  #//-------------------------------------------------------//
  
  def   enableEvents( self, events, enable ):
    
    if isinstance( events, str ):
      events = [ events ]
    else:
      events = toSequence(events)
    
    with self.lock:
      if enable:
        self.ignored_events.difference_update( events )
      else:
        self.ignored_events.update( events )
  
  #//-------------------------------------------------------//
  
  def   enableWarning( self, enable ):    self.enableEvents( warning_events, enable )
  def   enableInfo( self, enable ):       self.enableEvents( info_events, enable )
  def   enableDebug( self, enable ):      self.enableEvents( debug_events, enable )
  def   enableStatus( self, enable ):     self.enableEvents( status_events, enable )
  def   enableAll( self, enable ):        self.enableEvents( all_events, enable )
  
  #//-------------------------------------------------------//
  
  def   addHandler( self, handler, verbose = False ):
    _verifyHandler( handler, verbose )
    with self.lock:
      handlers = self.handlers
      handlers.add( handler )
      self.tm.start( len(handlers) )
  
  #//-------------------------------------------------------//
  @staticmethod
  def   __ignoreEvent( *args, **kw ):
    pass
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    with self.lock:
      if attr in self.ignored_events:
        return self.__ignoreEvent
    
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
        task = getattr( handler, handler_method, None )
        if task is not None:
          if __debug__:
            if not checkFunctionArgs( task, check_args, kw ):
              raise InvalidHandlerMethodArgs( handler_method )
          
          addTask( None, task, *args, **kw )
  
  #//-------------------------------------------------------//
  
  def   reset( self ):
    with self.lock:
      self.ignored_events.clear()
      self.handlers.clear()
      self.tm.stop()

#//===========================================================================//

event_manager = EventManager()
