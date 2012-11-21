#
# Copyright (c) 2011,2012 The developers of Aqualid project - http://aqualid.googlecode.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#


import threading

from aql_logging import logWarning
from aql_utils import toSequence, equalFunctionArgs, checkFunctionArgs
from aql_task_manager import TaskManager
from aql_event_handler import EventHandler, warning_events, info_events, debug_events, status_events, all_events

#//===========================================================================//

EVENT_WARNING = 0
EVENT_WARN = EVENT_WARNING
EVENT_INFO = 1
EVENT_DEBUG = 2


#//===========================================================================//

class   ErrorEventHandlerWrongArgs ( Exception ):
  def   __init__( self, method ):
    msg = "Invalid arguments of handler method: '%s'" % str(method)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorEventHandlerAlreadyExists ( Exception ):
  def   __init__( self, handler ):
    msg = "Similar handler is already exists: '%s'" % str(handler)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorEventHandlerUnknownEvent ( Exception ):
  def   __init__( self, event ):
    msg = "Unknown event: '%s'" % str(event)
    super(type(self), self).__init__( msg )

#//===========================================================================//

def   _verifyHandlers( handlers, verbose ):
  
  for handler in handlers:
    if type(handler) is not EventHandler:
      for event_method in all_events:
        handler_method = getattr( handler, event_method, None )
        if handler_method is None:
          if verbose:
            logWarning( "Handler doesn't have method: '%s'" % str(event_method) )
        else:
          method = getattr(EventHandler, event_method)
          if not equalFunctionArgs( method, handler_method ):
            raise ErrorEventHandlerWrongArgs( event_method )

#//===========================================================================//

class EventManager( object ):
  
  __slots__ = \
  (
    'lock',
    'tm',
    'default_handlers',
    'user_handlers',
    'ignored_events',
  )
  
  #//-------------------------------------------------------//
  
  _instance = __import__('__main__').__dict__.setdefault( '__AQL_EventManager_instance', [None] )
  
  #//-------------------------------------------------------//
  
  def   __new__( cls ):
    instance = EventManager._instance
    
    if instance[0] is not None:
      return instance[0]
    
    self = super(EventManager,cls).__new__(cls)
    instance[0] = self
  
  #//-------------------------------------------------------//

  def   __init__(self):
    self.lock = threading.Lock()
    self.default_handlers = {}
    self.user_handlers = {}
    self.tm = TaskManager( 0 )
    self.ignored_events = set()
  
  #//-------------------------------------------------------//
  
  def   addDefaultHandler( self, handler, importance_level ):
    event = handler.__name__
    
    with self.lock:
      pair = (handler, importance_level)
      other = self.default_handlers.setdefault( event, pair )
      if other != pair:
        raise ErrorEventHandlerAlreadyExists( handler )
  
  #//-------------------------------------------------------//
  
  def   addUserHandler( self, user_handler ):
    
    event = user_handler.__name__
    
    with self.lock:
      try:
        defualt_handler = self.default_handlers[ event ]
      except KeyError:
        raise ErrorEventHandlerUnknownEvent( event )
      
      if not equalFunctionArgs( defualt_handler, user_handler ):
        raise ErrorEventHandlerWrongArgs( event_method )
      
      self.user_handlers.setdefault( event, [] ).append( user_handler )
  
  #//-------------------------------------------------------//
  
  def   sendEvent( self, event, *args, **kw ):
    
    with self.lock:
      if event in self.ignored_events:
        return
      
      handlers = self.user_handlers.get( event, [] )
      default_handler = self.default_handlers.get( event, (None, 0) )[0]
      if default_handler:
        handlers.append( default_handler )
    
    addTask = self.tm.addTask
    for handler in handlers:
      addTask( None, handler, *args, **kw )
  
  #//-------------------------------------------------------//
  
  def   enableEvents( self, events, enable ):
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
  
  def   finish( self ):
    self.tm.finish()

#//===========================================================================//

_event_manager = EventManager()

#//===========================================================================//

class   HandlerProxy( object ):
  __slots__ = ('event_manager', 'event')
  
  def   __init__( self, event_manager, handler ):
    self.event_manager = event_manager
    self.event = handler.__name__
  
  def   __call__( self, *args, **kw ):
    self.event_manager.sendEvent( self.event, *args, **kw )

#//===========================================================================//

def   _eventImpl( handler, importance_level ):
  event_manager = _event_manager
  event_manager.addDefaultHandler( handler, importance_level )
  return HandlerProxy( event_manager, handler )

#//===========================================================================//

def   eventInfo( handler ):     return _eventImpl( handler, EVENT_INFO )
def   eventWarning( handler ):  return _eventImpl( handler, EVENT_WARNING )
def   eventDebug( handler ):    return _eventImpl( handler, EVENT_DEBUG )
