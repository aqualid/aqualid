import sys
import os.path
import time
import pprint

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_utils import getFunctionName, printStacks
from aql_event_manager import *
from aql_event_manager import EventManager

#//===========================================================================//

class TestEventManager( AqlTestCase ):
  
  #//-------------------------------------------------------//
  
  def test_event_manager(self):
    
    @eventWarning
    def   testEvent1( status ):
      status.append( "default-event1" )
    
    @eventHandler('testEvent1')
    def   testUserEvent1( status ):
      status.append( "user-event1" )
    
    @eventStatus
    def   testEvent2( status ):
      status.append( "default-event2" )
    
    @eventHandler('testEvent2')
    def   testUserEvent2( status ):
      status.append( "user-event2" )
    
    status = []
    testEvent1( status )
    finishHandleEvents()
    self.assertIn( "default-event1", status )
    self.assertIn( "user-event1", status )
    
    status = []
    testEvent1( status )
    finishHandleEvents()
    self.assertIn( "default-event1", status )
    self.assertIn( "user-event1", status )
    
    status = []
    disableDefaultHandlers()
    testEvent1( status )
    finishHandleEvents()
    self.assertNotIn( "default-event1", status )
    self.assertIn( "user-event1", status )
    
    status = []
    enableDefaultHandlers()
    disableEvents( EVENT_WARNING )
    testEvent1( status )
    testEvent2( status )
    finishHandleEvents()
    self.assertNotIn( "default-event1", status )
    self.assertNotIn( "user-event1", status )
    self.assertIn( "default-event2", status )
    self.assertIn( "user-event2", status )
  
  #//=======================================================//
  
  def test_event_manager_errors(self):
    
    em = EventManager()
    
    def   testEvent1( status ):
      status.append( "default-event1" )
    
    def   testUserEvent1( status ):
      status.append( "user-event1" )
    
    def   testEvent2( status ):
      status.append( "default-event2" )
    
    def   testUserEvent2( msg, status ):
      status.append( "user-event2" )
    
    em.addDefaultHandler( testEvent1, EVENT_WARNING )
    em.addDefaultHandler( testEvent2, EVENT_STATUS )
    em.addUserHandler( testUserEvent1, 'testEvent1' )
    
    #//-------------------------------------------------------//
    
    self.assertRaises( ErrorEventHandlerAlreadyDefined, em.addDefaultHandler, testEvent2, EVENT_WARNING )
    self.assertRaises( ErrorEventHandlerUnknownEvent, em.addUserHandler, testUserEvent2 )
    self.assertRaises( ErrorEventUserHandlerWrongArgs, em.addUserHandler, testUserEvent2, 'testEvent2' )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
