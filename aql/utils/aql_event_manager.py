#
# Copyright (c) 2011-2014 The developers of Aqualid project
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
  'EVENT_WARNING', 'EVENT_STATUS', 'EVENT_DEBUG', 'EVENT_ALL',
  'eventWarning',  'eventStatus',  'eventDebug', 'eventError',
  'eventHandler', 'disableEvents', 'enableEvents', 'EventSettings', 'setEventSettings',
  'disableDefaultHandlers', 'enableDefaultHandlers', 'addUserHandler', 'removeUserHandler',
  'ErrorEventUserHandlerWrongArgs', 'ErrorEventHandlerAlreadyDefined', 'ErrorEventHandlerUnknownEvent',
)

import types
import itertools

from aql.util_types import toSequence, AqlException

from .aql_utils import equalFunctionArgs

#//===========================================================================//

EVENT_ERROR, \
EVENT_WARNING, \
EVENT_STATUS, \
EVENT_DEBUG, \
  = EVENT_ALL = tuple(range(4))

#//===========================================================================//

class   ErrorEventUserHandlerWrongArgs ( AqlException ):
  def   __init__( self, event, handler ):
    msg = "Invalid arguments of event '%s' handler method: '%s'" % (event, handler)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorEventHandlerAlreadyDefined ( AqlException ):
  def   __init__( self, event, handler, other_handler ):
    msg = "Duplicate event '%s' definition to default handlers: '%s', '%s'" % (event, handler, other_handler )
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorEventHandlerUnknownEvent ( AqlException ):
  def   __init__( self, event ):
    msg = "Unknown event: '%s'" % (event,)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class EventSettings( object ):
  __slots__ = (
    'brief',
    'with_output',
    'trace_exec'
  )
  
  def   __init__(self, brief = True, with_output = True, trace_exec = False ):
    self.brief = brief
    self.with_output = with_output
    self.trace_exec = trace_exec

#//===========================================================================//

class EventManager( object ):
  
  __slots__ = (
    'default_handlers',
    'user_handlers',
    'ignored_events',
    'disable_defaults',
    'settings',
  )
  
  #//-------------------------------------------------------//

  def   __init__( self ):
    self.default_handlers = {}
    self.user_handlers = {}
    self.ignored_events = set()
    self.disable_defaults = False
    self.settings = EventSettings()
  
  #//-------------------------------------------------------//
  
  def   addDefaultHandler( self, handler, importance_level, event = None ):
    if not event:
      event = handler.__name__
    
    pair = (handler, importance_level)
    other = self.default_handlers.setdefault( event, pair )
    if other != pair:
      raise ErrorEventHandlerAlreadyDefined( event, other[0], handler )
  
  #//-------------------------------------------------------//
  
  def   addUserHandler( self, user_handler, event = None ):
    
    if not event:
      event = user_handler.__name__
    
    try:
      default_handler = self.default_handlers[ event ][0]
    except KeyError:
      raise ErrorEventHandlerUnknownEvent( event )
    
    if not equalFunctionArgs( default_handler, user_handler ):
      raise ErrorEventUserHandlerWrongArgs( event, user_handler )
    
    self.user_handlers.setdefault( event, [] ).append( user_handler )
  
  #//-------------------------------------------------------//
  
  def   removeUserHandler( self, user_handlers ):
    
    for event, handlers in self.user_handlers.items():
      for user_handler in toSequence( user_handlers ):
        try:
          handlers.remove( user_handler )
        except ValueError:
          pass
  
  #//-------------------------------------------------------//
  
  def   sendEvent( self, event, *args, **kw ):
    
    if event in self.ignored_events:
      return
    
    if self.disable_defaults:
      default_handlers = []
    else:
      default_handlers = [ self.default_handlers[ event ][0] ]
    
    user_handlers = self.user_handlers.get( event, [] )
    
    args = ( self.settings,) + args
    for handler in itertools.chain( user_handlers, default_handlers ):
      handler( *args, **kw )
  
  #//-------------------------------------------------------//
  
  def   __getEvents( self, event_filters ):
    events = set()
    
    for event_filter in toSequence(event_filters):
      if event_filter not in EVENT_ALL:
        events.add( event_filter )
      else:
        for event, pair in self.default_handlers.items():
          handler, level = pair
          if event_filter == level:
            events.add( event )
    
    return events
  
  #//-------------------------------------------------------//
  
  def   enableEvents( self, event_filters, enable ):
    
      events = self.__getEvents( event_filters )
      
      if enable:
        self.ignored_events.difference_update( events )
      else:
        self.ignored_events.update( events )
  
  #//-------------------------------------------------------//
  
  def   enableDefaultHandlers( self, enable ):
    self.disable_defaults = not enable
  
  #//-------------------------------------------------------//
  
  def   setSettings(self, settings ):
    self.settings = settings

_event_manager = EventManager()

#//===========================================================================//

def   _eventImpl( handler, importance_level, event = None ):
  
  if not event:
    event = handler.__name__
  
  _event_manager.addDefaultHandler( handler, importance_level )
  
  def   _sendEvent( *args, **kw ):
    _event_manager.sendEvent( event, *args, **kw )
  
  return _sendEvent

#//===========================================================================//

def   eventError( handler ):    return _eventImpl( handler, EVENT_ERROR )
def   eventWarning( handler ):  return _eventImpl( handler, EVENT_WARNING )
def   eventStatus( handler ):   return _eventImpl( handler, EVENT_STATUS )
def   eventDebug( handler ):    return _eventImpl( handler, EVENT_DEBUG )

#//===========================================================================//

def   eventHandler( event = None ):
  
  if isinstance( event, (types.FunctionType, types.MethodType)):
    _event_manager.addUserHandler( event )
    return event
  
  def   _eventHandlerImpl( handler ):
    _event_manager.addUserHandler( handler, event )
    return handler
  
  return _eventHandlerImpl

#//===========================================================================//

def   setEventSettings( settings ):
  _event_manager.setSettings( settings )

#//===========================================================================//

def   enableEvents( event_filters ):
  _event_manager.enableEvents( event_filters, True )

#//===========================================================================//

def   disableEvents( event_filters ):
  _event_manager.enableEvents( event_filters, False )

#//===========================================================================//

def   disableDefaultHandlers( ):
  _event_manager.enableDefaultHandlers( False )

#//===========================================================================//

def   enableDefaultHandlers():
  _event_manager.enableDefaultHandlers( True )

#//===========================================================================//

def   addUserHandler( handler, event = None ):
    _event_manager.addUserHandler( handler, event )

#//===========================================================================//

def   removeUserHandler( handler ):
    _event_manager.removeUserHandler( handler )

#//===========================================================================//
