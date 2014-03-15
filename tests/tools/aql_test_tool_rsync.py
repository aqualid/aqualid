import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempfile, Tempdir
from aql.values import ValuesFile
from aql.nodes import Node, BuildManager
from aql.options import builtinOptions

from aql.main import Project, ProjectConfig

from rsync import RSyncPullBuilder

#//===========================================================================//

@skip
class TestToolRsync( AqlTestCase ):
  
  def test_rsync_pull(self):
    with Tempdir() as tmp_dir:
      with Tempdir() as src_dir:
        with Tempdir() as target_dir:
          src_files = self.generateCppFiles( src_dir.path, "src_test", 10 )
          
          cfg = ProjectConfig( args = [ "build_dir=%s" % tmp_dir] )
          
          prj = Project( cfg.options, cfg.targets )
          
          prj.tools.rsync.Push( src_files, target = target_dir )
          prj.Build()
  
  #//=======================================================//
    
  def test_rsync_get(self):
    
    with Tempdir() as tmp_dir:
      
      options = builtinOptions()
      options.update( rsyncOptions() )
      
      options.env['PATH'] += r"C:\cygwin\bin"
      options.rsync_cygwin = True
      
      rsync = RSyncGetBuilder( options, local_path = 'D:\\test1_local\\', remote_path = 'D:\\test1\\' )
      
      vfilename = Tempfile( dir = str(tmp_dir), suffix = '.aql.values' ).name
      
      bm = BuildManager( vfilename, 4, True )
      vfile = ValuesFile( vfilename )
      try:
        rsync_files = Node( rsync, [] )
        self.assertFalse( rsync_files.isActual( vfile ) )
        
        bm.add( rsync_files )
        bm.build()
        
        rsync_files = Node( rsync, [] )
        self.assertTrue( rsync_files.isActual( vfile ) )
      
      finally:
        vfile.close()
        bm.close()
  
  #//-------------------------------------------------------//
  
  def test_rsync_put(self):
    
    with Tempdir() as tmp_dir:
      
      options = builtinOptions()
      options.update( rsyncOptions() )
      
      options.env['PATH'] += r"C:\cygwin\bin"
      options.rsync_cygwin = True
      
      rsync = RSyncPutBuilder( options, local_path = 'D:\\test1_local\\', remote_path = 'D:\\test1\\', exclude = [".svn", "test_*"] )
      
      vfilename = Tempfile( dir = str(tmp_dir), suffix = '.aql.values' ).name
      
      bm = BuildManager( vfilename, 4, True )
      vfile = ValuesFile( vfilename )
      try:
        rsync_files = Node( rsync, [] )
        self.assertFalse( rsync_files.isActual( vfile ) )
        
        bm.add( rsync_files )
        bm.build()
        
        rsync_files = Node( rsync, [] )
        self.assertTrue( rsync_files.isActual( vfile ) )
        
        sync_files  = [ r'd:\test1_local\sbe\sbe\list\list.hpp',
                        r'd:\test1_local\sbe\sbe\path_finder\path_finder.hpp',
                      ]
        
        rsync_files = Node( rsync, sync_files )
        self.assertFalse( rsync_files.isActual( vfile ) )
        bm.add( rsync_files )
        bm.build()
        
        rsync_files = Node( rsync, sync_files )
        self.assertTrue( rsync_files.isActual( vfile ) )
        bm.add( rsync_files )
        bm.build()
      
      finally:
        vfile.close()
        bm.close()

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
