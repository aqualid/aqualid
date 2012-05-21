import imp
import os.path
import unittest

__all__ = ('TestCaseBase', 'suite', 'suiteLocal', 'skip', 'runSuite' )

#//===========================================================================//

class TestCaseSuite(unittest.TestSuite):
  
  #//-------------------------------------------------------//
  
  def   __getTestCaseClass( self ):
    try:
      return next( iter(self) ).__class__
    except StopIteration:
      return None
  
  #//-------------------------------------------------------//
  
  def   __setUpTestCaseClass( self, test_case_class ):
    if test_case_class is not None:
      if not hasattr(unittest.TestCase, 'setUpClass' ):   # call setUpClass only if it's not supported
        setUpClass = getattr(test_case_class, 'setUpClass', None)
        if setUpClass is not None:
          setUpClass()
  
  #//-------------------------------------------------------//
  
  def   __tearDownTestCaseClass( self, test_case_class ):
    if test_case_class is not None:
      if not hasattr(unittest.TestCase, 'tearDownClass' ):  # call tearDownClass only if it's not supported
        tearDownClass = getattr(test_case_class, 'tearDownClass', None)
        if tearDownClass is not None:
          tearDownClass()
  
  #//-------------------------------------------------------//
  
  def run( self, result, debug = False ):
    
    test_case_class = self.__getTestCaseClass()
    
    if test_case_class is not None:
      print(">>>>>>>> Run test suite: %s.%s" % (test_case_class.__module__, test_case_class.__name__) )
    
    try:
      self.__setUpTestCaseClass( test_case_class )
      
      super(TestCaseSuite, self).run( result, debug )
      
      self.__tearDownTestCaseClass( test_case_class )
    finally:
      if test_case_class is not None:
        print("<<<<<<<< Finished test suite: %s.%s" % (test_case_class.__module__, test_case_class.__name__) )

#//===========================================================================//

class TestCaseBase(unittest.TestCase):
  
  def __init__(self, methodName = 'runTest', keep_going = False ):
    self.keep_going = keep_going
    super( TestCaseBase, self).__init__( methodName )
  
  #//-------------------------------------------------------//
  
  def run( self, result = None ):
    self.result = result
    
    if self.keep_going or result.wasSuccessful():
      super(TestCaseBase, self).run( result )
    else:
      result.stop()
  
  #//-------------------------------------------------------//
  
  @classmethod
  def setUpClass(cls):
    pass
  
  #//-------------------------------------------------------//
  
  @classmethod
  def tearDownClass(self):
    pass
  
  #//-------------------------------------------------------//
  
  def   tearDown(self):
    if not (self.keep_going or self.result.wasSuccessful()):
      self.result.stop()
    
    print(">> Finished TestCase: %s" % self.id() )
    
  #//-------------------------------------------------------//
  
  def   setUp(self):
    if not (self.keep_going or self.result.wasSuccessful()):
      self.result.stop()
    
    print(">> Run TestCase: %s" % self.id() )

#//===========================================================================//

def   _toSequence( value ):
  
  try:
    if not isinstance( value, str ):
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

def  _findTestModuleFiles( path, test_files_prefix ):
  
  test_case_modules = []
  
  for root, dirs, files in os.walk( path ):
    for file_name in files:
      file_name = file_name.lower()
      if file_name.startswith( test_files_prefix ) and file_name.endswith('.py'):
        test_case_modules.append( os.path.join(root, file_name))
    dirs[:] = filter( lambda d: not d.startswith('.') or d.startswith('__'), dirs )
  
  return test_case_modules

#//===========================================================================//

def   _loadTestModule( module_file ):
  
  module_dir = os.path.normpath( os.path.dirname( module_file ) )
  module_name = os.path.splitext( os.path.basename( module_file ) )[0]
  
  fp, pathname, description = imp.find_module( module_name, [ module_dir ] )
  
  with fp:
    print( "Loading test module: %s" % module_file )
    return imp.load_module( module_name, fp, pathname, description )

#//===========================================================================//

