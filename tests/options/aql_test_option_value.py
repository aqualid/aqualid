import copy
import sys
import os.path
import timeit
import operator

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.options import OptionType, BoolOptionType, EnumOptionType, RangeOptionType, ListOptionType, \
                        OptionValue, ConditionalValue, Condition, Operation, SimpleOperation, \
                        ErrorOptionTypeUnableConvertValue

from aql.types import Dict

#//===========================================================================//

def   _setOperator( dest_value, value ):
  return value

def   _doAction( options, context, dest_value, op, value ):
  if isinstance( value, OptionValue ):
    value = value.value( options, context )
  return op( dest_value, value )

def   SetValue( value, operation = None ):
  return Operation( operation, _doAction, _setOperator, value )

def   AddValue( value, operation = None ):
  return Operation( operation, _doAction, operator.iadd, value )

def   SubValue( value, operation = None ):
  return Operation( operation, _doAction, operator.isub, value )

#//===========================================================================//

def   _condition( options, context, flag, opt_value = None ):
  return flag

class TestOptionValue( AqlTestCase ):
  
  #//---------------------------------------------------------------------------//
  
  def test_option_value(self):
    opt_type1 = RangeOptionType( min_value = 0, max_value = 5 )
    
    opt_value = OptionValue( opt_type1 )
    
    cond = Condition( None, _condition, flag = True, opt_value = opt_value )
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
    
    cond_true = Condition( None, _condition, flag = True )
    cond_false = Condition( cond_true,  _condition, flag = False )
    cond_false = Condition( cond_false, _condition, flag = True )
    
    opt_value.appendValue( ConditionalValue( AddValue( 2 ), cond_false ) )
    self.assertEqual( opt_value.value( {} ), 0 )
    
    opt_value.appendValue( ConditionalValue( AddValue( 3 ), cond_true ) )
    self.assertEqual( opt_value.value( {} ), 3 )
    
    opt_value.appendValue( ConditionalValue( AddValue( 1 ), cond_true ) )
    self.assertEqual( opt_value.value( {} ), 4 )
    
    opt_value.appendValue( ConditionalValue( AddValue( 1 ), cond_false ) )
    self.assertEqual( opt_value.value( {} ), 4 )
    
    opt_value2 = OptionValue( OptionType( int ) )
    
    opt_value.appendValue( ConditionalValue( SetValue( opt_value2 ), cond_true ) )
    
    opt_value2.appendValue( ConditionalValue( SetValue( 7 ), cond_true ) )
    
    self.assertEqual( opt_value.value( None ), 7 )
    self.assertEqual( opt_value2.value( None ), 7 )
    
    opt_value2.appendValue( ConditionalValue( SetValue( 8 ), cond_true ) )
    
    self.assertEqual( opt_value.value( None ), 8 )
    self.assertEqual( opt_value2.value( None ), 8 )
    
    opt_value.appendValue( ConditionalValue( SubValue( 1, AddValue( 1 ) ), cond_true ) )
    
    self.assertEqual( opt_value.value( None ), 8 )
    
    tmp_opt_value = opt_value.copy()
    
    self.assertEqual( tmp_opt_value.value( None ), 8 )
    
    tmp_opt_value.appendValue( ConditionalValue( Operation( AddValue( 2 ), None ), cond_true ) )
    
    self.assertEqual( tmp_opt_value.value( None ), 10 )
  
  #//---------------------------------------------------------------------------//
  
  def test_option_value3(self):
    opt_value = OptionValue( OptionType( int ) )
    
    opt_value.appendValue( ConditionalValue( SetValue( 1 ) ) )
    self.assertEqual( opt_value.value( None ), 1 )
    opt_value.appendValue( ConditionalValue( SetValue( 0 ) ) )
    self.assertEqual( opt_value.value( None ), 0 )
    
    opt_value_list = OptionValue( ListOptionType( value_type = int ) )
    opt_value_list.appendValue( ConditionalValue( SetValue( 1 ) ) )
    self.assertEqual( opt_value_list.value( None ), 1 )
    
    opt_value_list.appendValue( ConditionalValue( AddValue( 0 ) ) )
    self.assertEqual( opt_value_list.value( None ), "1, 0" )
  
  #//---------------------------------------------------------------------------//
  
  def test_option_value4(self):
    opt_value = OptionValue( OptionType( int ) )
    
    def   _modValue( value ):
      return value + 1
    
    opt_value = OptionValue( OptionType( int ) )
    opt_value.appendValue( ConditionalValue( SetValue( 2 ) ) )
    opt_value.appendValue( ConditionalValue( SimpleOperation( _modValue ) ) )
    
    self.assertEqual( opt_value.value( None ), 3 )
  
  #//---------------------------------------------------------------------------//
  
  def test_option_value_enum(self):
    value_type = EnumOptionType( values = ( ('off', 0), ('size', 1), ('speed', 2) ) )
    
    opt_value = OptionValue( value_type )
    
    opt_value.appendValue( ConditionalValue( SetValue( 'size' ) ) )
    self.assertEqual( opt_value.value( {} ), 1 )
    
    opt_value.appendValue( ConditionalValue( SetValue( 'ultra' ) ) )
    self.assertRaises( ErrorOptionTypeUnableConvertValue, opt_value.value, {} )
  
  #//---------------------------------------------------------------------------//
  
  def test_option_value_cyclic(self):
    opt_value1 = OptionValue( OptionType( value_type = int ) )
    opt_value2 = OptionValue( RangeOptionType( min_value = 0, max_value = 5 ) )
    
    opt_value1.appendValue( ConditionalValue( SetValue( 1 ) ) )
    self.assertEqual( opt_value1.value( None ), 1 )
    
    opt_value2.appendValue( ConditionalValue( SetValue( 2 ) ) )
    self.assertEqual( opt_value2.value( None ), 2 )
    
    opt_value1.appendValue( ConditionalValue( AddValue( opt_value2 ) ) )
    self.assertEqual( opt_value1.value( None ), 3 )
    
    opt_value2.appendValue( ConditionalValue( AddValue( opt_value1 ) ) )
    
    self.assertEqual( opt_value2.value( None ), 5 )
    
    opt_value1.appendValue( ConditionalValue( AddValue( opt_value2 ) ) )
    
    self.assertEqual( opt_value2.value( None ), 7 )
    self.assertEqual( opt_value1.value( None ), 7 )
    
    # opt1: 1 + opt2 + opt2 = 1 + 3 + 3
    # opt2: 2 + opt1 = 2 + 1 + 2 + 2
    
  
  #//---------------------------------------------------------------------------//
  
  def test_option_value_list(self):
    opt_type1 = ListOptionType( value_type = EnumOptionType( values = ( ('off', 0), ('size', 1), ('speed', 2) ) ) )
    
    opt_value = OptionValue( opt_type1 )
    
    cond = Condition( None, _condition, flag = True, opt_value = opt_value )
    cond2 = Condition( cond, _condition, flag = False, opt_value = opt_value )
    
    cond_value  = ConditionalValue( AddValue( 1 ), cond )
    cond_value2 = ConditionalValue( AddValue( 0 ), cond2 )
    cond_value3 = ConditionalValue( AddValue( 2 ), cond )
    cond_value4 = ConditionalValue( AddValue( 1 ), cond2 )
    
    opt_value.appendValue( cond_value )
    opt_value.appendValue( cond_value2 )
    opt_value.appendValue( cond_value3 )
    opt_value.appendValue( cond_value4 )
    
    self.assertEqual( opt_value.value( None ), [1,2] )
    
    opt_value.prependValue( cond_value3 )
    self.assertEqual( opt_value.value( None ), [2,1,2] )
    
    opt_value = copy.copy( opt_value )
    self.assertEqual( opt_value.value( None ), [2,1,2] )
    
    self.assertIs( opt_value.optionType(), opt_type1 )
  
  #//---------------------------------------------------------------------------//
  
  def test_option_value_dict(self):
    opt_type1 = OptionType( value_type = dict )
    
    opt_value = OptionValue( opt_type1 )
    
    cond_value  = ConditionalValue( SetValue( {1:2} ) )
    cond_value  = ConditionalValue( SetValue( {3:4} ) )
    
    opt_value.appendValue( cond_value )
    
    self.assertEqual( opt_value.value( {} ), {3:4} )
    
    opt_type1 = OptionType( value_type = Dict )


#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
