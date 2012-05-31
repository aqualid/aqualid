import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_option_types import OptionType, BoolOptionType, EnumOptionType, RangeOptionType, ListOptionType
from aql_option_value import OptionValue, ConditionalValue, Condition, AddValue, SubValue, CallValue
from aql_options import Options

from aql_errors import EnumOptionValueIsAlreadySet, EnumOptionAliasIsAlreadySet, InvalidOptionValue

#//===========================================================================//

class TestOptions( AqlTestCase ):
  
  @staticmethod
  def   setUpClass():
    event_manager.setHandlers( EventHandler() )
  
  def test_options(self):
    options = Options()
    
    opt_type1 = RangeOptionType( min_value = 0, max_value = 5, fix_value = True )
    
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
  
  def test_options_conditions(self):
    options = Options()
    
    opt_type1 = RangeOptionType( min_value = 0, max_value = 5, fix_value = True )
    
    options.warn_level = opt_type1
    options.warning_level = options.warn_level
    
    opt_type2 = EnumOptionType( 'debug', 'release', 'final' )
    
    options.optimization = opt_type2
    options.opt = options.optimization
    
    options.warning_level = 0
    options.optimization = 'release'
    
    options.If().optimization.eq('debug').warning_level += 1
    
    self.assertEqual( options.warn_level, 0 )
    
    options.optimization = 'debug'
    
    self.assertEqual( options.warn_level, 1 )
    
    
    
    


#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
