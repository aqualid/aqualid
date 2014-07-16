import sys
import os.path

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import AqlTestCase, runLocalTests

from aql.utils import findFiles, changePath, \
  whereProgram, ErrorProgramNotFound, findOptionalProgram, findOptionalPrograms, \
  relativeJoin, excludeFilesFromDirs, groupPathsByDir, groupPathsByUniqueName, \
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
  
  def   test_path_group_unique_names( self ):
    paths = ['abc/file0.txt', 'abc/file1.txt', 'def/file2.txt', 'ghi/file0.txt', 'klm/file0.txt', 'ghi/file1.txt']
    
    groups = groupPathsByUniqueName( paths )
    
    self.assertEqual( groups, [ ['abc/file0.txt', 'abc/file1.txt', 'def/file2.txt'], ['ghi/file0.txt', 'ghi/file1.txt'], ['klm/file0.txt'] ])
    
    groups = groupPathsByUniqueName( paths, max_group_size = 1 )
    
    self.assertEqual( groups, [ ['abc/file0.txt'], ['abc/file1.txt'], ['def/file2.txt'], ['ghi/file0.txt'], ['klm/file0.txt'], ['ghi/file1.txt' ] ])
    
    groups = groupPathsByUniqueName( paths, max_group_size = 2 )
    self.assertEqual( groups, [ ['abc/file0.txt', 'abc/file1.txt'], ['def/file2.txt', 'ghi/file0.txt'], ['klm/file0.txt', 'ghi/file1.txt' ] ])
    
    groups = groupPathsByUniqueName( paths, wish_groups = 3 )
    self.assertEqual( groups, [ ['abc/file0.txt', 'abc/file1.txt'], ['def/file2.txt', 'ghi/file0.txt'], ['klm/file0.txt', 'ghi/file1.txt' ] ])
    
    groups = groupPathsByUniqueName( paths, wish_groups = 2 )
    self.assertEqual( groups, [ ['abc/file0.txt', 'abc/file1.txt', 'def/file2.txt'], ['ghi/file0.txt','ghi/file1.txt'], ['klm/file0.txt'] ])
    
    paths = ['abc/file0.txt', 'abc/file1.txt', 'def/file2.txt', 'ghi/file3.txt', 'klm/file4.txt', 'ghi/file5.txt', 'ghi/file6.txt' ]
    groups = groupPathsByUniqueName( paths, wish_groups = 2 )
    self.assertEqual( groups, [ ['abc/file0.txt', 'abc/file1.txt', 'def/file2.txt'], ['ghi/file3.txt', 'klm/file4.txt', 'ghi/file5.txt', 'ghi/file6.txt' ] ])
    
    groups = groupPathsByUniqueName( paths, wish_groups = 1 )
    self.assertEqual( groups, [ ['abc/file0.txt', 'abc/file1.txt', 'def/file2.txt', 'ghi/file3.txt', 'klm/file4.txt', 'ghi/file5.txt', 'ghi/file6.txt' ] ])
    
    groups = groupPathsByUniqueName( paths, wish_groups = 3 )
    self.assertEqual( groups, [ ['abc/file0.txt', 'abc/file1.txt'], ['def/file2.txt', 'ghi/file3.txt'], ['klm/file4.txt', 'ghi/file5.txt', 'ghi/file6.txt' ] ])
    
    groups = groupPathsByUniqueName( paths, wish_groups = 4 )
    self.assertEqual( groups, [ ['abc/file0.txt'], ['abc/file1.txt', 'def/file2.txt'], ['ghi/file3.txt', 'klm/file4.txt'], ['ghi/file5.txt', 'ghi/file6.txt' ] ])
    
    groups = groupPathsByUniqueName( paths, wish_groups = 5 )
    self.assertEqual( groups, [ ['abc/file0.txt'], ['abc/file1.txt'], ['def/file2.txt'], ['ghi/file3.txt', 'klm/file4.txt'], ['ghi/file5.txt', 'ghi/file6.txt' ] ])
    
    groups = groupPathsByUniqueName( paths, wish_groups = 6 )
    self.assertEqual( groups, [ ['abc/file0.txt'], ['abc/file1.txt'], ['def/file2.txt'], ['ghi/file3.txt'], ['klm/file4.txt'], ['ghi/file5.txt', 'ghi/file6.txt' ] ])
    
    groups = groupPathsByUniqueName( paths, wish_groups = 7 )
    self.assertEqual( groups, [ ['abc/file0.txt'], ['abc/file1.txt'], ['def/file2.txt'], ['ghi/file3.txt'], ['klm/file4.txt'], ['ghi/file5.txt'], ['ghi/file6.txt' ] ])
    
    groups = groupPathsByUniqueName( paths, wish_groups = 8 )
    self.assertEqual( groups, [ ['abc/file0.txt'], ['abc/file1.txt'], ['def/file2.txt'], ['ghi/file3.txt'], ['klm/file4.txt'], ['ghi/file5.txt'], ['ghi/file6.txt' ] ])
    
    groups = groupPathsByUniqueName( paths, wish_groups = 10 )
    self.assertEqual( groups, [ ['abc/file0.txt'], ['abc/file1.txt'], ['def/file2.txt'], ['ghi/file3.txt'], ['klm/file4.txt'], ['ghi/file5.txt'], ['ghi/file6.txt' ] ])
    
    paths = ['file0.txt', 'file1.txt', 'file2.txt', 'file3.txt', 'file4.txt']
    groups = groupPathsByUniqueName( paths, wish_groups = 4 )
    self.assertEqual( groups, [ ['file0.txt'], ['file1.txt'], ['file2.txt'], ['file3.txt', 'file4.txt'] ] )
  
  #//=======================================================//
  
  def   test_path_group_dirs( self ):
    paths = ['abc/file0.txt', 'abc/file1.txt', 'def/file2.txt', 'ghi/file0.txt', 'klm/file0.txt', 'ghi/file1.txt' ]
    
    def   _normPaths( paths_list ):
      norm_paths_list = []
      for paths in paths_list:
        norm_paths_list.append( [ os.path.normpath( path) for path in paths ] )
      return norm_paths_list
    
    groups, indexes = groupPathsByDir( paths )
    
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt', 'abc/file1.txt'],
                                          ['def/file2.txt'],
                                          ['ghi/file0.txt', 'ghi/file1.txt'],
                                          ['klm/file0.txt'] ]))
    self.assertEqual( indexes, [ [0,1], [2], [3,5], [4] ])
    
    groups, indexes = groupPathsByDir( paths, max_group_size = 1 )
    
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt'], ['abc/file1.txt'], ['def/file2.txt'], ['ghi/file0.txt'], ['ghi/file1.txt' ], ['klm/file0.txt'] ]) )
    
    groups, indexes = groupPathsByDir( paths, max_group_size = 2 )
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt', 'abc/file1.txt'], ['def/file2.txt'], ['ghi/file0.txt', 'ghi/file1.txt'], ['klm/file0.txt'] ]))
    
    groups, indexes = groupPathsByDir( paths, wish_groups = 3 )
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt', 'abc/file1.txt'], ['def/file2.txt'], ['ghi/file0.txt', 'ghi/file1.txt'], ['klm/file0.txt'] ]))
    
    paths = ['abc/file0.txt', 'abc/file1.txt', 'abc/file2.txt', 'abc/file3.txt', 'abc/file4.txt', 'abc/file5.txt' ]
    groups, indexes = groupPathsByDir( paths, wish_groups = 3 )
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt', 'abc/file1.txt'], ['abc/file2.txt', 'abc/file3.txt'], ['abc/file4.txt', 'abc/file5.txt'] ]))
    
    groups, indexes = groupPathsByDir( paths, wish_groups = 2 )
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt', 'abc/file1.txt', 'abc/file2.txt'], ['abc/file3.txt', 'abc/file4.txt', 'abc/file5.txt'] ]))
    
    groups, indexes = groupPathsByDir( paths, wish_groups = 2, max_group_size = 1 )
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt'], ['abc/file1.txt'], ['abc/file2.txt'], ['abc/file3.txt'], ['abc/file4.txt'], ['abc/file5.txt'] ]))
    
    groups, indexes = groupPathsByDir( paths, wish_groups = 1 )
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt', 'abc/file1.txt', 'abc/file2.txt', 'abc/file3.txt', 'abc/file4.txt', 'abc/file5.txt'] ]))
    
    paths = ['abc/file0.txt', 'abc/file1.txt', 'abc/file2.txt', 'abc/file3.txt', 'abc/file4.txt', 'abc/file5.txt', 'abc/file6.txt' ]
    groups, indexes = groupPathsByDir( paths, wish_groups = 3 )
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt', 'abc/file1.txt'], ['abc/file2.txt', 'abc/file3.txt'], ['abc/file4.txt', 'abc/file5.txt', 'abc/file6.txt'] ]))
    
    groups, indexes = groupPathsByDir( paths, wish_groups = 3, max_group_size = 2 )
    self.assertEqual( groups, _normPaths([ ['abc/file0.txt', 'abc/file1.txt'], ['abc/file2.txt', 'abc/file3.txt'], ['abc/file4.txt', 'abc/file5.txt'], ['abc/file6.txt'] ]))
    
  #//===========================================================================//
  
  def   test_find_prog( self ):
    self.assertTrue( whereProgram( 'route' ) )
    self.assertRaises( ErrorProgramNotFound, whereProgram, 'route', env = {} )
    
    self.assertTrue( findOptionalProgram( 'route' ) )
    
    prog = findOptionalProgram( 'route', env = {} )
    self.assertEqual( prog.get(), 'route' )
    
    self.assertEqual( len(findOptionalPrograms( ['route'] )), 1 )
    
    progs = findOptionalPrograms( ['route'], env = {} )
    self.assertEqual( progs[0].get(), 'route' )
  
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
