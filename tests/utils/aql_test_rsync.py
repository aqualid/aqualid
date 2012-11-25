import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests
from aql_temp_file import Tempdir

from aql_rsync import Rsync, RemotePathMapping

#//===========================================================================//

class TestRsync( AqlTestCase ):
  
  #//-------------------------------------------------------//
  
  @skip
  def test_rsync_path_map(self):
    
    with Tempdir() as tmp_dir:
      tmp_dir = str(tmp_dir)
      
      mapping = RemotePathMapping( { tmp_dir : '/work/bar//',
                                     tmp_dir : '/work/src/foo//'},
                                    remote_path_sep = '/', local_path_sep = os.path.sep, cygwin_paths = False )
      
      rpath = '/work/src/foo/lib1/foo1.cpp'
      lpath = os.path.join( tmp_dir, 'lib0', 'main.cpp' )
      self.assertEqual( mapping.remotePath( mapping.localPath( rpath ) ), rpath )
      self.assertEqual( mapping.remotePath( mapping.localPath( '/work/tmp/../src/foo/lib1/foo1.cpp' ) ), rpath )
      self.assertEqual( mapping.localPath( mapping.remotePath( lpath ) ), lpath )
      self.assertEqual( mapping.localPath( mapping.remotePath( tmp_dir ) ), tmp_dir + '\\' )
      self.assertEqual( mapping.remotePath( tmp_dir ), '/work/src/foo/' )
      self.assertEqual( mapping.localPath( '/work/src/foo' ), tmp_dir + '\\' )
      
      mapping = RemotePathMapping()
      
      mapping.add( tmp_dir + '/src/bar/', '/work/src/bar/')
      mapping.add( tmp_dir + '/src/tools/', '/work/src/tools/')
      mapping.add( tmp_dir + '/src/bar/', '/work/src/tools/')
      
      rpath = '/work/src/tools/lib1/foo1.cpp'
      self.assertEqual( mapping.remotePath( mapping.localPath( rpath ) ), rpath )
      self.assertEqual( mapping.localPath( '/work/src/bar' ), '' )
      self.assertEqual( mapping.remotePath( tmp_dir + '/src/tools' ), '' )
      self.assertEqual( mapping.localPath( '/work/src/tools1' ), '' )
      
      mapping = RemotePathMapping( (( tmp_dir, '/work/bar//'),
                                    ( tmp_dir + '/foo', '/work/src/foo/')) )
      
      rpath = '/work/src/foo/lib1/foo1.cpp'
      self.assertEqual( mapping.localPath( rpath ), os.path.join( tmp_dir, 'foo','lib1','foo1.cpp' ) )
      
      mapping = RemotePathMapping( (( tmp_dir, '/work/bar//'),
                                    ( tmp_dir + '/foo', '/work/src/foo/')),
                                   cygwin_paths = True
                                 )
      
      rpath = '/work/src/foo/lib1/foo1.cpp'
      tmp_drive, tmp_path = os.path.splitdrive( tmp_dir )
      if tmp_drive:
        tmp_drive = '/cygdrive/' + tmp_drive[0].lower()
      
      self.assertEqual( mapping.localPath( rpath ), tmp_drive + tmp_path.replace('\\', '/') + '/foo/lib1/foo1.cpp' )
  
  #//-------------------------------------------------------//
  
  @skip
  def   test_rsync(self):
    env = os.environ.copy()
    env['PATH'] = 'C:\\cygwin\\bin' + os.pathsep + env['PATH']
    
    #~ host = RemoteHost( address = 'nas', login = 'me', key_file = r"C:\work\settings\keys\nas.key" )
    #~ path_map = RemotePathMapping( {'/cygdrive/d/build_bench100k': '/home/me/work/build_bench100k/lib_0' } )
    host = None
    #~ path_map = RemotePathMapping( {'/cygdrive/d/test1': '/cygdrive/d/test1_backup' } )
    #~ path_map = RemotePathMapping( {'D:\\test1\\': 'd:\\test1_backup\\' }, cygwin_paths = True )
    
    sync = Rsync( rsync = None, host = host, cygwin_paths = True, env = env )
    #~ sync.syncRemote( '/cygdrive/d/test1', exclude = ['.svn'] )
    #~ sync.syncLocal( '/cygdrive/d/test1_backup', exclude = ['.svn'] )
    #~ sync.get( 'd:\\test1\\', 'd:\\test1_backup\\', exclude = ['.svn', '*.txt'] )
    #~ sync.put( 'D:/test1/',  'd:\\test1_backup\\' )
    sync.put( 'D:/test1/',  'd:\\test1_backup\\',
              local_files = ['D:\\test1\\sbe\\sbe\\allocators\\fixed_allocator.hpp',
                             r'/sbe\tests\allocators\test_fixed_allocator.cpp'] )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
