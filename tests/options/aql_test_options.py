import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.types import UpperCaseString, FilePath

from aql.options import OptionType, BoolOptionType, EnumOptionType, RangeOptionType, ListOptionType, DictOptionType, PathOptionType, \
                        builtinOptions, \
                        OptionValue, ConditionalValue, Condition, Options, AddValue, SubValue, \
                        ErrorOptionsOperationIsNotSpecified, ErrorOptionsForeignOptionValue, \
                        ErrorOptionsNewValueTypeIsNotOption, ErrorOptionsOptionValueExists, ErrorOptionsMergeNonOptions


#//===========================================================================//

class TestOptions( AqlTestCase ):
  
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
    self.assertEqual( over_opts.debug_on, 'true' )
    options.debug_on = False
    self.assertEqual( over_opts.debug_on, 'false' )
    options.debug_on = True
    self.assertEqual( over_opts.debug_on, 'true' )
    
    over_opts.debug_on = False
    
    self.assertEqual( options.debug_on, 'true' )
    self.assertEqual( over_opts.debug_on, 'false' )
    self.assertEqual( over_opts.warn_level, 0 )
    
    options.warning_level = 3
    self.assertEqual( over_opts.warn_level, 3 )
    self.assertEqual( over_opts.warning_level, 3 )
    over_opts.warn_level.set( 1 )
    self.assertEqual( options.warning_level, 3 )
    self.assertEqual( options.warn_level, 3 )
    self.assertEqual( over_opts.warning_level, 1 )
    self.assertEqual( over_opts.warn_level, 1 )
    
    over_opts = over_opts.copy()
    options.warning_level = 2
    self.assertEqual( options.warn_level, 2 )
    self.assertEqual( over_opts.warn_level, 1 )
    self.assertEqual( over_opts.warning_level, 1 )
    
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
    
    options.warn_level.set( 2 )
    self.assertEqual( options.warn_level, 2 )
    self.assertNotEqual( options.warn_level, 1 )
    self.assertLess( options.warn_level, 3 )
    self.assertLessEqual( options.warn_level, 3 )
    self.assertLessEqual( options.warn_level, 2 )
    self.assertGreater( options.warn_level, 1 )
    self.assertGreaterEqual( options.warn_level, 1 )
    self.assertGreaterEqual( options.warn_level, 2 )
    
    options.warn_levels = ListOptionType( value_type = options.warn_level.optionType() )
    
    options.warn_levels += [1,2,3]
    
    self.assertIn( 1, options.warn_levels )
    self.assertNotIn( 5, options.warn_levels )
  
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
  
  #//-------------------------------------------------------//
  
  def test_options_conditions3(self):
    options = Options()
    
    options.warn_levels = ListOptionType( value_type = RangeOptionType( min_value = 0, max_value = 5 ) )
    options.opt = RangeOptionType( min_value = 1, max_value = 100 )
    
    options.If().warn_levels.hasAny([2,5]).opt += 10
    options.If().warn_levels.hasAll([1,4,3]).opt += 20
    
    self.assertEqual( options.opt, 1 )
    
    options.warn_levels = [3,1,4]
    self.assertEqual( options.warn_levels, [3,1,4] )
    
    self.assertEqual( options.opt, 21 )
    
    options.warn_levels = [0,4,5]
    self.assertEqual( options.warn_levels, [0,4,5] )
    self.assertEqual( options.opt, 11 )
    
    options.warn_levels = [1,3,2,4]
    self.assertEqual( options.warn_levels, [1,3,2,4] )
    self.assertEqual( options.opt, 31 )
    
    options.If().opt.oneOf([1,11,21,31]).opt -= 1
    options.If().opt.oneOf([1,11,21,31]).opt -= 1
    
    self.assertEqual( options.opt, 30 )
    
  
  #//-------------------------------------------------------//
  
  def test_options_conditions4(self):
    options = Options()
    
    options.opt = RangeOptionType( min_value = 1, max_value = 100 )
    options.warn_level = RangeOptionType( min_value = 0, max_value = 5 )
    
    options.opt = 1
    options.If().warn_level.eq(3).opt += 10
    options.If().warn_level.ge(3).opt += 10
    
    options.warn_level = 3
    
    options.If().opt.oneOf([1,11,21,31]).opt -= 1
    options.If().opt.oneOf([1,11,21,31]).opt -= 1
    
    self.assertEqual( options.opt, 20 )
    
    options.If().warn_level.ne(3).opt -= 1
    self.assertEqual( options.opt, 20 )
    options.If().warn_level.ne(2).opt += 1
    self.assertEqual( options.opt, 21 )
    
    options.If().warn_level.gt(3).opt += 1
    self.assertEqual( options.opt, 21 )
    options.If().warn_level.gt(2).opt += 4
    self.assertEqual( options.opt, 25 )
    
    options.If().warn_level.lt(3).opt += 1
    self.assertEqual( options.opt, 25 )
    options.If().warn_level.lt(4).opt += 5
    self.assertEqual( options.opt, 30 )
    
    options.If().warn_level.le(2).opt += 1
    self.assertEqual( options.opt.value(), 30 )
    options.If().warn_level.le(4).opt += 5
    self.assertEqual( options.opt, 35 )
    
    tc = options.If().warn_level.le(4)
    tc.opt += 5
    self.assertEqual( options.opt, 40 )
    tc.opt += 5
    self.assertEqual( options.opt, 45 )
    
    to = tc.opt
    to += 5
    
    self.assertEqual( options.opt.value(), 50 )
  
  #//-------------------------------------------------------//
  
  def   test_options_refs(self):
    options = Options()
    
    options.opt = RangeOptionType( min_value = 1, max_value = 100 )
    options.warn_level = RangeOptionType( min_value = 0, max_value = 5 )
    
    options.warn_level = AddValue( options.opt )
    self.assertEqual( options.warn_level, 1 )
    
    options.If().warn_level.eq( options.opt ).warn_level += 1
    self.assertEqual( options.warn_level, 2 )
    
    options.opt = 2
    
    self.assertEqual( options.warn_level, 3 )
    
    options2 = Options()
    options2.opt = RangeOptionType( min_value = 1, max_value = 100 )
    self.assertRaises( ErrorOptionsForeignOptionValue, options.warn_level.set, options2.opt )
    
    options.warn_level.set( options.opt )
    self.assertEqual( options.warn_level, 2 )
    
    self.assertRaises( ErrorOptionsOperationIsNotSpecified, options.appendValue, 'warn_level', 1 )
    self.assertRaises( ErrorOptionsNewValueTypeIsNotOption, options.__setattr__, 'test', 1 )
    
    options.opt += options.opt
    
    self.assertEqual( options.opt, 4 )
    
  #//-------------------------------------------------------//
  
  def   test_options_errors(self):
    options = Options()
    options2 = Options()
    
    options.opt = RangeOptionType( min_value = 1, max_value = 100 )
    options.warn_level = RangeOptionType( min_value = 0, max_value = 5 )
    
    self.assertRaises( ErrorOptionsOptionValueExists, options.__setattr__, 'opt', options.opt.option_value.optionType() )
    self.assertRaises( ErrorOptionsForeignOptionValue, options2.__setattr__, 'opt', options.opt )
    self.assertRaises( AttributeError, options.__getattr__, 'debug_on' )
    
    options.opt = options.warn_level
    options.warn_level = 2
    self.assertEqual( options.opt, options.warn_level )
    self.assertEqual( options.opt, 2 )
    self.assertIn( 'opt', options )
    self.assertNotIn( 'debug_on', options )
    self.assertEqual( sorted(options), sorted(['opt','warn_level']) )
    
  #//-------------------------------------------------------//
  
  def   test_options_update(self):
    options = Options()
    
    options.opt = RangeOptionType( min_value = 1, max_value = 100 )
    options.warn_level = RangeOptionType( min_value = 0, max_value = 5 )
    
    args = {'opt':5, 'warn_level':3, 'debug_on': True }
    options.update( args )
    self.assertEqual( options.opt, args['opt'] )
    self.assertEqual( options.warn_level, args['warn_level'] )
    self.assertNotIn( 'debug_on', options )
    
    options.update( {} )
    options.update( options )
    self.assertRaises( ErrorOptionsMergeNonOptions, options.merge, args )
    
    options2 = Options()
    options2.debug_on = BoolOptionType()
    options2.debug_on = False
    options2.bv = ListOptionType( value_type = str )
    options2.bv += 'debug,release,final'
    options2.build_variant = options2.bv
    options.merge( options2 )
    self.assertEqual( options.debug_on, options2.debug_on )
    self.assertEqual( options.bv, options2.bv )
    self.assertEqual( options.bv, options2.build_variant )
    self.assertEqual( options2.bv, options2.build_variant )
    self.assertIs( options.bv.option_value, options.build_variant.option_value )
    
    options.merge( options2 )
    self.assertEqual( options.debug_on, options2.debug_on )
    self.assertEqual( options2.bv, options2.build_variant )

  #//-------------------------------------------------------//
  
  def   test_builtin_options(self):
    options = builtinOptions()
    self.assertEqual( options.build_variant, 'debug' )
    self.assertEqual( options.optimization, 'off' )
    
    options.build_variant = 'release'
    self.assertEqual( options.optimization, 'speed' )
    
    options.build_variant = 'release_size'
    self.assertEqual( options.optimization, 'size' )
    
    options.build_variant = 'final'
    self.assertEqual( options.optimization, 'speed' )
    
    self.assertEqual( options.build_variant.optionType().group, "Build output" )
    
    self.assertTrue( options.do_build_path_merge )
    
    options.build_dir_suffix = 'syslib'
    
    self.assertFalse( options.do_build_path_merge )
    
    options.build_dir_suffix = None
    
    self.assertTrue( options.do_build_path_merge )
  
  #//-------------------------------------------------------//
  
  def test_options_dict(self):
    options = Options()
    
    options.cxx = PathOptionType()
    options.debug_on = BoolOptionType()
    
    options.defines = DictOptionType( key_type = str, value_type = str )
    options.env = DictOptionType( key_type = UpperCaseString )
    options.env['PATH'] = ListOptionType( value_type = FilePath, separators = os.pathsep )()
    options.env['HOME'] = FilePath()
    options.env['Path'] = '/work/bin'
    options.env['Path'] += '/usr/bin'
    options.env['path'] += ['/usr/local/bin', '/home/user/bin']
    options.env['Home'] = '/home/user'
    options.env['path'] += options.env['Home']
    options.env['path'] += options.cxx
    options.cxx = '/mingw/bin/g++'
    options.If().debug_on.eq(False).defines['DEBUG'] = 'FALSE'
    options.If().debug_on.eq(True).defines['DEBUG'] = 'TRUE'
    options.defines['OPTS'] = ''
    options.If().defines['DEBUG'].eq('TRUE').defines['OPTS'] += options.defines['DEBUG']
    
    path = list(map(FilePath, ['/work/bin', '/usr/bin', '/usr/local/bin', '/home/user/bin', '/home/user', '/mingw/bin/g++' ] ))
    
    value = options.env.value()
    self.assertEqual( value['path'], path )
    
    self.assertEqual( options.defines['OPTS'], '' )
    options.debug_on = True
    self.assertEqual( options.defines['OPTS'], 'TRUE' )
  
  #//=======================================================//
  
  def   test_options_merge(self):
    options = Options()
    options.opt1 = RangeOptionType( min_value = 1, max_value = 100 )
    options.opt2 = RangeOptionType( min_value = 0, max_value = 5 )
    options.opt3 = RangeOptionType( min_value = -10, max_value = 10 )
    options.option1 = options.opt1
    options.option3 = options.opt3
    
    options.opt1.setDefault( 50 )
    options.opt2.setDefault( 3 )
    options.opt3.setDefault( 0 )
    
    options2 = Options()
    options2.opt21 = RangeOptionType( min_value = 1, max_value = 100 )
    options2.opt22 = RangeOptionType( min_value = 0, max_value = 5 )
    options2.opt23 = RangeOptionType( min_value = -10, max_value = 10 )
    options2.option22 = options2.opt22
    options2.option23 = options2.opt23
    
    options.merge( options2 )
    self.assertEqual( options.opt1, 50 )
    self.assertEqual( options.opt2, 3 )
    self.assertEqual( options.opt3, 0 )
    self.assertIs( options.option1.option_value, options.opt1.option_value )
    self.assertIs( options.option3.option_value, options.opt3.option_value )
    self.assertEqual( options.opt21, options2.opt21 )
    self.assertEqual( options.opt23, options2.opt23 )
    self.assertEqual( options.opt22, options2.opt22 )
    self.assertIs( options.option22.option_value, options.opt22.option_value )
    self.assertIs( options.option23.option_value, options.opt23.option_value )
    
    child_options2 = options2.override()
    
    child_options2.option21 = child_options2.opt21
    child_options2.opt22 = 3
    child_options2.opt23 = 7
    
    child_options2.join()
    self.assertIs( options2.option21.option_value, options2.opt21.option_value )
    self.assertEqual( options2.opt22, 3 )
    self.assertEqual( options2.opt23, 7 )
    self.assertFalse( child_options2 )
    
    child_options2 = options2.override()
    
    options2.option_21 = options2.opt21
    
    child_options2.opt22 = 4
    child_options2.opt23 = 8
    
    child_options2.unjoin()
    
    self.assertIs( child_options2.option21.option_value, child_options2.option_21.option_value )
    self.assertIs( child_options2.option21.option_value, child_options2.opt21.option_value )
    self.assertIsNot( child_options2.opt21.option_value, options2.opt21.option_value )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
