import sys
import os.path
import io
import pickle
import unittest

sys.path.insert( 0, os.path.normpath( os.path.join( os.path.dirname( __file__ ), '..', 'utils') ) )
sys.path.insert( 0, os.path.normpath( os.path.join( os.path.dirname( __file__ ), '..', 'events') ) )
sys.path.insert( 0, os.path.normpath( os.path.join( os.path.dirname( __file__ ), '..', 'values') ) )
sys.path.insert( 0, os.path.normpath( os.path.join( os.path.dirname( __file__ ), '..', 'nodes') ) )

from aql_value import NoContent

#//===========================================================================//

def  _getExecTests( tests ):
  
  exec_tests = set()
  add_tests = set()
  skip_tests = set()
  start_from_test = None
  
  for test in tests:
    if test.startswith('+'):
      add_tests.add( test[1:] )
    
    elif test.startswith('-'):
      skip_tests.add( test[1:] )
    
    elif test.startswith('~'):
      start_from_test = test[1:]
    
    elif test:
      exec_tests.add( test )
  
  return (exec_tests, add_tests, skip_tests, start_from_test)

#//===========================================================================//


class _Settings( object ):
  def   __init__(self):
    from optparse import OptionParser
    
    parser = OptionParser()
    
    parser.add_option("-c", "--config", dest = "config",
                      help = "Path to config file", metavar = "FILE PATH")
    
    parser.add_option("-x", "--tests", dest = "tests",
                      help = "List of tests which should be executed", metavar = "TESTS")
    
    parser.add_option("-q", "--quiet", action="store_false", dest="verbose",
                      help = "Quiet mode", default = True )
    
    (options, args) = parser.parse_args()
    print_usage = False
    
    settings = {}
    
    if options.config is not None:
      if not os.path.isfile(options.config):
        print( "Error: Config file doesn't exist." )
        print_usage = True
      else:
        execfile( options.config, {}, settings )
    
    for opt,value in options.__dict__.items():
      if (value is not None) or (opt not in settings):
        settings[ opt ] = value
    
    tests = settings['tests']
    if tests is None:
      settings['tests'] = []
    else:
      if not isinstance( tests, (list, tuple) ):
        settings['tests'] = tests.split(',')
    
    self.__dict__ = settings

#//===========================================================================//

class AqlTests(unittest.TestCase):
  
  testcases = set()
  
  def   __init__(self, testname, settings ):
    super(AqlTests, self).__init__(testname)
    
    self.settings = settings
    self.result = self.defaultTestResult()
  
  #//=======================================================//
  
  def run( self, result = None ):
    if result is not None:
      self.result = result
    
    super(AqlTests, self).run( self.result )
  
  #//=======================================================//
  
  def   tearDown(self):
    if not self.result.wasSuccessful():
      self.result.stop()
    
  #//===========================================================================//
  
  def   setUp(self):
    if not self.result.wasSuccessful():
      self.result.stop()
    
    print("")
    print( "*" * 64)
    print("* TestCase: %s" % self.id() )
    print("*" * 64)
  
  #//=======================================================//
  
  def testSaveLoad( self, value ):
    data = pickle.dumps( ( value, ), protocol = pickle.HIGHEST_PROTOCOL )
    
    loaded_values = pickle.loads( data )
    loaded_value = loaded_values[0]
    
    self.assertEqual( value.name, loaded_value.name )
    if type(value.content) is not NoContent:
      self.assertEqual( value.content, loaded_value.content )
    else:
      self.assertEqual( type(value.content), type(loaded_value.content) )
  
  #//=======================================================//


def  testcase( test_case ):
  if callable(test_case):
    test_case_name = test_case.__name__
    setattr( AqlTests, test_case_name, test_case )
    AqlTests.testcases.add( test_case_name )
  
  return test_case

#//===========================================================================//

def  skip( test_case ):
  if callable(test_case):
    try:
      AqlTests.testcases.remove( test_case.__name__ )
    except KeyError:
      pass
  
  return test_case

#//===========================================================================//

def _runTests( settings, tests = None, add_tests = None, skip_tests = None, start_from_test = None ):
  
  if not tests:
    tests = AqlTests.testcases
  
  tests = sorted(tests)
  
  try:
    if start_from_test is not None:
      tests = tests[ tests.index( start_from_test): ]
  except ValueError:
    pass
  
  tests = set(tests)
  
  if add_tests is not None:
    tests |= set(add_tests)
  
  if skip_tests is not None:
    tests -= set(skip_tests)
  
  tests = sorted(tests)
  
  suite = unittest.TestSuite()
  for test_method in tests:
    suite.addTest( AqlTests( test_method, settings ) )
  
  unittest.TextTestRunner().run(suite)

#//===========================================================================//

def   runTests():
  settings = _Settings()
  
  exec_tests, add_tests, skip_tests, start_from_test = _getExecTests( settings.tests )
  
  #//-------------------------------------------------------//
  
  _runTests( settings, exec_tests, add_tests, skip_tests, start_from_test )

