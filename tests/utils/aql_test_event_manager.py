import sys
import os.path
import time
import pprint

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_utils import getFunctionName, printStacks
from aql_event_manager import *

#//===========================================================================//

class TestEventManager( AqlTestCase ):
  
  def   setUp( self ):
    super(TestEventManager, self).setUp()
    resetEventHandlers()
  
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
    
    @eventWarning
    def   testEvent1( status ):
      status.append( "default-event1" )
    
    @eventHandler('testEvent1')
    def   testUserEvent1( status ):
      status.append( "user-event1" )
    
    @eventStatus
    def   testEvent2( status ):
      status.append( "default-event2" )
    
    #//-------------------------------------------------------//
    
    try:
      unknown_event = False
      @eventHandler()
      def   testUserEvent2( status ):
        status.append( "user-event2" )
    except ErrorEventHandlerUnknownEvent:
      unknown_event = True
    
    self.assertTrue( unknown_event )
    
    #//-------------------------------------------------------//
    
    try:
      duplicate_event_def = False
      @eventStatus
      def   testEvent2( status ):
        status.append( "default-event2" )
    except ErrorEventHandlerAlreadyDefined:
      duplicate_event_def = True
    
    self.assertTrue( duplicate_event_def )
    
    #//-------------------------------------------------------//
    
    try:
      wrong_args = False
      @eventHandler('testEvent2')
      def   testUserEvent2( msg, status ):
        status.append( "default-event2" )
    except ErrorEventUserHandlerWrongArgs:
      wrong_args = True
    
    self.assertTrue( wrong_args )


#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
