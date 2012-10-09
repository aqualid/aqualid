import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_utils import findProgram
from aql_temp_file import Tempfile, Tempdir
from aql_path_types import FilePath, FilePaths
from aql_file_value import FileValue, FileContentTimeStamp, FileContentChecksum
from aql_values_file import ValuesFile
from aql_node import Node
from aql_build_manager import BuildManager
from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_builtin_options import builtinOptions

from rsync import Rsync, rsyncOptions, RemotePathMapping

#//===========================================================================//

class TestToolRsync( AqlTestCase ):
  
  @classmethod
  def   setUpClass( cls ):
    event_manager.setHandlers( EventHandler() )
  
  #//-------------------------------------------------------//
  
  def test_rsync_path_map(self):
    
    with Tempdir() as tmp_dir:
      tmp_dir = str(tmp_dir)
      
      mapping = RemotePathMapping( { tmp_dir : '/work/bar//',
                                     tmp_dir : '/work/src/foo//'} )
      
      rpath = '/work/src/foo/lib1/foo1.cpp'
      lpath = os.path.join( tmp_dir, 'lib0', 'main.cpp' )
      self.assertEqual( mapping.remotePath( mapping.localPath( rpath ) ), rpath )
      self.assertEqual( mapping.remotePath( mapping.localPath( '/work/tmp/../src/foo/lib1/foo1.cpp' ) ), rpath )
      self.assertEqual( mapping.localPath( mapping.remotePath( lpath ) ), lpath )
      
      mapping = RemotePathMapping()
      
      mapping.add( tmp_dir + '/src/bar', '/work/src/bar/')
      mapping.add( tmp_dir + '/src/tools', '/work/src/tools/')
      mapping.add( tmp_dir + '/src/bar', '/work/src/tools')
      
      rpath = '/work/src/tools/lib1/foo1.cpp'
      self.assertEqual( mapping.remotePath( mapping.localPath( rpath ) ), rpath )
      self.assertEqual( mapping.localPath( '/work/src/bar' ), '' )
      self.assertEqual( mapping.remotePath( tmp_dir + '/src/tools' ), '' )
      self.assertEqual( mapping.localPath( '/work/src/tools1' ), '' )
      
      mapping = RemotePathMapping( (( tmp_dir, '/work/bar//'),
                                    ( tmp_dir + '/foo', '/work/src/foo/')) )
      
      rpath = '/work/src/foo/lib1/foo1.cpp'
      self.assertEqual( mapping.localPath( rpath ), os.path.join( tmp_dir, 'foo','lib1','foo1.cpp' ) )
  
  #//-------------------------------------------------------//
 
  def test_rsync(self):
    env = os.environ.copy()
    env['PATH'] = 'C:\\cygwin\\bin' + os.pathsep + env['PATH']
    
    rsync = findProgram( 'rsync', env )
    self.assertTrue( rsync )
    
    #~ host = RemoteHost( address = 'nas', login = 'me', key_file = r"C:\work\settings\keys\nas.key" )
    #~ path_map = RemotePathMapping( {'/cygdrive/d/build_bench100k': '/home/me/work/build_bench100k/lib_0' } )
    host = None
    #~ path_map = RemotePathMapping( {'/cygdrive/d/test1': '/cygdrive/d/test1_backup' } )
    path_map = RemotePathMapping( {'D:/test1': '/cygdrive/d/test1_backup' } )
    
    sync = Rsync( rsync = rsync, host = host, path_map = path_map, env = env )
    #~ sync.syncRemote( '/cygdrive/d/test1', exclude = ['.svn'] )
    #~ sync.syncLocal( '/cygdrive/d/test1_backup', exclude = ['.svn'] )
    sync.syncRemote( 'D:/test1', exclude = ['.svn'] )
    sync.syncLocal( '/cygdrive/d/test1_backup', exclude = ['.svn'] )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
