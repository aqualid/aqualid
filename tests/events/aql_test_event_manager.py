import sys
import os.path
import time
import traceback

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
    
    #~ try:
      #~ raise Exception()
    #~ except Exception as err:
      #~ print(err.__traceback__.tb_frame.f_code.co_name)
    
    #~ import traceback
    #~ method_name = traceback.extract_stack( limit = 1 )
    #~ print("outdatedNode: %s" % method_name )
    #~ self.last_event = method_name
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

@testcase
def test_event_manager(self):
  em = EventManager()
  
  eh = _TestEventHandler()
  eh.outdatedNode( 1 )
  
  
  em.addHandler( eh )
  em.outdatedNode( 'abc' )
  printStacks()

#//===========================================================================//

if __name__ == "__main__":
  runTests()
