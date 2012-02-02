import sys
import os.path
import time

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_utils import getFunctionName, printStacks
from aql_event_manager import EventManager
from aql_event_handler import EventHandler

#//===========================================================================//


#//===========================================================================//

class _TestEventHandler( EventHandler ):
  
  __slots__ = ( 'last_event' )
  
  def   __init__(self):
    self.last_event = None
  
  #//-------------------------------------------------------//
  
  def   outdatedNode( self, node ):
    self.last_event = getFunctionName()
  
  #//-------------------------------------------------------//
  
  def   dataFileIsNotSync( self, filename ):
    self.last_event = getFunctionName()
  
  #//-------------------------------------------------------//
  
  def   depValueIsCyclic( self, value ):
    self.last_event = getFunctionName()
  
  #//-------------------------------------------------------//
  
  def   unknownValue( self, value ):
    self.last_event = getFunctionName()


#//===========================================================================//

def   _testHandlerMethod( test, event_manager, event_handler, method, *args, **kw):
  getattr(event_manager, method)( *args, **kw )
  time.sleep(0.05)
  test.assertEqual( event_handler.last_event, method )

#//===========================================================================//

@testcase
def test_event_manager(self):
  
  em = EventManager()
  
  eh = _TestEventHandler()
  eh.outdatedNode( 'abc' )
  
  em.addHandler( eh )
  
  _testHandlerMethod( self, em, eh, 'outdatedNode',       None )
  _testHandlerMethod( self, em, eh, 'dataFileIsNotSync',  None )
  _testHandlerMethod( self, em, eh, 'depValueIsCyclic',   None )
  _testHandlerMethod( self, em, eh, 'unknownValue',       None )

#//===========================================================================//

if __name__ == "__main__":
  runTests()
