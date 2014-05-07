import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempdir
from aql.main import Project, ProjectConfig

import rsync

#//===========================================================================//

def   _build( prj ):
  if not prj.Build( verbose = True ):
    prj.build_manager.printFails()
    assert False, "Build failed"

#//===========================================================================//

class TestToolRsync( AqlTestCase ):
  
  def test_rsync_push_local(self):
    with Tempdir() as tmp_dir:
      with Tempdir() as src_dir:
        with Tempdir() as target_dir:
          src_files = self.generateCppFiles( src_dir, "src_test", 3 )
          
          cfg = ProjectConfig( args = [ "build_dir=%s" % tmp_dir] )
          
          prj = Project( cfg.options, cfg.targets )
          
          prj.tools.rsync.Push( src_files, target = target_dir )
          
          _build( prj )
          
          prj.tools.rsync.Push( src_files, target = target_dir )
          
          _build( prj )
  
  #//=======================================================//

  @skip
  def test_rsync_push_remote(self):
    with Tempdir() as tmp_dir:
      with Tempdir() as src_dir:
        src_files = self.generateCppFiles( src_dir, "src_test", 3 )

        cfg = ProjectConfig( args = [ "build_dir=%s" % tmp_dir] )

        prj = Project( cfg.options, cfg.targets )

        remote_files = prj.tools.rsync.Push( src_dir + '/', target = 'test_rsync_push/',
                                             host = 'nas', key_file = r'C:\cygwin\home\me\rsync.key',
                                             exclude="*.h" )
        remote_files.options.rsync_flags += ['--chmod=u+xrw,g+xr,o+xr']
        remote_files.options.rsync_flags += ['--delete-excluded']
        _build( prj )

  #//=======================================================//

  def test_rsync_pull(self):
    with Tempdir() as tmp_dir:
      with Tempdir() as src_dir:
        with Tempdir() as target_dir:
          src_files = self.generateCppFiles( src_dir, "src_test", 3 )
          
          cfg = ProjectConfig( args = [ "build_dir=%s" % tmp_dir] )
          
          prj = Project( cfg.options, cfg.targets )
          
          prj.tools.rsync.Pull( src_files, target = target_dir )
          
          _build( prj )
          
          prj.tools.rsync.Pull( src_files, target = target_dir )
          
          _build( prj )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
