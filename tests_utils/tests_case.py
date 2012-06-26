import imp
import os.path
import unittest

__all__ = ('TestCaseSuite', 'TestCaseBase')

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
  
  def run( self, result ):
    
    test_case_class = self.__getTestCaseClass()
    
    self.__setUpTestCaseClass( test_case_class )
    
    super(TestCaseSuite, self).run( result )
    
    self.__tearDownTestCaseClass( test_case_class )

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
  def tearDownClass(cls):
    pass
  
  #//-------------------------------------------------------//
  
  def   tearDown(self):
    if not (self.keep_going or self.result.wasSuccessful()):
      self.result.stop()
    
  #//-------------------------------------------------------//
  
  def   setUp(self):
    if not (self.keep_going or self.result.wasSuccessful()):
      self.result.stop()
    
    print( "\n*** RUN TEST: %s ***" % self.id() )
  
  #//-------------------------------------------------------//
  
  if not hasattr( unittest.TestCase, 'assertIn' ):
    def assertIn( self, a, b, msg = None):
      if msg is None: str(a) + " in " + str(b) + ' is False'
      self.assertTrue( a in b, msg )
  
  if not hasattr( unittest.TestCase, 'assertNotIn' ):
    def assertNotIn( self, a, b, msg = None):
      if msg is None: str(a) + " not in " + str(b) + ' is False'
      self.assertTrue( a not in b, msg)
  
  if not hasattr( unittest.TestCase, 'assertIsNone' ):
    def assertIsNone( self, a, msg = None):
      if msg is None: str(a) + " is " + str(None) + ' is False'
      self.assertTrue( a is None, msg )
  
  if not hasattr( unittest.TestCase, 'assertIsNotNone' ):
    def assertIsNotNone( self, a, msg = None):
      if msg is None: str(a) + " is not " + str(None) + ' is False'
      self.assertTrue( a is not None, msg )
  
  if not hasattr( unittest.TestCase, 'assertGreater' ):
    def assertGreater( self, a, b, msg = None):
      if msg is None: msg = str(a) + " > " + str(b) + ' is False'
      self.assertTrue( a > b, msg )
  
  if not hasattr( unittest.TestCase, 'assertGreaterEqual' ):
    def assertGreaterEqual( self, a, b, msg = None):
      if msg is None: msg = str(a) + " >= " + str(b) + ' is False'
      self.assertTrue( a >= b, msg )
  
  if not hasattr( unittest.TestCase, 'assertLess' ):
    def assertLess( self, a, b, msg = None):
      if msg is None: msg = str(a) + " < " + str(b) + ' is False'
      self.assertTrue( a < b, msg )
  
  if not hasattr( unittest.TestCase, 'assertLessEqual' ):
    def assertLessEqual( self, a, b, msg = None):
      if msg is None: msg = str(a) + " <= " + str(b) + ' is False'
      self.assertTrue( a <= b, msg)
  
  if not hasattr( unittest.TestCase, 'assertItemsEqual' ):
    def assertItemsEqual( self, actual, expected, msg = None):
      def _valueCounts( seq ):
        counts = dict()
        for value in seq:
          counts.setdefault( value, 0 )
          counts[ value ] += 1
        return counts
      
      actual_counts = _valueCounts( actual )
      expected_counts = _valueCounts( expected )
      
      if msg is None: msg = str(actual) + " != " + str(expected)
      
      self.assertTrue( actual_counts == expected_counts, msg )
