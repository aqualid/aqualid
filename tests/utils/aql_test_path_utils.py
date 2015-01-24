import sys
import os
import os.path

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import AqlTestCase, runLocalTests

from aql.utils import findFiles, changePath, \
  findProgram, findPrograms, findOptionalProgram, findOptionalPrograms, \
  relativeJoin, excludeFilesFromDirs, groupPathsByDir, \
  Chdir

#//===========================================================================//

class TestPathUtils( AqlTestCase ):
  #//===========================================================================//

  def test_path_relative_join(self):
    
    common_path = os.path.normcase( os.getcwd() + os.path.sep )
    dir1 = os.path.normcase( os.path.abspath('foo') )
    file2 = os.path.normcase( os.path.abspath('bar/file2.txt') )
    host_file = '//host/share/bar/file3.txt'
    
    disk_file = ''
    if dir1[0].isalpha():
      disk_file = os.path.join( 'a:', os.path.splitdrive( dir1 )[1] )
    
    self.assertEqual( relativeJoin( dir1, file2 ), os.path.join( dir1, 'bar', 'file2.txt') )
    self.assertEqual( relativeJoin( dir1, host_file ), os.path.join( dir1, *(filter(None, host_file.split('/'))) ) )
    
    if disk_file:
      self.assertEqual( relativeJoin( dir1, disk_file ), os.path.join( dir1, *disk_file.replace(':', os.path.sep ).split( os.path.sep ) ) )
    self.assertEqual( relativeJoin( dir1, '' ), os.path.join( dir1, '.' ) )
    self.assertEqual( relativeJoin( dir1, '.' ), os.path.join( dir1, '.' ) )
    self.assertEqual( relativeJoin( dir1, '..' ), os.path.join( dir1, '..' ) )
    
    self.assertEqual( relativeJoin('foo/bar', 'bar/foo/file.txt' ), os.path.normpath( 'foo/bar/bar/foo/file.txt') )
    self.assertEqual( relativeJoin('foo/bar', 'foo/file.txt' ), os.path.normpath( 'foo/bar/file.txt' ) )
  
  #//=======================================================//
  
  def   test_path_change( self ):
    self.assertEqual( changePath( 'file0.txt', ext = '.ttt'), 'file0.ttt' )
    self.assertEqual( changePath( 'file0.txt', dirname = os.path.normpath('foo/bar')), os.path.normpath( 'foo/bar/file0.txt') )
  
  #//=======================================================//
  
  def   test_path_group_dirs( self ):
    paths = list( map( os.path.normpath, ['abc/file0.txt', 'abc/file1.txt', 'def/file2.txt', 'ghi/file0.txt', 'klm/file0.txt', 'ghi/file1.txt' ] ) )
    
    def   _normPaths( paths_list ):
      norm_paths_list = []
      for paths in paths_list:
        norm_paths_list.append( [ os.path.normpath( path) for path in paths ] )
      return norm_paths_list
    
    groups = groupPathsByDir( paths )
    
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt', 'abc/file1.txt'],
                                          ['def/file2.txt'],
                                          ['ghi/file0.txt', 'ghi/file1.txt'],
                                          ['klm/file0.txt'] ]))
    
    groups = groupPathsByDir( paths, max_group_size = 1 )
    
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt'], ['abc/file1.txt'], ['def/file2.txt'], ['ghi/file0.txt'], ['ghi/file1.txt' ], ['klm/file0.txt'] ]) )
    
    groups = groupPathsByDir( paths, max_group_size = 2 )
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt', 'abc/file1.txt'], ['def/file2.txt'], ['ghi/file0.txt', 'ghi/file1.txt'], ['klm/file0.txt'] ]))
    
    groups = groupPathsByDir( paths, wish_groups = 3 )
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt', 'abc/file1.txt'], ['def/file2.txt'], ['ghi/file0.txt', 'ghi/file1.txt'], ['klm/file0.txt'] ]))
    
    paths = list( map( os.path.normpath, ['abc/file0.txt', 'abc/file1.txt', 'abc/file2.txt', 'abc/file3.txt', 'abc/file4.txt', 'abc/file5.txt' ] ) )
    groups = groupPathsByDir( paths, wish_groups = 3 )
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt', 'abc/file1.txt'], ['abc/file2.txt', 'abc/file3.txt'], ['abc/file4.txt', 'abc/file5.txt'] ]))
    
    groups = groupPathsByDir( paths, wish_groups = 2 )
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt', 'abc/file1.txt', 'abc/file2.txt'], ['abc/file3.txt', 'abc/file4.txt', 'abc/file5.txt'] ]))
    
    groups = groupPathsByDir( paths, wish_groups = 2, max_group_size = 1 )
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt'], ['abc/file1.txt'], ['abc/file2.txt'], ['abc/file3.txt'], ['abc/file4.txt'], ['abc/file5.txt'] ]))
    
    groups = groupPathsByDir( paths, wish_groups = 1 )
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt', 'abc/file1.txt', 'abc/file2.txt', 'abc/file3.txt', 'abc/file4.txt', 'abc/file5.txt'] ]))
    
    paths = list( map( os.path.normpath, ['abc/file0.txt', 'abc/file1.txt', 'abc/file2.txt', 'abc/file3.txt', 'abc/file4.txt', 'abc/file5.txt', 'abc/file6.txt' ] ) )
    groups = groupPathsByDir( paths, wish_groups = 3 )
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt', 'abc/file1.txt'], ['abc/file2.txt', 'abc/file3.txt'], ['abc/file4.txt', 'abc/file5.txt', 'abc/file6.txt'] ]))
    
    groups = groupPathsByDir( paths, wish_groups = 3, max_group_size = 2 )
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt', 'abc/file1.txt'], ['abc/file2.txt', 'abc/file3.txt'], ['abc/file4.txt', 'abc/file5.txt'], ['abc/file6.txt'] ]))
    
  #//===========================================================================//
  
  def   test_find_prog( self ):
    os_env = os.environ
    prog = findProgram( 'route', os_env )
    self.assertEqual( findProgram( 'route', os_env, prog ), prog )
    self.assertIsNone( findProgram( 'non-existing-program', os_env, prog ) )
    self.assertIsNone( findProgram( 'route', env = {} ) )
    self.assertEqual( findProgram( 'route', {}, prog ), prog )
    
    route1, route2 = findPrograms( ['route', 'route'], os_env )
    self.assertEqual( route1, route2 )
    
    route1, route2 = findPrograms( ['route', 'route'], env = {}, hint_prog = prog )
    self.assertEqual( route1, route2 )
    
    self.assertTrue( findOptionalProgram( 'route', os_env ) )
    
    oprog = findOptionalProgram( 'route', env = {} )
    self.assertTrue( oprog.get().startswith('route') )
    
    route1, route2 = findOptionalPrograms( ['route', 'route'], os_env )
    self.assertEqual( route1.get(), route2.get() )
    
    route1, route2 = findOptionalPrograms( ['route', 'route'], env = {}, hint_prog = prog )
    self.assertEqual( route1.get(), route2.get() )
    
    progs = findOptionalPrograms( ['route'], env = {} )
    self.assertTrue( progs[0].get().startswith( 'route' ) )
  
  #//===========================================================================//
  
  def   test_find_files( self ):
    path = os.path.join( os.path.dirname( __file__ ), '..', '..') 
    
    files = findFiles( path, mask = ['*.pythonics', "*.tdt", "*.py", "*.pyc" ] )
    self.assertIn( os.path.abspath(__file__), files )
    
    files2 = findFiles( path, mask = '|*.pythonics|*.tdt||*.py|*.pyc' )
    self.assertEqual( files2, files )
  
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
