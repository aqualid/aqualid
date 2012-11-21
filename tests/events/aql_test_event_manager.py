import sys
import os.path
import time

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_utils import getFunctionName, printStacks
from aql_event_manager import eventWarning, eventHandler, finishHandleEvents

#//===========================================================================//

@eventWarning
def   testEvent1( msg, status ):
  status.append( "default" )

_test_event1 = testEvent1

#//===========================================================================//

@eventHandler
def   testEvent1( msg, status ):
  status.append( "user" )

#//===========================================================================//

class TestEventManager( AqlTestCase ):
  def test_event_manager(self):
    
    status = []
    _test_event1( "test event #1", status )
    finishHandleEvents()
    self.assertIn( "default", status )
    self.assertIn( "user", status )
    
    status = []
    _test_event1( "test event #2", status )
    finishHandleEvents()
    self.assertIn( "default", status )
    self.assertIn( "user", status )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
