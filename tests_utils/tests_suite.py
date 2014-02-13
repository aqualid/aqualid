#
# Copyright (c) 2011,2012 The developers of Aqualid project - http://aqualid.googlecode.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#


import imp
import sys
import os.path
import unittest

from tests_case import TestCaseSuite

__all__ = ('testsSuite', 'localTestsSuite', 'skip', 'runSuite', 'runTests', 'runLocalTests' )

#//===========================================================================//

try:
  unicode("test")
except NameError:
  unicode = str

def   _toSequence( value ):
  
  try:
    if not isinstance( value, (str, unicode) ):
      iter( value )
      return value
  except TypeError:
    pass
  
  if value is None:
    return tuple()
  
  return ( value, )

#//===========================================================================//

def   _isSubSequence( sub_seq, seq ):
  
  if not sub_seq:
    return True
  
  sub_seq_len = len(sub_seq)
  first_part = sub_seq[0]
  pos = 0
  while True:
    try:
      pos = seq.index( first_part, pos )
      if seq[pos : pos + sub_seq_len] == sub_seq:
        return True
      
      pos += 1
      
    except ValueError:
      return False

#//===========================================================================//

def  _findTestModuleFiles( path, test_modules_prefix ):
  
  test_case_modules = []
  
  for root, dirs, files in os.walk( path ):
    for file_name in files:
      file_name = file_name.lower()
      if file_name.startswith( test_modules_prefix ) and file_name.endswith('.py'):
        test_case_modules.append( os.path.join(root, file_name))
    dirs[:] = filter( lambda d: not d.startswith('.') or d.startswith('__'), dirs )
  
  return test_case_modules

#//===========================================================================//

def   _loadTestModule( module_file, verbose ):
  
  module_dir = os.path.normpath( os.path.dirname( module_file ) )
  module_name = os.path.splitext( os.path.basename( module_file ) )[0]
  
  fp, pathname, description = imp.find_module( module_name, [ module_dir ] )
  
  with fp:
    if verbose:
      print( "Loading test module: %s" % module_file )
    
    m = imp.load_module( module_name, fp, pathname, description )
    sys_path = sys.path
    try:
      sys_path.remove( module_dir )
    except ValueError:
      pass
    sys_path.insert( 0, module_dir )
    return m

#//===========================================================================//

def   _loadTestModules( path, test_modules_prefix, verbose ):
  
  test_modules = []
  module_files = []
  
  for path in _toSequence( path ):
    if os.path.isdir( path ):
      module_files += _findTestModuleFiles( path, test_modules_prefix )
    else:
      module_files.append( path )
  
  for module_file in module_files:
    test_modules.append( _loadTestModule( module_file, verbose ) )
  
  return test_modules

#//===========================================================================//

def   _getModuleTestCaseClasses( module_globals ):
  
  test_case_classes = []
  
  for value in module_globals.values():
    if isinstance(value, type) and issubclass(value, unittest.TestCase):
      test_case_classes.append( value )
  
  return test_case_classes

#//===========================================================================//

def   _getTestCaseClasses( test_modules ):
  test_case_classes = []
  for test_module in test_modules:
    test_case_classes += _getModuleTestCaseClasses( test_module.__dict__ )
  
  return test_case_classes

#//===========================================================================//

def   _loadTestCaseClasses( path, test_modules_prefix, verbose ):
  return _getTestCaseClasses( _loadTestModules( path, test_modules_prefix, verbose ) )

#//===========================================================================//

