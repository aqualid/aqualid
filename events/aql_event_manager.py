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

from aql_utils import toSequence, equalFunctionArgs
from aql_task_manager import TaskManager

#//===========================================================================//

EVENT_WARNING = 0
EVENT_STATUS = 1
EVENT_INFO = 2
EVENT_DEBUG = 3

EVENT_ALL = ( EVENT_DEBUG, EVENT_INFO, EVENT_STATUS, EVENT_WARNING )

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

class EventManager( object ):
  
  __slots__ = \
  (
    'lock',
    'tm',
    'default_handlers',
    'user_handlers',
    'ignored_events',
  )
  
  #~ #//-------------------------------------------------------//
  
  #~ _instance = __import__('__main__').__dict__.setdefault( '__AQL_EventManager_instance', [None] )
  
  #~ #//-------------------------------------------------------//
  
  #~ def   __new__( cls ):
    #~ instance = EventManager._instance
    
    #~ if instance[0] is not None:
      #~ return instance[0]
    
    #~ self = super(EventManager,cls).__new__(cls)
    #~ instance[0] = self
  
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
        defualt_handler = self.default_handlers[ event ][0]
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
    
    self.tm.start( len(handlers) )
    
    add_task = self.tm.addTask
    for handler in handlers:
      add_task( None, handler, *args, **kw )
  
  #//-------------------------------------------------------//
  
  def   __getEvents( self, importance_level ):
    events = []
    
    for event, pair in self.default_handlers.items():
      handler, level = pair
      if importance_level == level:
        events.append( event )
    
    return events
  
  #//-------------------------------------------------------//
  
  def   enableEvents( self, event_filters, enable ):
    
    events = set()
    
    with self.lock:
      for filter in toSequence(event_filters):
        if filter in EVENT_ALL:
          events.update( self.__getEvents(filter) )
        else:
          events.add( filter )
      
      if enable:
        self.ignored_events.difference_update( events )
      else:
        self.ignored_events.update( events )
  
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

def   eventWarning( handler ):  return _eventImpl( handler, EVENT_WARNING )
def   eventStatus( handler ):   return _eventImpl( handler, EVENT_STATUS )
def   eventInfo( handler ):     return _eventImpl( handler, EVENT_INFO )
def   eventDebug( handler ):    return _eventImpl( handler, EVENT_DEBUG )

#//===========================================================================//

def   eventHandler( handler ):
  _event_manager.addUserHandler( handler )
  return handler

#//===========================================================================//

def   enableEvents( event_filters ):  _event_manager.enableEvents( event_filters, True )
def   disableEvents( event_filters ): _event_manager.enableEvents( event_filters, False )
def   finishHandleEvents(): _event_manager.finish()
