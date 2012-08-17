import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_simple_types import IgnoreCaseString, LowerCaseString, UpperCaseString, Version, FilePath

#//===========================================================================//

class TestSimpleTypes( AqlTestCase ):
  def test_istr(self):
    event_manager.setHandlers( EventHandler() )
    
    s1 = IgnoreCaseString('ABC')
    s2 = IgnoreCaseString('abc')
    
    self.assertEqual( s1, s2 )
    self.assertNotEqual( str(s1), str(s2) )
    
    a = {}
    a[s1] = 1
    a[s2] = 2
    
    self.assertEqual( len(a), 1 )
    
    b = set()
    b.add(s1)
    b.add(s2)
    
    self.assertEqual( len(b), 1 )
    
    self.assertIs( s1, IgnoreCaseString( s1 ) )

  #//===========================================================================//

  def test_lowerstr(self):
    event_manager.setHandlers( EventHandler() )
    
    s1 = LowerCaseString('ABC')
    s2 = LowerCaseString('abc')
    
    self.assertEqual( s1, s2 )
    self.assertEqual( str(s1), str(s2) )
    
    a = {}
    a[s1] = 1
    a[s2] = 2
    
    self.assertEqual( len(a), 1 )
    
    b = set()
    b.add(s1)
    b.add(s2)
    
    self.assertEqual( len(b), 1 )
    
    self.assertIs( s1, LowerCaseString( s1 ) )

  #//===========================================================================//

  def test_upperstr(self):
    event_manager.setHandlers( EventHandler() )
    
    s1 = UpperCaseString('ABC')
    s2 = UpperCaseString('abc')
    
    self.assertEqual( s1, s2 )
    self.assertEqual( str(s1), str(s2) )
    
    a = {}
    a[s1] = 1
    a[s2] = 2
    
    self.assertEqual( len(a), 1 )
    
    b = set()
    b.add(s1)
    b.add(s2)
    
    self.assertEqual( len(b), 1 )
    
    self.assertIs( s1, UpperCaseString( s1 ) )

  #//===========================================================================//

  def test_version(self):
    event_manager.setHandlers( EventHandler() )
    
    v1 = Version('1.2.100')
    v2 = Version('1.2.99')
    
    self.assertLess( v2, v1 )
    
    a = {}
    a[v1] = 1
    a[v2] = 2
    
    v3 = Version('1.2.100')
    a[v3] = 3
    
    self.assertEqual( len(a), 2 )
    
    b = set()
    b.add(v1)
    b.add(v2)
    b.add(v3)
    
    self.assertEqual( len(b), 2 )
    
    self.assertIs( v1, Version( v1 ) )
  
  #//===========================================================================//

  def test_file_path(self):
    
    file1 = os.path.abspath('foo/file.txt')
    file2 = os.path.abspath('bar/file2.txt')
    host_file = '//host/share/bar/file3.txt'
    
    if file1[0].isalpha():
      disk_file = os.path.join( 'a:', os.path.splitdrive( file1 )[1] )
    
    p = FilePath( file1 )
    p2 = FilePath( file2 )
    self.assertEqual( p.name_ext, os.path.basename(file1) )
    self.assertEqual( p.dir, os.path.dirname(file1) )
    self.assertEqual( p.name, os.path.splitext( os.path.basename(file1) )[0] )
    self.assertEqual( p.ext, os.path.splitext( os.path.basename(file1) )[1] )
    self.assertEqual( p.drive, os.path.splitdrive( file1 )[0] )
    
    self.assertEqual( p.mergePaths( p2 ), os.path.join( p, os.path.basename(p2.dir), p2.name_ext ) )
    self.assertEqual( p.mergePaths( host_file ), os.path.join( p, *(filter(None, host_file.split('/'))) ) )
    
    self.assertEqual( p.mergePaths( disk_file ), os.path.join( p, 'a', os.path.splitdrive( file1 )[1].strip( os.path.sep ) ) )
    self.assertEqual( p.mergePaths( '' ), file1 )
    self.assertEqual( p.mergePaths( '.' ), file1 )
    self.assertEqual( p.mergePaths( '..' ), p.dir )
    self.assertEqual( FilePath('foo/bar').mergePaths( 'bar/foo/file.txt' ), 'foo/bar/bar/foo/file.txt' )
    self.assertEqual( FilePath('foo/bar').mergePaths( 'foo/file.txt' ), 'foo/bar/file.txt' )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
