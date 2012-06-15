import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_option_types import OptionType, BoolOptionType, EnumOptionType, RangeOptionType, ListOptionType
from aql_option_value import OptionValue, ConditionalValue, Condition, AddValue, SubValue
from aql_options import Options

from aql_errors import EnumOptionValueIsAlreadySet, EnumOptionAliasIsAlreadySet, InvalidOptionValue

#//===========================================================================//

class TestOptions( AqlTestCase ):
  
  @classmethod
  def   setUpClass( cls ):
    super(TestOptions, cls).setUpClass()
    event_manager.setHandlers( EventHandler() )
  
  #//---------------------------------------------------------------------------//
  
  def test_options(self):
    options = Options()
    
    opt_type1 = RangeOptionType( min_value = 0, max_value = 5 )
    
    options.warn_level = opt_type1
    options.warning_level = options.warn_level
    
    self.assertEqual( options.warn_level, options.warning_level )
    
    options.warning_level = 1
    
    self.assertEqual( options.warn_level, options.warning_level )
    
    options.warning_level += 1
    
    self.assertEqual( options.warn_level, 2 )
    
    options.warning_level -= 2
    
    self.assertEqual( options.warn_level, 0 )
    
    opt_type2 = BoolOptionType()
    options.debug_on = opt_type2
    options.debug_on = True
    self.assertEqual( options.debug_on, 'true' )
    
    over_opts = options.override()
    over_opts.debug_on = False
    
    self.assertEqual( options.debug_on, 'true' )
    self.assertEqual( over_opts.debug_on, 'false' )
    self.assertEqual( over_opts.warn_level, 0 )
    
    options.warning_level = 3
    self.assertEqual( over_opts.warn_level, 3 )
    
    over_opts = over_opts.copy()
    options.warning_level = 2
    self.assertEqual( options.warn_level, 2 )
    self.assertEqual( over_opts.warn_level, 3 )
    self.assertEqual( over_opts.warning_level, 3 )
    
    over_opts.warn_level = 4
    self.assertEqual( over_opts.warn_level, 4 )
    self.assertEqual( over_opts.warning_level, 4 )
  
  #//-------------------------------------------------------//
  
  def test_options_2(self):
    options = Options()
    options2 = Options()
    
    options.warn_level = RangeOptionType( min_value = 0, max_value = 5 )
    options2.warn_level = RangeOptionType( min_value = 0, max_value = 5 )
    
    options.warn_level = 1
    options2.warn_level = 1
    
    self.assertEqual( options.warn_level, options2.warn_level )
    self.assertEqual( options.warn_level, options2.warn_level.option_value )
  
  #//-------------------------------------------------------//
  
  def test_options_conditions(self):
    options = Options()
    
    opt_type1 = RangeOptionType( min_value = 0, max_value = 5 )
    
    options.warn_level = opt_type1
    options.warning_level = options.warn_level
    
    opt_type2 = EnumOptionType( values = ('debug', 'release', 'final') )
    
    options.optimization = opt_type2
    options.opt = options.optimization
    
    options.warning_level = 0
    options.optimization = 'release'
    
    options.If().optimization.eq('debug').warning_level += 1
    
    self.assertEqual( options.warn_level, 0 )
    
    options.optimization = 'debug'
    
    self.assertEqual( options.warn_level, 1 )
    
    options.optimization = 'release'
    
    options.If().warning_level.ge(2).optimization = 'debug'
    options.If().optimization.eq('release').warning_level += 2
    
    print( options.optimization.value() )
    
    self.assertEqual( options.optimization, 'debug' )
    
    # wl: 0, opt == debug: +1, opt == release: +2
    # opt: release, debug, release, wl == 2: debug
    
  #//-------------------------------------------------------//
  
  def test_options_conditions2(self):
    options = Options()
    
    options.warning_level = RangeOptionType( min_value = 0, max_value = 5 )
    
    options.optimization = EnumOptionType( values = ('debug', 'release', 'final') )
    
    options.build_variants = ListOptionType( value_type = options.optimization.optionType() )
    
    options.If().build_variants.has('release').warning_level = 5
    
    self.assertEqual( options.warning_level, 0 )
    
    options.build_variants += 'release'
    
    self.assertEqual( options.warning_level, 5 )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
