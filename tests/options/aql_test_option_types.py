﻿import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_option_types import OptionType, BoolOptionType, EnumOptionType, RangeOptionType
from aql_simple_types import IgnoreCaseString, FilePath

from aql_errors import EnumOptionValueIsAlreadySet, EnumOptionAliasIsAlreadySet, InvalidOptionValue

#//===========================================================================//

@testcase
def test_bool_option(self):
  event_manager.setHandlers( EventHandler() )
  
  debug_symbols = BoolOptionType( description = 'Include debug symbols', group = "Debug", style = (True, False) )
  
  true_values = ['tRUe', 't', '1', 'yeS', 'ENABled', 'On', 'y', 1, 2, 3, -1, True ]
  false_values = ['FAlsE', 'F', '0', 'nO', 'disabled', 'oFF', 'N', 0, None, False ]
  
  for t in true_values:
    v = debug_symbols( t )
    self.assertTrue( v ); self.assertEqual( str(v), str(True) )
  
  for t in false_values:
    v = debug_symbols( t )
    self.assertFalse( v ); self.assertEqual( str(v), str(False) )
  
  debug_symbols = BoolOptionType( description = 'Include debug symbols', group = "Debug", style = ('ON', 'OFF'))
  
  v = debug_symbols( 'TRUE' )
  self.assertTrue( v ); self.assertEqual( str(v), 'ON' )
  
  v = debug_symbols( 0 )
  self.assertFalse( v ); self.assertEqual( str(v), 'OFF' )
  
  #~ print( debug_symbols.rangeHelp() )

#//===========================================================================//

@testcase
def test_enum_option(self):
  event_manager.setHandlers( EventHandler() )
  
  optimization = EnumOptionType( values = ( ('off', 0), ('size', 1), ('speed', 2) ),
                                 description = 'Compiler optimization level', group = "Optimization" )
  
  values = ['oFF', 'siZe', 'SpeeD', '0', '1', '2', 0, 1, 2]
  base_values = ['off', 'size', 'speed', 'off', 'size', 'speed', 'off', 'size', 'speed']
  
  for v, base in zip( values, base_values ):
    self.assertEqual( optimization( v ), base )
  
  with self.assertRaises( InvalidOptionValue ):
    optimization( 3 )
    
  optimization.addValues( {'final': 3} )
  
  optimization.addValues( {'final': 99} )
  optimization.addValues( {2: 'fast'} )
  with self.assertRaises( EnumOptionAliasIsAlreadySet ):
    optimization.addValues( {'slow': 'fast'} )
  
  with self.assertRaises( EnumOptionValueIsAlreadySet ):
    optimization.addValues( {'slow': 'speed'} )
  
  optimization.addValues( ('ultra', 'speed') )
  self.assertEqual( optimization( 'ULTRA' ), 'ultra' )
  
  #~ print( optimization.rangeHelp() )

#//===========================================================================//

@testcase
def test_enum_option_int(self):
  event_manager.setHandlers( EventHandler() )
  
  optimization = EnumOptionType( values = ( (0, 10), (1, 100), (2, 1000) ),
                                 description = 'Optimization level', group = "Optimization",
                                 value_type = int )
  
  values = [0, 1, 2, 10, 100, 1000 ]
  base_values = [0, 1, 2, 0, 1, 2 ]
  
  for v, base in zip( values, base_values ):
    self.assertEqual( optimization( v ), base )
  
  with self.assertRaises( InvalidOptionValue ):
    optimization( 3 )

#//===========================================================================//

@testcase
def test_range_option(self):
  event_manager.setHandlers( EventHandler() )
  
  warn_level = RangeOptionType( min_value = 0, max_value = 5,
                                description = 'Warning level', group = "Diagnostics" )
  
  self.assertEqual( warn_level( 0 ), 0 )
  self.assertEqual( warn_level( 5 ), 5 )
  self.assertEqual( warn_level( 3 ), 3 )
  
  with self.assertRaises( InvalidOptionValue ):
    warn_level( 10 )
  
  with self.assertRaises( InvalidOptionValue ):
    warn_level( -1 )
  
  warn_level = RangeOptionType( min_value = 0, max_value = 5, fix_value = True,
                                description = 'Warning level', group = "Diagnostics" )
  
  self.assertEqual( warn_level( 0 ), 0 )
  self.assertEqual( warn_level( 3 ), 3 )
  self.assertEqual( warn_level( 5 ), 5 )
  self.assertEqual( warn_level( -100 ), 0 )
  self.assertEqual( warn_level( 100 ), 5 )
  
  #~ print( warn_level.rangeHelp() )

#//===========================================================================//

@testcase
def test_str_option(self):
  event_manager.setHandlers( EventHandler() )
  
  opt1 = OptionType( value_type = IgnoreCaseString, description = 'Option 1', group = "group1", range_help = "<Case-insensitive string>")
  
  self.assertEqual( opt1( 0 ), '0' )
  self.assertEqual( opt1( 'ABC' ), 'abc' )
  self.assertEqual( opt1( 'efg' ), 'EFG' )
  self.assertEqual( opt1( None ), '' )
  
  #~ print( opt1.rangeHelp() )
  
#//===========================================================================//

@testcase
def test_int_option(self):
  event_manager.setHandlers( EventHandler() )
  
  opt1 = OptionType( value_type = int, description = 'Option 1', group = "group1" )
  
  self.assertEqual( opt1( 0 ), 0 )
  self.assertEqual( opt1( '2' ), 2 )
  
  with self.assertRaises( InvalidOptionValue ):
    opt1( 'a1' )
  
  #~ print( opt1.rangeHelp() )

#//===========================================================================//

@testcase
def test_path_option(self):
  event_manager.setHandlers( EventHandler() )
  
  opt1 = OptionType( value_type = FilePath, description = 'Option 1', group = "group1" )
  
  self.assertEqual( opt1( 'abc' ), 'abc' )
  self.assertEqual( opt1( '../abc/../123' ), '../123' )
  self.assertEqual( opt1( '../abc/../123' ), '../abc/../123' )
  
  #~ print( opt1.rangeHelp() )


#//===========================================================================//

if __name__ == "__main__":
  runTests()