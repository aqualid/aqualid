import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_option_types import OptionType, BoolOptionType, EnumOptionType, RangeOptionType, ListOptionType
from aql_option_value import OptionValue, ConditionalValue, Condition, AddValue, SubValue, CallValue

from aql_errors import EnumOptionValueIsAlreadySet, EnumOptionAliasIsAlreadySet, InvalidOptionValue

#//===========================================================================//

def   _condition( options, context, flag, opt_value ):
  #~ print("context[opt_value]: %s" % (context[opt_value], ))
  return flag

@testcase
def test_option_value(self):
  event_manager.setHandlers( EventHandler() )
  
  opt_type1 = RangeOptionType( min_value = 0, max_value = 5, fix_value = True )
  
  opt_value = OptionValue( opt_type1 )
  
  cond = Condition( _condition, flag = True, opt_value = opt_value )
  cond_value  = ConditionalValue( CallValue( opt_type1, AddValue( 2 ) ), cond )
  cond_value2 = ConditionalValue( CallValue( opt_type1, AddValue( 3 ) ), cond )
  cond_value3 = ConditionalValue( CallValue( opt_type1, AddValue( 3 ) ), cond )
  
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
  
  print("Value: %s" % (opt_value.value( {} ) ))

#//===========================================================================//

if __name__ == "__main__":
  runTests()
