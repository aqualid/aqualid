import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_option_types import BoolOption

#//===========================================================================//

@testcase
def test_bool_option(self):
  event_manager.setHandlers( EventHandler() )
  
  debug_symbols = BoolOption( description = 'Include debug symbols', group = "Debug", style = (True, False))
  
  true_values = ['tRUe', 't', '1', 'yeS', 'ENABled', 'On', 'y', 1, 2, 3, -1, True ]
  false_values = ['FAlsE', 'F', '0', 'nO', 'disabled', 'oFF', 'N', 0, None, False ]
  
  for t in true_values:
    v = debug_symbols.convert( t )
    self.assertTrue( v ); self.assertEqual( str(v), str(True) )
  
  for t in false_values:
    v = debug_symbols.convert( t )
    self.assertFalse( v ); self.assertEqual( str(v), str(False) )
  
  debug_symbols = BoolOption( description = 'Include debug symbols', group = "Debug", style = ('ON', 'OFF'))
  
  v = debug_symbols.convert( 'TRUE' )
  self.assertTrue( v ); self.assertEqual( str(v), 'ON' )
  
  v = debug_symbols.convert( 0 )
  self.assertFalse( v ); self.assertEqual( str(v), 'OFF' )


#//===========================================================================//

if __name__ == "__main__":
  runTests()