def   _loadTestModules( path, test_files_prefix ):
  
  test_modules = []
  module_files = []
  
  for path in _toSequence( path ):
    if os.path.isdir( path ):
      module_files += _findTestModuleFiles( path, test_files_prefix )
    else:
      module_files.append( path )
  
  for module_file in module_files:
    test_modules.append( _loadTestModule( module_file ) )
  
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

def   _loadTestCaseClasses( path, test_files_prefix ):
  return _getTestCaseClasses( _loadTestModules( path, test_files_prefix ) )

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
      print( "test_classes: %s" % str(test_classes) )
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
      if isinstance( name, str ):
        name = tuple( name.split('.')[-3:] )
      else:
        name = tuple( _toSequence( name ) )
      
      norm_names.add( name )
    
    return norm_names
  
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
  
  def   load( self, path = None, test_files_prefix = 'test', test_methods_prefix = 'test' ):
    test_classes = _loadTestCaseClasses( path, test_files_prefix )
    
    return Tests( test_classes )
  
  #//-------------------------------------------------------//
  
  def   sortedTests( self, all_tests, run_tests = None, add_tests = None, skip_tests = None, start_from_test = None ):
    if run_tests is None:
      tests  = all_tests.copy()
      
      if self.skip_test_methods:
        tests -= all_tests.getTestsByMethods( self.skip_test_methods )
      
      if self.skip_test_classes:
        tests -= all_tests.getTestsByClasses( self.skip_test_classes )
    else:
      tests = all_tests.getTestsByNames( run_tests )
    
    if add_tests:
      tests += all_tests.getTestsByNames( add_tests )
    
    if start_from_test:
      tests += all_tests.getTestsByNames( start_from_test )
      tests = Tests( tests.sortedFrom( start_from_test ) )
    
    if skip_tests:
      tests -= tests.getTestsByNames( skip_tests )
    
    return tests.sorted()
  
  #//-------------------------------------------------------//
  
  def   suite( self, sorted_tests, suite_class = TestCaseSuite ):
    
    main_suite = suite_class()
    for test_class, methods in sorted_tests:
      suite = suite_class()
      for method in methods:
        suite.addTest( test_class( method.__name__ ) )
      
      main_suite.addTest( suite )
    
    return main_suite

_suite_maker = TestsSuiteMaker()

#//===========================================================================//

def  skip( test_case ):
  global _suite_maker
  
  if isinstance( test_case, type) and issubclass( test_case, unittest.TestCase ):
    _suite_maker.skip_test_classes.add( test_case )
  
  elif hasattr(test_case, '__call__'):
    _suite_maker.skip_test_methods.add( test_case )
  
  return test_case

#//===========================================================================//

def   suite( path = None, test_files_prefix = 'test', test_methods_prefix = 'test',
           run_tests = None, add_tests = None, skip_tests = None, start_from_test = None, suite_class = TestCaseSuite ):
  
  global _suite_maker
  
  all_tests = _suite_maker.load( path, test_files_prefix, test_methods_prefix )
  sorted_tests = _suite_maker.sortedTests( all_tests, run_tests, add_tests, skip_tests, start_from_test )
  return _suite_maker.suite( sorted_tests, suite_class )

#//===========================================================================//

def   suiteLocal( test_methods_prefix = 'test',
                  run_tests = None, add_tests = None, skip_tests = None, start_from_test = None, suite_class = TestCaseSuite ):
  
  global _suite_maker
  
  all_tests =_suite_maker.loadLocals( test_methods_prefix )
  sorted_tests = _suite_maker.sortedTests( all_tests, run_tests, add_tests, skip_tests, start_from_test )
  return _suite_maker.suite( sorted_tests, suite_class )

#//===========================================================================//

def   runSuite( suite ):
  unittest.TextTestRunner().run( suite )

#//===========================================================================//

if __name__ == "__main__":
  
  #@skip
  class Foo(TestCaseBase) :
    
    #@skip
    def test( self ):
      print("Foo.test")
    
    #@skip
    def test2( self ):
      print("Foo.test2")
  
  class Foo2(TestCaseBase) :
    
    #@skip
    def test( self ):
      print("Foo2.test")
    
    #@skip
    def test2( self ):
      print("Foo2.test2")
  
  runSuite( suiteLocal() )
  
  #~ pprint.pprint( runSuite( suiteLocal( globals() ) ) )
  
