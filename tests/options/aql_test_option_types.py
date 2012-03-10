import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_option_types import BoolOption, EnumOption

from aql_errors import EnumOptionValueIsAlreadySet, EnumOptionAliasIsAlreadySet, EnumOptionInvalidValue

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
  
  #~ print( debug_symbols.rangeHelp() )

#//===========================================================================//

@testcase
def test_enum_option(self):
  event_manager.setHandlers( EventHandler() )
  
  optimization = EnumOption( description = 'Compiler optimization level', group = "Optimization",
                             values = ( ('off', 0), ('size', 1), ('speed', 2) ) )
  
  values = ['oFF', 'siZe', 'SpeeD', '0', '1', '2', 0, 1, 2]
  base_values = ['off', 'size', 'speed', 'off', 'size', 'speed', 'off', 'size', 'speed']
  
  for v, base in zip( values, base_values ):
    self.assertEqual( optimization.convert( v ), base )
  
  with self.assertRaises( EnumOptionInvalidValue ):
    optimization.convert( 3 )
    
  optimization.addValues( {'final': 3} )
  
  optimization.addValues( {'final': 99} )
  optimization.addValues( {2: 'fast'} )
  with self.assertRaises( EnumOptionAliasIsAlreadySet ):
    optimization.addValues( {'slow': 'fast'} )
  
  with self.assertRaises( EnumOptionValueIsAlreadySet ):
    optimization.addValues( {'slow': 'speed'} )
  
  optimization.addValues( ('ultra', 'speed') )
  self.assertEqual( optimization.convert( 'ULTRA' ), 'ultra' )
  
  #~ print( optimization.rangeHelp() )


#//===========================================================================//

if __name__ == "__main__":
  runTests()
