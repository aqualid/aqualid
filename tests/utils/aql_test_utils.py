import sys
import os.path
import timeit
import hashlib
import shutil

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_utils import fileChecksum, isSequence, toSequence, equalFunctionArgs, checkFunctionArgs

@testcase
def test_isSequence(self):
  
  self.assertTrue( isSequence([1,2]) )
  self.assertTrue( isSequence((1,2)) )
  self.assertTrue( isSequence({1:2}) )
  self.assertTrue( isSequence(set([1,2])) )
  self.assertTrue( isSequence(frozenset([1,2])) )
  self.assertTrue( isSequence(filter( lambda v: True, [1,2])) )
  self.assertTrue( isSequence(map( lambda v: v, [1,2])) )
  self.assertTrue( isSequence(iter([1,2])) )
  
  self.assertFalse( isSequence( 1 ) )
  self.assertFalse( isSequence( None ) )

#//===========================================================================//

@testcase
def test_equalFunctionArgs(self):
  def   f0( a, b, c ): pass
  def   f1( a, b, c ): pass
  
  self.assertTrue( equalFunctionArgs( f0, f1 ) )
  
  def   f2( a, b, c, *args ): pass
  def   f3( a, b, c, *args ): pass
  
  self.assertTrue( equalFunctionArgs( f2, f3 ) )
  
  def   f4( a, b, c = 3, *args, **kw): pass
  def   f5( a, b, c, *args, **kw): pass
  
  self.assertTrue( equalFunctionArgs( f4, f5 ) )
  
  def   f6( a, b, c ): pass
  def   f7( a, b, c, *args ): pass
  
  self.assertFalse( equalFunctionArgs( f6, f7 ) )

#//===========================================================================//

@testcase
def test_checkFunctionArgs(self):
  def   f0( a, b, c ): pass
  def   f1( a, b, c, d = 0, e = 1, f = 2, *args, **kw): pass
  
  args = [1,2,3]
  kw = {}
  
  self.assertTrue( checkFunctionArgs( f0, args, kw) )
  
  args = []
  kw = {'a':2, 'c':4, 'b': 3}

  self.assertTrue( checkFunctionArgs( f0, args, kw) )
  
  args = [1]
  kw = {'c':4, 'b': 3}

  self.assertTrue( checkFunctionArgs( f0, args, kw) )
  
  args = [1,2,3,4,5]
  kw = {'g':4, 'f': 3}

  self.assertTrue( checkFunctionArgs( f1, args, kw) )
  
  args = [1,2,3,4 ]
  kw = {'e':4, 'f': 3}

  self.assertTrue( checkFunctionArgs( f1, args, kw) )


#//===========================================================================//

if __name__ == "__main__":
  runTests()
