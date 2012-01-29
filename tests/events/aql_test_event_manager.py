import sys
import os.path
import time

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_event_manager import EventManager
from aql_event_handler import EventHandler

#//===========================================================================//

class _TestEventHandler( EventHandler ):
  
  __slots__ = ( 'last_event' )
  
  def   __init__(self):
    self.last_event = None
  
  #//-------------------------------------------------------//
  
  def   outdatedNode( self, node ):
    print("outdatedNode: %s" % __function__ )
    self.last_event = __name__
  
  #//-------------------------------------------------------//
  
  def   dataFileIsNotSync( self, filename ):
    logWarning("Internal error: DataFile is unsynchronized")
  
  #//-------------------------------------------------------//
  
  def   depValueIsCyclic( self, value ):
    logWarning("Internal error: Cyclic dependency value: %s" % value )
  
  #//-------------------------------------------------------//
  
  def   unknownValue( self, value ):
    logWarning("Internal error: Unknown value: %s " % value )


#//===========================================================================//

@testcase
def test_event_manager(self):
  em = EventManager()
  
  eh = _TestEventHandler()
  
  em.addHandler( eh )
  em.outdatedNode( 'abc' )

#//===========================================================================//

if __name__ == "__main__":
  runTests()
