import sys
import os.path
import time
import inspect

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
    print("> outdatedNode")
    #~ print(globals())
    
    print("Func name: %s" % getFunctionName() )
    print("< outdatedNode")
  
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
def   _foo( a, b, c = -5, d = -9, *agrs, **kw ):
  fs = inspect.getfullargspec(_foo)
  
  print( fs )
  print( fs.varargs )

@testcase
def test_event_manager(self):
  print( inspect.getfullargspec(self.test_event_manager) )
  _foo( 1, 2, b = -4)
  
  em = EventManager()
  
  eh = _TestEventHandler()
  eh.outdatedNode( 1 )
  
  
  em.addHandler( eh )
  em.outdatedNode( 'abc' )
  printStacks()

#//===========================================================================//

if __name__ == "__main__":
  runTests()
