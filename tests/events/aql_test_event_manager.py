import sys
import os.path
import time

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_utils import getFunctionName, printStacks
from aql_event_manager import EventManager
from aql_event_handler import EventHandler

#//===========================================================================//

class _TestEventHandler( object ):
  
  __slots__ = ( 'last_event' )
  
  def   __init__(self):
    self.last_event = None
  
  #//-------------------------------------------------------//
  
  def   eventOutdatedNode( self, node ):
    self.last_event = getFunctionName()
  
  #//-------------------------------------------------------//
  
  def   eventDataFileIsNotSync( self, filename ):
    self.last_event = getFunctionName()
  
  #//-------------------------------------------------------//
  
  def   eventDepValueIsCyclic( self, value ):
    self.last_event = getFunctionName()
  
  #//-------------------------------------------------------//
  
  def   eventUnknownValue( self, value ):
    self.last_event = getFunctionName()

  #//-------------------------------------------------------//
  
  def   eventActualNode( self, node ):
    self.last_event = getFunctionName()


#//===========================================================================//

def   _testEvent( test, event_manager, event_handler, method, *args, **kw):
  event_handler.last_event = None
  getattr(event_manager, method)( *args, **kw )
  time.sleep(0.05)
  test.assertEqual( event_handler.last_event, method )

#//===========================================================================//

def   _testDisabledEvent( test, event_manager, event_handler, method, *args, **kw):
  event_handler.last_event = None
  getattr(event_manager, method)( *args, **kw )
  time.sleep(0.05)
  test.assertIsNone( event_handler.last_event )

#//===========================================================================//

@testcase
def test_event_manager(self):
  
  em = EventManager()
  eh = _TestEventHandler()
  
  em.addHandlers( eh, True )
  
  _testEvent( self, em, eh, 'eventOutdatedNode',       None )
  _testEvent( self, em, eh, 'eventDataFileIsNotSync',  None )
  _testEvent( self, em, eh, 'eventDepValueIsCyclic',   None )
  _testEvent( self, em, eh, 'eventUnknownValue',       None )
  
  em.enableEvents( 'eventUnknownValue', False )
  _testDisabledEvent( self, em, eh, 'eventUnknownValue',  None )
  
  em.enableWarning( False )
  _testDisabledEvent( self, em, eh, 'eventDepValueIsCyclic',  None )
  
  em.enableAll( False )
  _testDisabledEvent( self, em, eh, 'eventActualNode', None )
  
  em.enableAll( True )
  _testEvent( self, em, eh, 'eventActualNode', None )
  

#//===========================================================================//

if __name__ == "__main__":
  runTests()
