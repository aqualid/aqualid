import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_option_types import OptionType, BoolOptionType, EnumOptionType, RangeOptionType, ListOptionType
from aql_option_value import OptionValue, OptionConditionalValue, OptionCondition, OptionValuesAdd, subOptionValues, addOptionValues

from aql_errors import EnumOptionValueIsAlreadySet, EnumOptionAliasIsAlreadySet, InvalidOptionValue

#//===========================================================================//

def   _condition( options, context, flag, opt_value ):
  print("context[opt_value]: %s" % (context[opt_value], ))
  return flag

@testcase
def test_option_value(self):
  event_manager.setHandlers( EventHandler() )
  
  opt_type1 = RangeOptionType( min_value = 0, max_value = 5, fix_value = True )
  
  opt_value = OptionValue( opt_type1 )
  
  cond = OptionCondition( _condition, flag = True, opt_value = opt_value )
  cond_value  = OptionConditionalValue( 2, OptionValuesAdd( opt_type1 ), [cond] )
  cond_value2 = OptionConditionalValue( 3, OptionValuesAdd( opt_type1 ), [cond] )
  cond_value3 = OptionConditionalValue( 3, OptionValuesAdd( opt_type1 ), [cond] )
  
  opt_value.appendValue( cond_value )
  opt_value.appendValue( cond_value2 )
  opt_value.appendValue( cond_value3 )
  
  self.assertEqual( opt_value.value( {} ), 5 )
  print("Value: %s" % (opt_value.value( {} ) ))

#//===========================================================================//

@testcase
def test_option_value_list(self):
  event_manager.setHandlers( EventHandler() )
  
  opt_type1 = ListOptionType( value_type = EnumOptionType( values = ( ('off', 0), ('size', 1), ('speed', 2) ) ) )
  
  opt_value = OptionValue( opt_type1 )
  
  cond = OptionCondition( _condition, flag = True, opt_value = opt_value )
  cond_value = OptionConditionalValue( 1, addOptionValues, [cond] )
  cond_value2 = OptionConditionalValue( 0, addOptionValues, [cond] )
  cond_value3 = OptionConditionalValue( 2, addOptionValues, [cond] )
  cond_value4 = OptionConditionalValue( 1, subOptionValues, [cond] )
  
  opt_value.appendValue( cond_value )
  opt_value.appendValue( cond_value2 )
  opt_value.appendValue( cond_value3 )
  opt_value.appendValue( cond_value4 )
  
  print("Value: %s" % (opt_value.value( {} ) ))

#//===========================================================================//

if __name__ == "__main__":
  runTests()
