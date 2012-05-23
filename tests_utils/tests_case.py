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
  
  def __init__(self, methodName = 'runTest', keep_going = NotImplemented ):
    
    if keep_going is NotImplemented:
      from tests_options import getOptions
      keep_going = getOptions().keep_going
    
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
    
  #//-------------------------------------------------------//
  
  def   setUp(self):
    if not (self.keep_going or self.result.wasSuccessful()):
      self.result.stop()