class Tests(dict):
  
  class SortedClassesAndMethods( list ): pass
  
  @staticmethod
  def   __getTestMethods( test_class, test_methods_prefix ):
    
    test_methods = set()
    
    for name, instance in test_class.__dict__.items():
      if hasattr(instance, '__call__') and name.startswith( test_methods_prefix ):
        test_methods.add( instance )
    
    return test_methods
  
  #//-------------------------------------------------------//
  
  def   __init__( self, test_classes = None, test_methods_prefix = 'test' ):
    
    if isinstance(test_classes, Tests.SortedClassesAndMethods ):
      for test_class, methods in test_classes:
        module_name, cls_name = test_class.__module__, test_class.__name__
        
        for method in methods:
          test_name = ( module_name, cls_name, method.__name__ )
          self[ method ] = ( test_name, test_class )
    
    else:
      for test_class in _toSequence( test_classes ):
        
        module_name, cls_name = test_class.__module__, test_class.__name__
        
        for method in self.__getTestMethods( test_class, test_methods_prefix ):
          test_name = ( module_name, cls_name, method.__name__ )
          self[ method ] = ( test_name, test_class )
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __normalizeNames( names ):
    
    norm_names = set()
    
    for name in _toSequence( names ):
      if isinstance( name, (str, unicode) ):
        name = tuple( name.split('.')[-3:] )
      else:
        name = tuple( _toSequence( name ) )
      
      norm_names.add( name )
    
    return norm_names
  
  #//-------------------------------------------------------//
  
  def   getTestsByMethodNames( self, method_names ):
    
    names = self.__normalizeNames( method_names )
    
    tests = Tests()
    
    for method, test_info in self.items():
      test_name, test_class = test_info
      
      for name in names:
        method_name = test_name[ len(test_name) - len(name) : ]
        if method_name == name:
          tests[ method ] = test_info
    
    return tests
  
  #//-------------------------------------------------------//
  
  def   getTestsByClassNames( self, class_names ):
    
    names = self.__normalizeNames( class_names )
    
    tests = Tests()
    
    for method, test_info in self.items():
      test_name, test_class = test_info
      
      test_name = test_name[:2]   # remove method name, only class name matters
      
      for name in names:
        offset = len(test_name) - len(name)
        
        if offset >= 0:
          if test_name[ offset: ] == name:
            tests[ method ] = test_info
    
    return tests
  
  #//-------------------------------------------------------//
  
  def   getTestsByNames( self, names ):
    names = self.__normalizeNames( names )
    
    tests = Tests()
    
    for method, test_info in self.items():
      test_name, test_class = test_info
      
      for name in names:
        if _isSubSequence( name, test_name ):
          tests[ method ] = test_info
    
    return tests
  
  #//-------------------------------------------------------//
  
  def getTestsByMethods( self, methods ):
    tests = Tests()
    
    for method in methods:
      try:
        tests[ method ] = self[ method ]
      except KeyError:
        pass
    
    return tests
  
  #//-------------------------------------------------------//
  
  def getTestsByClasses( self, test_classes ):
    tests = Tests()
    
    for method, test_info in self.items():
      test_name, test_class = test_info
      
      if test_class in test_classes:
        tests[ method ] = test_info
    
    return tests
  
  #//-------------------------------------------------------//
  
  def   __isub__(self, other):
    for method in other:
      try:
        del self[ method ]
      except KeyError:
        pass
    
    return self
  
  #//-------------------------------------------------------//
  
  def   __iadd__( self, other ):
    self.update( other )
    
    return self
  
  #//-------------------------------------------------------//
  
  def   copy( self ):
    other = Tests()
    other.update( self )
    
    return other
  
  #//-------------------------------------------------------//
  
  def   sorted( self ):
    modules = {}
    
    for method, test_info in self.items():
      test_name, test_class = test_info
      module_name = test_name[0]
      
      modules.setdefault( module_name, {} ).setdefault( test_class, set() ).add( method )
    
    sorted_tests = Tests.SortedClassesAndMethods()
    
    for module_name in sorted( modules ):
      test_classes = modules[ module_name ]
      for test_class in sorted( test_classes, key = lambda test_class: test_class.__name__ ):
        methods = test_classes[ test_class ]
        sorted_methods = sorted( methods, key = lambda method: method.__name__)
        
        sorted_tests.append( [ test_class, sorted_methods ] )
    
    return sorted_tests
  
  #//-------------------------------------------------------//
  
  def   sortedFrom( self, start_from ):
    
    tests = Tests.SortedClassesAndMethods()
    sorted_tests = self.sorted()
    
    start_names = self.__normalizeNames( start_from )
    
    index = 0
    for test_class, methods in sorted_tests:
      module_name     = test_class.__module__
      test_class_name = test_class.__name__
      
      method_index = 0
      for method in methods:
        test_name = ( module_name, test_class_name, method.__name__ )
        for name in start_names:
          if _isSubSequence( name, test_name ):
            tests += [ [ test_class, methods[method_index:] ] ]
            tests += sorted_tests[ index + 1 : ]
            return tests
          
        method_index += 1
      index += 1
    
    return tests
  
  #//-------------------------------------------------------//
  
  def   list( self, verbose ):
    """Method collects and returns all test names."""
    
    if verbose:
      formatter = lambda m: m.__name__ if not m.__doc__ else m.__doc__ + '[' + m.__name__ + ']'
    else:
      formatter = lambda m: m.__name__
      
    test_names = []
    for test_class, methods in self.sorted():
      method_names = map( formatter, methods )
      test_names.append( ( "%s.%s" % (test_class.__module__ , test_class.__name__), method_names) )

    
    return test_names
  
