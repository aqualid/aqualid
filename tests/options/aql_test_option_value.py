import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_option_types import OptionType, BoolOptionType, EnumOptionType, RangeOptionType, ListOptionType
from aql_option_value import OptionValue, ConditionalValue, Condition, AddValue, SubValue, CallValue, SetValue

from aql_errors import EnumOptionValueIsAlreadySet, EnumOptionAliasIsAlreadySet, InvalidOptionValue

#//===========================================================================//

def   _condition( options, context, flag, opt_value = None ):
  return flag

class TestOptionValue( AqlTestCase ):
  
  @staticmethod
  def setUpClass():
    event_manager.setHandlers( EventHandler() )
  
  #//---------------------------------------------------------------------------//
  
  def test_option_value(self):
    opt_type1 = RangeOptionType( min_value = 0, max_value = 5, fix_value = True )
    
    opt_value = OptionValue( opt_type1 )
    
    cond = Condition( _condition, flag = True, opt_value = opt_value )
    cond_value  = ConditionalValue( AddValue( 2 ), cond )
    cond_value2 = ConditionalValue( AddValue( 3 ), cond )
    cond_value3 = ConditionalValue( AddValue( 3 ), cond )
    
    opt_value.appendValue( cond_value )
    opt_value.appendValue( cond_value2 )
    opt_value.appendValue( cond_value3 )
    
    self.assertEqual( opt_value.value( {} ), 5 )
  
  #//---------------------------------------------------------------------------//
  
  def test_option_value2(self):
    opt_value = OptionValue( OptionType( int ) )
    
    cond_true = Condition( _condition, flag = True )
    cond_false = Condition( _condition, cond_true, flag = False )
    cond_false = Condition( _condition, cond_false, flag = True )
    
    opt_value.appendValue( ConditionalValue( AddValue( 2 ), cond_false ) )
    self.assertEqual( opt_value.value( {} ), 0 )
    
    opt_value.appendValue( ConditionalValue( AddValue( 3 ), cond_true ) )
    self.assertEqual( opt_value.value( {} ), 3 )
    
    opt_value.appendValue( ConditionalValue( AddValue( 1 ), cond_true ) )
    self.assertEqual( opt_value.value( {} ), 4 )
    
    opt_value.appendValue( ConditionalValue( AddValue( 1 ), cond_false ) )
    self.assertEqual( opt_value.value( {} ), 4 )

  #//---------------------------------------------------------------------------//
  
  def test_option_value_enum(self):
    value_type = EnumOptionType( values = ( ('off', 0), ('size', 1), ('speed', 2) ) )
    
    opt_value = OptionValue( value_type )
    
    opt_value.appendValue( ConditionalValue( SetValue( 'size' ) ) )
    self.assertEqual( opt_value.value( {} ), 1 )
    
    opt_value.appendValue( ConditionalValue( SetValue( 'ultra' ) ) )
    self.assertRaises( InvalidOptionValue, opt_value.value, {} )
  
  #//===========================================================================//

  def test_option_value_list(self):
    opt_type1 = ListOptionType( value_type = EnumOptionType( values = ( ('off', 0), ('size', 1), ('speed', 2) ) ) )
    
    opt_value = OptionValue( opt_type1 )
    
    cond = Condition( _condition, flag = True, opt_value = opt_value )
    cond = Condition( _condition, cond, flag = True, opt_value = opt_value )
    
    cond_value  = ConditionalValue( AddValue( 1 ), cond )
    cond_value2 = ConditionalValue( AddValue( 0 ), cond )
    cond_value3 = ConditionalValue( AddValue( 2 ), cond )
    cond_value4 = ConditionalValue( AddValue( 1 ), cond )
    
    opt_value.appendValue( cond_value )
    opt_value.appendValue( cond_value2 )
    opt_value.appendValue( cond_value3 )
    opt_value.appendValue( cond_value4 )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
