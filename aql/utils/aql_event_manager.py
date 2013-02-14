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

__all__ = (
  'EVENT_WARNING', 'EVENT_STATUS', 'EVENT_INFO', 'EVENT_DEBUG', 'EVENT_ALL',
  'eventWarning',  'eventStatus',  'eventInfo',  'eventDebug',
  'eventHandler', 'disableEvents', 'enableEvents', 'finishHandleEvents',
  'disableDefaultHandlers', 'enableDefaultHandlers',
  'ErrorEventUserHandlerWrongArgs', 'ErrorEventHandlerAlreadyDefined', 'ErrorEventHandlerUnknownEvent',
)

import threading

from aql.types import Singleton

from .aql_utils import toSequence, equalFunctionArgs
from .aql_task_manager import TaskManager

#//===========================================================================//

EVENT_WARNING = 0
EVENT_STATUS = 1
EVENT_INFO = 2
EVENT_DEBUG = 3

EVENT_ALL = ( EVENT_DEBUG, EVENT_INFO, EVENT_STATUS, EVENT_WARNING )

#//===========================================================================//

class   ErrorEventUserHandlerWrongArgs ( Exception ):
  def   __init__( self, event, handler ):
    msg = "Invalid arguments of event '%s' handler method: '%s'" % (event, handler)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorEventHandlerAlreadyDefined ( Exception ):
  def   __init__( self, event, handler, other_handler ):
    msg = "Duplicate event '%s' definition to default handlers: '%s', '%s'" % (event, handler, other_handler )
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorEventHandlerUnknownEvent ( Exception ):
  def   __init__( self, event ):
    msg = "Unknown event: '%s'" % str(event)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class EventManager( Singleton ):
  
  _instance = []
  
  __slots__ = \
  (
    'lock',
    'tm',
    'default_handlers',
    'user_handlers',
    'ignored_events',
    'disable_defaults',
  )
  
  #//-------------------------------------------------------//

  def   __init__(self):
    self.lock = threading.Lock()
    self.default_handlers = {}
    self.user_handlers = {}
    self.tm = TaskManager( 0 )
    self.ignored_events = set()
    self.disable_defaults = False
  
  #//-------------------------------------------------------//
  
  def   addDefaultHandler( self, handler, importance_level, event = None ):
    if not event:
      event = handler.__name__
    
    with self.lock:
      pair = (handler, importance_level)
      other = self.default_handlers.setdefault( event, pair )
      if other != pair:
        raise ErrorEventHandlerAlreadyDefined( event, other[0], handler )
  
  #//-------------------------------------------------------//
  
  def   addUserHandler( self, user_handler, event = None ):
    
    if not event:
      event = user_handler.__name__
    
    with self.lock:
      try:
        defualt_handler = self.default_handlers[ event ][0]
      except KeyError:
        raise ErrorEventHandlerUnknownEvent( event )
      
      if not equalFunctionArgs( defualt_handler, user_handler ):
        raise ErrorEventUserHandlerWrongArgs( event, user_handler )
      
      self.user_handlers.setdefault( event, [] ).append( user_handler )
  
  #//-------------------------------------------------------//
  
  def   sendEvent( self, event, *args, **kw ):
    
    with self.lock:
      if event in self.ignored_events:
        return
      
      handlers = list(self.user_handlers.get( event, [] ))
      if not self.disable_defaults:
        default_handler = self.default_handlers[ event ][0]
        handlers.append( default_handler )
    
    self.tm.start( len(handlers) )
    
    add_task = self.tm.addTask
    for handler in handlers:
      add_task( None, handler, *args, **kw )
  
  #//-------------------------------------------------------//
  
  def   __getEvents( self, event_filters ):
    events = set()
    
    for filter in toSequence(event_filters):
      if filter not in EVENT_ALL:
        events.add( filter )
      else:
        for event, pair in self.default_handlers.items():
          handler, level = pair
          if filter == level:
            events.add( event )
    
    return events
  
  #//-------------------------------------------------------//
  
  def   enableEvents( self, event_filters, enable ):
    
    events = set()
    
    with self.lock:
      events = self.__getEvents( event_filters )
      
      if enable:
        self.ignored_events.difference_update( events )
      else:
        self.ignored_events.update( events )
  
  #//-------------------------------------------------------//
  
  def   disableDefaultHandlers( self ):
    self.disable_defaults = True
  
  #//-------------------------------------------------------//
  
  def   enableDefaultHandlers( self ):
    self.disable_defaults = False
  
  #//-------------------------------------------------------//
  
  def   finish( self ):
    self.tm.finish()

#//===========================================================================//

def   _eventImpl( handler, importance_level, event = None ):
  
  if not event:
    event = handler.__name__
  
  event_manager = EventManager.instance()
  event_manager.addDefaultHandler( handler, importance_level )
  
  def   _sendEvent( *args, **kw ):
    event_manager.sendEvent( event, *args, **kw )
  
  return _sendEvent

#//===========================================================================//

def   eventWarning( handler ):  return _eventImpl( handler, EVENT_WARNING )
def   eventStatus( handler ):   return _eventImpl( handler, EVENT_STATUS )
def   eventInfo( handler ):     return _eventImpl( handler, EVENT_INFO )
def   eventDebug( handler ):    return _eventImpl( handler, EVENT_DEBUG )

#//===========================================================================//

def   eventHandler( event = None ):
  def   _eventHandlerImpl( handler ):
    EventManager.instance().addUserHandler( handler, event )
    return handler
  
  return _eventHandlerImpl

#//===========================================================================//

def   enableEvents( event_filters ):
  EventManager.instance().enableEvents( event_filters, True )

#//===========================================================================//

def   disableEvents( event_filters ):
  EventManager.instance().enableEvents( event_filters, False )

#//===========================================================================//

def   disableDefaultHandlers():
  EventManager.instance().disableDefaultHandlers()

#//===========================================================================//

def   enableDefaultHandlers():
  EventManager.instance().enableDefaultHandlers()

#//===========================================================================//

def   finishHandleEvents():
  EventManager.instance().finish()

#//===========================================================================//