#//===========================================================================//

class TestsSuiteMaker(object):
  
  __slots__  = (
    'skip_test_methods',
    'skip_test_classes',
  )
  
  #//-------------------------------------------------------//
  def   __init__( self ):
    self.skip_test_methods = set()
    self.skip_test_classes = set()
  
  #//-------------------------------------------------------//
  
  def   loadLocals( self, test_methods_prefix = 'test' ):
    test_classes = _getModuleTestCaseClasses( __import__('__main__').__dict__ )
    
    return Tests( test_classes )
  
  #//-------------------------------------------------------//
  
  def   load( self, path = None, test_modules_prefix = 'test', test_methods_prefix = 'test', verbose = False ):
    test_classes = _loadTestCaseClasses( path, test_modules_prefix, verbose )
    
    return Tests( test_classes )
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __updateSkippedTests( all_tests, exec_test_names, skip_test_methods, skip_test_classes ):
    method_tests = all_tests.getTestsByMethodNames( exec_test_names )
    class_tests = all_tests.getTestsByClassNames( exec_test_names )
    
    skip_test_methods -= method_tests
    skip_test_classes -= method_tests
    skip_test_classes -= class_tests
  
  #//-------------------------------------------------------//
  
  def   tests( self, all_tests, run_tests = None, add_tests = None, skip_tests = None, start_from_test = None ):
    """Method defines tests which should be run, should be skiped, from which tests testing will be started and
    additionals tests.

    Arguments:
    all_tests       - start set of tests
    run_tests       - base tests which should be run, default value is None
    skip_tests      - tests should be skipped, default value is None
    start_from_test - name of test from sequence of tests will be started, default value is None
    """
    
    skip_test_methods = all_tests.getTestsByMethods( self.skip_test_methods )
    skip_test_classes = all_tests.getTestsByClasses( self.skip_test_classes )
    
    self.__updateSkippedTests( all_tests, run_tests,        skip_test_methods, skip_test_classes )
    self.__updateSkippedTests( all_tests, add_tests,        skip_test_methods, skip_test_classes )
    self.__updateSkippedTests( all_tests, start_from_test,  skip_test_methods, skip_test_classes )
    
    if run_tests is None:
      tests  = all_tests.copy()
    else:
      tests = all_tests.getTestsByNames( run_tests )
    
    tests += all_tests.getTestsByNames( add_tests )
    
    if start_from_test:
      tests += all_tests.getTestsByNames( start_from_test )
      tests = Tests( tests.sortedFrom( start_from_test ) )
    
    tests -= skip_test_methods
    tests -= skip_test_classes
    tests -= tests.getTestsByNames( skip_tests )
    
    return tests
  
  #//-------------------------------------------------------//
  
  def   suite( self, tests, suite_class = TestCaseSuite, options = None ):
    """Method makes test suite from tests.

    tests       - tests which should be added in test suite
    suite_class - test suite class
    options     - specify options for tests, default value is None

    """
    
    from tests_case import TestCaseBase
    
    main_suite = suite_class()

    keep_going = False
    if options is not None:
      keep_going = options.keep_going
      main_suite.xunit_output_dir = options.xunit_output_dir
    
    for test_class, methods in tests.sorted():
      test_class.options = options
      suite = suite_class( keep_going = keep_going )
      
      for method in methods:
        if issubclass( test_class, TestCaseBase ):
          test_case = test_class( method.__name__, keep_going = keep_going )
        else:
          test_case = test_class( method.__name__ )
        
        suite.addTest( test_case )
      
      main_suite.addTest( suite )
    
    return main_suite

#//===========================================================================//

_suite_maker = TestsSuiteMaker()

def  skip( test_case ):
  global _suite_maker
  
  if isinstance( test_case, type) and issubclass( test_case, unittest.TestCase ):
    _suite_maker.skip_test_classes.add( test_case )
  
  elif hasattr(test_case, '__call__'):
    _suite_maker.skip_test_methods.add( test_case )
  
  return test_case

