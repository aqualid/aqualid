import sys
import os.path

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import equalFunctionArgs, checkFunctionArgs, getFunctionName, \
                      whereProgram, executeCommand, ErrorProgramNotFound, findFiles, flattenList, commonDirName, \
                      excludeFilesFromDirs

class TestUtils( AqlTestCase ):

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
    result = executeCommand("route")
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
  
  def   test_flatten( self ):
    
    l = []
    l_flat = []
    for i in range(2000):
      l = [l, i ]
      l_flat.append( i )
    
    self.assertEqual( flattenList( l ), l_flat )
    self.assertEqual( flattenList( [] ), [] )
    self.assertEqual( flattenList( [([1,3,4], [2,3])] ), [1,3,4,2,3] )
  
  #//===========================================================================//
  
  def   test_common_dirname( self ):
    
    paths = [ 'abc/cores',
              'abc/cores2',
            ]
    
    self.assertEqual( commonDirName( paths), "abc" + os.path.sep )
    
    paths = [ 'abc/cores1',
              'abc/cores2',
            ]
    
    self.assertEqual( commonDirName( paths), "abc" + os.path.sep )
    
    paths = [ 'abc/efg/cores1',
              'abc/efg/cores/abc',
              'abc/efg/cores2',
            ]
    
    self.assertEqual( commonDirName( paths ), "abc%sefg%s" % (os.path.sep,os.path.sep) )
    
    paths = [ 'abc/efg/cores1',
              'efg/efg/cores/abc',
              'abc/efg/cores2',
            ]
    
    self.assertEqual( commonDirName( paths ), "" )
    
    paths = [ '/abc/efg/cores1',
              '/efg/efg/cores/abc',
              '/abc/efg/cores2',
            ]
    
    self.assertEqual( commonDirName( paths ), os.path.sep )
  
  #//===========================================================================//
  
  def   test_exclude_files( self ):
    
    dirs = 'abc/test0'
    files = [ 'abc/file0.hpp',
              'abc/test0/file0.hpp' ]
    
    result = [ 'abc/file0.hpp' ]
    
    result = [ os.path.normcase( os.path.abspath( file )) for file in result ]
    
    self.assertEqual( excludeFilesFromDirs( files, dirs ), result )
    
    dirs = ['abc/test0', 'efd', 'ttt/eee']
    files = [
              'abc/test0/file0.hpp',
              'abc/file0.hpp',
              'efd/file1.hpp',
              'dfs/file1.hpp',
              'ttt/file1.hpp',
              'ttt/eee/file1.hpp',
            ]
    
    result = [ 'abc/file0.hpp', 'dfs/file1.hpp', 'ttt/file1.hpp' ]
    
    result = [ os.path.normcase( os.path.abspath( file )) for file in result ]
    
    self.assertEqual( excludeFilesFromDirs( files, dirs ), result )
    
#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
