import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_build_path import BuildPathMapper


#//===========================================================================//

class TestBuildPath( AqlTestCase ):
  
  #//---------------------------------------------------------------------------//
  
  def test_build_path(self):
    
    build_dir_prefix = 'c:/a/b/d'
    build_dir_suffix = ''
    build_dir_name = 'windows_x86-32_release'
    
    path_mapper = BuildPathMapper( build_dir_prefix, build_dir_name, build_dir_suffix )
    
    self.assertEqual( path_mapper.getBuildPath( 'c:/a/b/d/src/foo.cpp'),
                      os.path.normpath( os.path.join( build_dir_prefix, build_dir_name, 'src', 'foo.cpp' ) ) )
    
    self.assertEqual( path_mapper.getBuildPath( 'c:/a/b/d/src/foo/foo.cpp'),
                      os.path.normpath( os.path.join( build_dir_prefix, build_dir_name, 'src', 'foo', 'foo.cpp' ) ) )
    
    self.assertEqual( path_mapper.getBuildPath( 'c:/a/src/foo/foo.cpp'),
                      os.path.normpath( os.path.join( build_dir_prefix, build_dir_name, 'src', 'foo', 'foo.cpp' ) ) )
    
    self.assertEqual( path_mapper.getBuildPath( 'd:/a/src/foo/foo.cpp'),
                      os.path.normpath( os.path.join( build_dir_prefix, build_dir_name, 'd', 'a', 'src', 'foo', 'foo.cpp' ) ) )
    
    self.assertEqual( path_mapper.getBuildPath( '//host/project_1/src/foo/foo.cpp'),
                      os.path.normpath( os.path.join( build_dir_prefix, build_dir_name, 'host', 'project_1', 'src', 'foo', 'foo.cpp' ) ) )
    
    build_dir_suffix = 'k/l/m'
    
    path_mapper = BuildPathMapper( build_dir_prefix, build_dir_name, build_dir_suffix )
    
    self.assertEqual( path_mapper.getBuildPath( 'c:/a/b/d/src/foo.cpp'),
                      os.path.normpath( os.path.join( build_dir_prefix, build_dir_name, build_dir_suffix, 'foo.cpp' ) ) )
    
    self.assertEqual( path_mapper.getBuildPath( 'c:/a/src/foo/foo.cpp'),
                      os.path.normpath( os.path.join( build_dir_prefix, build_dir_name, build_dir_suffix, 'foo.cpp' ) ) )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