#//===========================================================================//

def   _printTestsAndExit( tests, verbose ):
  """Method prints all tests names and tests methods.

  Aruments:
  tests - test names which are processed in method
  """

  print("\n  Tests:\n==================")
  for test_name, methods in tests.list( verbose ):
    print( test_name + ":\n\t\t" + "\n\t\t".join( methods ) + '\n')
  exit()

#//===========================================================================//

def   _printOptionsAndExit( options ):
  print("\n  Options:\n==================")
  for name, value in options.dump():
    if isinstance(value, (set, frozenset, tuple)):
      value = list(value)
    
    print( '    {name:<25}:  {value}'.format(name = name, value = value) )
  exit()

#//===========================================================================//

def   testsSuite( path = None, test_modules_prefix = 'test_', test_methods_prefix = 'test',
             run_tests = None, add_tests = None, skip_tests = None, start_from_test = None, suite_class = TestCaseSuite, list_tests = False, options = None ):
  
  global _suite_maker
  
  verbose = False if options is None else options.verbose
  
  all_tests = _suite_maker.load( path, test_modules_prefix, test_methods_prefix, verbose )
  tests = _suite_maker.tests( all_tests, run_tests, add_tests, skip_tests, start_from_test )
  
  if list_tests:
    _printTestsAndExit(tests, verbose )

  TestsNum().setNum(len(tests))
  
  return _suite_maker.suite( tests, suite_class, options )

#//===========================================================================//

def   localTestsSuite( test_methods_prefix = 'test',
                  run_tests = None, add_tests = None, skip_tests = None, start_from_test = None, suite_class = TestCaseSuite, list_tests = False, options = None ):
  
  global _suite_maker
  
  all_tests =_suite_maker.loadLocals( test_methods_prefix )
  tests = _suite_maker.tests( all_tests, run_tests, add_tests, skip_tests, start_from_test )
  
  if list_tests:
    verbose = False if options is None else options.verbose
    _printTestsAndExit( tests, verbose )
  
  return _suite_maker.suite( tests, suite_class, options )

#//===========================================================================//

def   runSuite( suite ):
  """Run test suite.
  
  Arguments:
  suite - suite which should be run 

  """

  try:
    test_runner = None
    
    if hasattr(suite, "xunit_output_dir" ) and suite.xunit_output_dir != None:
      from .. import xmlrunner
      test_runner = xmlrunner.XMLTestRunner( output = suite.xunit_output_dir, verbosity=2, descriptions=True )
    else:
      test_runner = unittest.TextTestRunner()

    result = test_runner.run( suite )
    if not result.wasSuccessful():
      exit(1)
    
  except KeyboardInterrupt:
    print("\nInterrupted by user")
  
  except URLError:
    print("\nConnection refused")
    
  finally:
    print(TestsStatistic())

#//===========================================================================//

def   runTests( suite_class = TestCaseSuite, options = None ):
  if options is None:
    from tests_options import TestsOptions
    options = TestsOptions()
  
  suite = testsSuite( options.tests_dirs, options.test_modules_prefix, options.test_methods_prefix,
                      options.run_tests, options.add_tests, options.skip_tests, options.start_from_tests, suite_class, options.list_tests, options )
  
  if options.list_options:
    _printOptionsAndExit( options )
  
  runSuite( suite )

#//===========================================================================//

def   runLocalTests( suite_class = TestCaseSuite, options = None ):
  if options is None:
    from tests_options import TestsOptions
    options = TestsOptions()
  
  suite = localTestsSuite( options.test_methods_prefix,
                           options.run_tests, options.add_tests, options.skip_tests, options.start_from_tests, suite_class, options.list_tests, options )
  
  if options.list_options:
    _printOptionsAndExit( options )
  
  runSuite( suite )

#//===========================================================================//

if __name__ == "__main__":
  
  from tests_case import TestCaseBase
  
  #@skip
  class Foo(TestCaseBase) :
    
    #@skip
    def test( self ):
      print("Foo.test")
    
    #@skip
    def test2( self ):
      raise NotImplementedError()
  
  class Foo2(TestCaseBase) :
    
    #@skip
    def test( self ):
      print("Foo2.test")
    
    #@skip
    def test2( self ):
      print("Foo2.test2")
  
  runLocalTests()
  
  #~ pprint.pprint( runSuite( suiteLocal( globals() ) ) )
  
