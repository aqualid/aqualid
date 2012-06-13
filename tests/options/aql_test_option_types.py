import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_option_types import OptionType, BoolOptionType, EnumOptionType, RangeOptionType, ListOptionType
from aql_simple_types import IgnoreCaseString, FilePath

from aql_errors import EnumOptionValueIsAlreadySet, EnumOptionAliasIsAlreadySet, InvalidOptionValue

#//===========================================================================//

class TestOptionTypes( AqlTestCase ):
  
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
    
    opt_type = BoolOptionType( style = ('Yes', 'No'), true_values = [], false_values = [])
    
    self.assertEqual( opt_type.rangeHelp(), ['Yes', 'No'] )
    
    opt_type.addValues('Y', 'N')
    opt_type.addValues('y', 'n')
    self.assertEqual( opt_type.rangeHelp(), ['Y, Yes', 'N, No'] )
    
    opt_type.addValues('1', '0')
    
    v = opt_type('1')
    v |= 3; self.assertEqual( v, 'y' ); self.assertIs( type(v), type(opt_type()) )
    v &= 100; self.assertEqual( v, 1 ); self.assertIs( type(v), type(opt_type()) )
    v = v & 0; self.assertEqual( v, 0 ); self.assertIs( type(v), type(opt_type()) )
    v = v | 5; self.assertEqual( v, 1 ); self.assertIs( type(v), type(opt_type()) )
    v ^= 2; self.assertEqual( v, 0 ); self.assertIs( type(v), type(opt_type()) )
    v = v ^ 2; self.assertEqual( v, 1 ); self.assertIs( type(v), type(opt_type()) )
    
    self.assertNotEqual( opt_type('1'), 0 )
    self.assertLess( opt_type('0'), 1 )
    self.assertLessEqual( opt_type('0'), 1 )
    self.assertLessEqual( opt_type('1'), 1 )
    self.assertGreater( opt_type('1'), 0 )
    self.assertGreaterEqual( opt_type('1'), 1 )
    self.assertGreaterEqual( opt_type('1'), 0 )
    
    bt = OptionType( value_type = bool )
    
    self.assertEqual( bt('1'), 1 )
    self.assertNotEqual( bt('1'), 0 )
    self.assertNotEqual( bt('0'), 0 )
    self.assertEqual( bt(1), True )
    self.assertEqual( bt(0), False )
    
    self.assertEqual( str(bt(1)), str(True) )
    self.assertEqual( str(bt(0)), str(False) )
    
    bt = BoolOptionType()
    self.assertEqual( str(bt(1)), 'True' )
    self.assertEqual( str(bt('disabled')), 'False' )
    

  #//===========================================================================//

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
    
    self.assertEqual( sorted(optimization.range()), sorted(['slow', 'off', 'ultra', 'speed', 'final', 'size']) )
    
    self.assertEqual( optimization.rangeHelp(), ['slow', 'off (or 0)', 'ultra', 'speed (or fast, 2)', 'final (or 99, 3)', 'size (or 1)'] )

  #//===========================================================================//

  def test_enum_option_int(self):
    event_manager.setHandlers( EventHandler() )
    
    optimization = EnumOptionType( values = ( (0, 10), (1, 100), (2, 1000) ),
                                   description = 'Optimization level', group = "Optimization",
                                   value_type = int )
    
    values = [0, 1, 2, 10, 100, 1000 ]
    base_values = [0, 1, 2, 0, 1, 2 ]
    
    for v, base in zip( values, base_values ):
      self.assertEqual( optimization( v ), base )
    
    self.assertEqual( optimization(), 0 )
    
    self.assertRaises( InvalidOptionValue, optimization, 3 )
    
    et = EnumOptionType( values = [] )
    self.assertRaises( InvalidOptionValue, et )

  #//===========================================================================//

  def test_range_option(self):
    event_manager.setHandlers( EventHandler() )
    
    warn_level = RangeOptionType( min_value = 0, max_value = 5, auto_correct = False,
                                  description = 'Warning level', group = "Diagnostics" )
    
    self.assertEqual( warn_level( 0 ), 0 )
    self.assertEqual( warn_level( 5 ), 5 )
    self.assertEqual( warn_level( 3 ), 3 )
    
    self.assertRaises( InvalidOptionValue, warn_level, 10 )
    self.assertRaises( InvalidOptionValue, warn_level, -1 )
    
    warn_level = RangeOptionType( min_value = 0, max_value = 5, auto_correct = True,
                                  description = 'Warning level', group = "Diagnostics" )
    
    self.assertEqual( warn_level( 0 ), 0 )
    self.assertEqual( warn_level(), 0 )
    self.assertEqual( warn_level( 3 ), 3 )
    self.assertEqual( warn_level( 5 ), 5 )
    self.assertEqual( warn_level( -100 ), 0 )
    self.assertEqual( warn_level( 100 ), 5 )
    
    self.assertEqual( warn_level.rangeHelp(), ['0 ... 5'] )
    self.assertEqual( warn_level.range(), [0, 5] )
    
    warn_level.setRange( min_value = None, max_value = None, auto_correct = False )
    self.assertEqual( warn_level( 0 ), 0 )
    self.assertRaises( InvalidOptionValue, warn_level, 1 )
    
    warn_level.setRange( min_value = None, max_value = None, auto_correct = True )
    self.assertEqual( warn_level( 0 ), 0 )
    self.assertEqual( warn_level( 10 ), 0 )
    self.assertEqual( warn_level( -10 ), 0 )
    
    self.assertRaises( InvalidOptionValue, warn_level.setRange, min_value = "abc", max_value = None )
    self.assertRaises( InvalidOptionValue, warn_level.setRange, min_value = None, max_value = "efg" )
    

  #//===========================================================================//

  def test_str_option(self):
    event_manager.setHandlers( EventHandler() )
    
    range_help = "<Case-insensitive string>"
    
    opt1 = OptionType( value_type = IgnoreCaseString, description = 'Option 1', group = "group1", range_help = range_help )
    
    self.assertEqual( opt1( 0 ), '0' )
    self.assertEqual( opt1( 'ABC' ), 'abc' )
    self.assertEqual( opt1( 'efg' ), 'EFG' )
    self.assertEqual( opt1( None ), '' )
    
    self.assertEqual( opt1.rangeHelp(), [ range_help ] )
    
  #//===========================================================================//

  def test_int_option(self):
    event_manager.setHandlers( EventHandler() )
    
    opt1 = OptionType( value_type = int, description = 'Option 1', group = "group1" )
    
    self.assertEqual( opt1( 0 ), 0 )
    self.assertEqual( opt1( '2' ), 2 )
    
    self.assertRaises( InvalidOptionValue, opt1, 'a1' )
    
    self.assertEqual( opt1.rangeHelp(), ["Value of type 'int'"] )
    
    self.assertEqual( opt1(), 0 )
    self.assertEqual( opt1(1), opt1(1) )
    
    v = opt1(1)
    v += '1'; self.assertEqual( v, 2 ); self.assertIs( type(v), type(opt1()) )
    v = v + '2'; self.assertEqual( v, 4 ); self.assertIs( type(v), type(opt1()) )
    v = v - '3'; self.assertEqual( v, 1 ); self.assertIs( type(v), type(opt1()) )
    v -= '1'; self.assertEqual( v, '0' ); self.assertIs( type(v), type(opt1()) )
    v = v + '5'; self.assertEqual( v, '5' ); self.assertIs( type(v), type(opt1()) )
    v = v * '2'; self.assertEqual( v, '10' ); self.assertIs( type(v), type(opt1()) )
    v *= '0'; self.assertEqual( v, '0' ); self.assertIs( type(v), type(opt1()) )
    v += '2'; self.assertEqual( v, '2' ); self.assertIs( type(v), type(opt1()) )
    v /= '2'; self.assertEqual( v, '1' ); self.assertIs( type(v), type(opt1()) )
    v = v / '1'; self.assertEqual( v, '1' ); self.assertIs( type(v), type(opt1()) )
    v //= '1'; self.assertEqual( v, '1' ); self.assertIs( type(v), type(opt1()) )
    v = v // '1'; self.assertEqual( v, '1' ); self.assertIs( type(v), type(opt1()) )
    v += 4; self.assertEqual( v, '5' ); self.assertIs( type(v), type(opt1()) )
    v %= 2; self.assertEqual( v, '1' ); self.assertIs( type(v), type(opt1()) )
    v = v % 2; self.assertEqual( v, '1' ); self.assertIs( type(v), type(opt1()) )
    v |= 3; self.assertEqual( v, '3' ); self.assertIs( type(v), type(opt1()) )
    v = v | 7; self.assertEqual( v, '7' ); self.assertIs( type(v), type(opt1()) )
    v &= 5; self.assertEqual( v, '5' ); self.assertIs( type(v), type(opt1()) )
    v = v & 2; self.assertEqual( v, '0' ); self.assertIs( type(v), type(opt1()) )
    v ^= 2; self.assertEqual( v, '2' ); self.assertIs( type(v), type(opt1()) )
    v = v ^ 2; self.assertEqual( v, '0' ); self.assertIs( type(v), type(opt1()) )
    v = (v + 2) ** 2; self.assertEqual( v, '4' ); self.assertIs( type(v), type(opt1()) )
    v **= 1; self.assertEqual( v, '4' ); self.assertIs( type(v), type(opt1()) )
    v >>= 2; self.assertEqual( v, '1' ); self.assertIs( type(v), type(opt1()) )
    v <<= 3; self.assertEqual( v, '8' ); self.assertIs( type(v), type(opt1()) )
    v = v << 2; self.assertEqual( v, '32' ); self.assertIs( type(v), type(opt1()) )
    v = v >> 2; self.assertEqual( v, '8' ); self.assertIs( type(v), type(opt1()) )
    
    self.assertNotEqual( v, '7' )
    self.assertLess( v, '9' )
    self.assertLessEqual( v, '9' )
    self.assertLessEqual( v, '8' )
    self.assertGreater( v, '7' )
    self.assertGreaterEqual( v, '7' )
    self.assertGreaterEqual( v, '8' )
    
    self.assertEqual( set([opt1(7), opt1(5)]), set([opt1(5), opt1(7), opt1(5)]) )

  #//===========================================================================//

  def test_path_option(self):
    event_manager.setHandlers( EventHandler() )
    
    opt1 = OptionType( value_type = FilePath, description = 'Option 1', group = "group1" )
    
    self.assertEqual( opt1( 'abc' ), 'abc' )
    self.assertEqual( opt1( '../abc/../123' ), '../123' )
    self.assertEqual( opt1( '../abc/../123' ), '../abc/../123' )
    
    self.assertEqual( opt1.rangeHelp(), ["Value of type 'FilePath'"])

  #//===========================================================================//

  def test_list_option(self):
    event_manager.setHandlers( EventHandler() )
    
    opt1 = ListOptionType( value_type = FilePath, description = 'Option 1', group = "group1" )
    
    self.assertEqual( opt1( 'abc' ), 'abc' )
    self.assertEqual( opt1( '../abc/../123' ), '../123' )
    self.assertEqual( opt1( '../abc/../123' ), '../abc/../123' )
    self.assertEqual( opt1( [1,2,3,4] ), [1,2,3,4] )
    self.assertEqual( opt1(), [] )
    self.assertEqual( opt1( NotImplemented ), [] )
    
    b = BoolOptionType( description = 'Test1', group = "Debug", style = ("On", "Off"), true_values = ["Yes","enabled"], false_values = ["No","disabled"] )
    ob = ListOptionType( value_type = b, unique = True )
    
    self.assertEqual( ob( 'yes,no' ), 'on,disabled' )
    self.assertIn( 'yes', ob( 'yes,no' ) )
    
    self.assertEqual( ob.rangeHelp(), ['enabled, On, Yes', 'disabled, No, Off'] )
    
    on = ListOptionType( value_type = int, unique = True, range_help = "List of integers" )
    
    self.assertEqual( on( '1,0,2,1,1,2,0' ), [1,0,2] )
    self.assertRaises( InvalidOptionValue, on, [1,'abc'] )
    
    self.assertEqual( on.rangeHelp(), ["List of integers"] )
    
    on = ListOptionType( value_type = int )
    self.assertEqual( on.rangeHelp(), ["List of type 'int'"] )
    


#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
