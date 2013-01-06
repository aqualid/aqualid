import sys
import os.path
import timeit
import hashlib
import shutil

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import isSequence, equalFunctionArgs, checkFunctionArgs, getFunctionName, \
                      whereProgram, execCommand, ErrorProgramNotFound, findFiles

class TestUtils( AqlTestCase ):
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

  def test_checkFunctionArgs(self):
    def   f(): pass
    def   f0( a, b, c ): pass
    def   f1( a, b, c, d = 0, e = 1, f = 2, *args, **kw): pass
    
    args = []
    kw = {}
    
    self.assertTrue( checkFunctionArgs( f, args, kw) )
    
    args = [1,2,3]
    kw = {}
    
    self.assertTrue( checkFunctionArgs( f0, args, kw) )
    
    args = []
    kw = {'a':2, 'c':4, 'b': 3}
    
    self.assertTrue( checkFunctionArgs( f0, args, kw) )
    
    args = [1]
    kw = {'c':4, 'b': 3}
    
    self.assertTrue( checkFunctionArgs( f0, args, kw) )
    
    kw = {'g':4, 'f': 3}
    args = [1,2,3,4,5]
    
    self.assertTrue( checkFunctionArgs( f1, args, kw) )
    
    args = [1,2,3,4 ]
    kw = {'e':4, 'f': 3}
    
    self.assertTrue( checkFunctionArgs( f1, args, kw) )
    
    args = [1,2,3,4 ]
    kw = {'a':4, 'f': 3}
    
    self.assertFalse( checkFunctionArgs( f1, args, kw) )
    
    args = []
    kw = {'e':4, 'f': 3, 'd': 1 }
    
    self.assertFalse( checkFunctionArgs( f1, args, kw) )
    
    args = []
    kw = {}
    
    self.assertFalse( checkFunctionArgs( f1, args, kw) )
    
    #//-------------------------------------------------------//
    
    class Foo:
      def   test(self, a, b, c):
        pass
    
    class Bar( Foo ):
      pass
    
    args = [None, 1, 2, 3]
    kw = {}
    
    self.assertTrue( checkFunctionArgs( Foo().test, args, kw) )

  #//===========================================================================//

  def   test_functionName( self ):
    self.assertTrue( getFunctionName(), 'test_functionName' )
  
  #//===========================================================================//
  
  def   test_exec_command( self ):
    result = execCommand("route")
    self.assertTrue( result.out or result.err )
  
  #//===========================================================================//
  
  def   test_find_prog( self ):
    self.assertTrue( whereProgram, 'route' )
    self.assertRaises( ErrorProgramNotFound, whereProgram, 'route', env = {} )
  
  #//===========================================================================//
  
  @skip
  def   test_find_files( self ):
    files = findFiles( r"../..", suffixes = ".py" )
    #~ files = findFiles( r"C:\work\src\aql\aql\main", prefixes = "aql_test_", suffixes = [".py", ".pyc"] )
    import pprint
    pprint.pprint( files )
  
#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
