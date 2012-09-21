import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_path_types import FilePath, FilePaths

#//===========================================================================//

class TestPathTypes( AqlTestCase ):
  #//===========================================================================//

  def test_file_path(self):
    
    file1 = os.path.abspath('foo/file.txt')
    file2 = os.path.abspath('bar/file2.txt')
    host_file = '//host/share/bar/file3.txt'
    
    
    disk_file = ''
    if file1[0].isalpha():
      disk_file = os.path.join( 'a:', os.path.splitdrive( file1 )[1] )
    
    p = FilePath( file1 )
    p2 = FilePath( file2 )
    self.assertEqual( p.name_ext, os.path.basename(file1) )
    self.assertEqual( p.dir, os.path.dirname(file1) )
    self.assertEqual( p.name, os.path.splitext( os.path.basename(file1) )[0] )
    self.assertEqual( p.ext, os.path.splitext( os.path.basename(file1) )[1] )
    self.assertIn( p.drive, [ os.path.splitdrive( file1 )[0], os.path.splitunc( file1 )[0] ] )
    
    self.assertEqual( p.merge( p2 ), os.path.join( p, os.path.basename(p2.dir), p2.name_ext ) )
    self.assertEqual( p.merge( host_file ), os.path.join( p, *(filter(None, host_file.split('/'))) ) )
    
    if disk_file:
      self.assertEqual( p.merge( disk_file ), os.path.join( p, 'a', os.path.splitdrive( file1 )[1].strip( os.path.sep ) ) )
    self.assertEqual( p.merge( '' ), file1 )
    self.assertEqual( p.merge( '.' ), file1 )
    self.assertEqual( p.merge( '..' ), p.dir )
    self.assertEqual( FilePath('foo/bar').merge( 'bar/foo/file.txt' ), 'foo/bar/bar/foo/file.txt' )
    self.assertEqual( FilePath('foo/bar').merge( 'foo/file.txt' ), 'foo/bar/file.txt' )
    
    self.assertEqual( FilePath('foo/bar').join( 'foo/file.txt' ), 'foo/bar/foo/file.txt' )
    self.assertEqual( FilePath('foo/bar').join( ['foo'], 'file.txt' ), 'foo/bar/foo/file.txt' )
    self.assertEqual( FilePath('foo/bar').join( ['foo', 'foo2'], 'test', 'file.txt' ), 'foo/bar/foo/foo2/test/file.txt' )
  
  #//=======================================================//
  
  def   test_file_paths( self ):
    paths = FilePaths()
    
    paths += ['file0.txt', 'file1.txt', 'file2.txt' ]
    
    self.assertEqual( paths.change( ext = '.ttt'), ['file0.ttt', 'file1.ttt', 'file2.ttt' ] )
    self.assertEqual( paths.change( dir = 'foo/bar'), ['foo/bar/file0.txt', 'foo/bar/file1.txt', 'foo/bar/file2.txt' ] )
  
  #//=======================================================//
  
  def   test_file_path_groups( self ):
    paths = FilePaths(['abc/file0.txt', 'abc/file1.txt', 'def/file2.txt', 'ghi/file0.txt', 'klm/file0.txt', 'ghi/file1.txt' ])
    
    groups = paths.groupUniqueNames()
    
    self.assertEqual( groups, [ ['abc/file0.txt', 'abc/file1.txt', 'def/file2.txt'], ['ghi/file0.txt', 'ghi/file1.txt'], ['klm/file0.txt'] ])
  
  #//=======================================================//
  
  def   test_file_path_change( self ):
    paths = FilePaths(['abc/file0.txt', 'abc/file1.txt', 'def/file2.txt'])
    paths_ttt, paths_eee = paths.change( ext = ['.ttt', '.eee'])
    
    self.assertEqual( paths_ttt, ['abc/file0.ttt', 'abc/file1.ttt', 'def/file2.ttt'])
    self.assertEqual( paths_eee, ['abc/file0.eee', 'abc/file1.eee', 'def/file2.eee'])
    
    paths_foo, paths_bar = paths.change( dir = ['foo', 'bar'] )
    
    self.assertEqual( paths_foo, ['foo/file0.txt', 'foo/file1.txt', 'foo/file2.txt'])
    self.assertEqual( paths_bar, ['bar/file0.txt', 'bar/file1.txt', 'bar/file2.txt'])
    
    paths_foo_ttt, paths_foo_eee, paths_bar_ttt, paths_bar_eee = paths.change( dir = ['foo', 'bar'], ext = ['.ttt', '.eee'] )
    
    self.assertEqual( paths_foo_ttt, ['foo/file0.ttt', 'foo/file1.ttt', 'foo/file2.ttt'])
    self.assertEqual( paths_foo_eee, ['foo/file0.eee', 'foo/file1.eee', 'foo/file2.eee'])
    self.assertEqual( paths_bar_ttt, ['bar/file0.ttt', 'bar/file1.ttt', 'bar/file2.ttt'])
    self.assertEqual( paths_bar_eee, ['bar/file0.eee', 'bar/file1.eee', 'bar/file2.eee'])
    
    paths_www = paths.change( ext = '.www' )
    self.assertEqual( paths_www, ['abc/file0.www', 'abc/file1.www', 'def/file2.www'])
  
  #//=======================================================//
  
  def   test_file_path_add( self ):
    paths = FilePaths(['abc/file0.txt', 'abc/file1.txt', 'def/file2.txt'])
    paths_ttt, paths_eee = paths.add( suffix = ['.ttt', '.eee'] )
    
    self.assertEqual( paths_ttt, ['abc/file0.txt.ttt', 'abc/file1.txt.ttt', 'def/file2.txt.ttt'])
    self.assertEqual( paths_eee, ['abc/file0.txt.eee', 'abc/file1.txt.eee', 'def/file2.txt.eee'])
    
    paths_www = paths.add( suffix = '.www' )
    self.assertEqual( paths_www, ['abc/file0.txt.www', 'abc/file1.txt.www', 'def/file2.txt.www'])
  
#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
