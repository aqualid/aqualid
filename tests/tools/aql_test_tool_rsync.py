import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempfile, Tempdir, finishHandleEvents
from aql.values import ValuesFile
from aql.nodes import Node, BuildManager
from aql.options import builtinOptions

from rsync import RSyncGetBuilder, RSyncPutBuilder, rsyncOptions

#//===========================================================================//

@skip
class TestToolRsync( AqlTestCase ):
  
  @classmethod
  def   tearDownClass( cls ):
    finishHandleEvents()
  
  #//-------------------------------------------------------//
  
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
        self.assertFalse( rsync_files.actual( vfile ) )
        
        bm.add( rsync_files )
        bm.build()
        
        rsync_files = Node( rsync, [] )
        self.assertTrue( rsync_files.actual( vfile ) )
      
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
        self.assertFalse( rsync_files.actual( vfile ) )
        
        bm.add( rsync_files )
        bm.build()
        
        rsync_files = Node( rsync, [] )
        self.assertTrue( rsync_files.actual( vfile ) )
        
        sync_files  = [ r'd:\test1_local\sbe\sbe\list\list.hpp',
                        r'd:\test1_local\sbe\sbe\path_finder\path_finder.hpp',
                      ]
        
        rsync_files = Node( rsync, sync_files )
        self.assertFalse( rsync_files.actual( vfile ) )
        bm.add( rsync_files )
        bm.build()
        
        rsync_files = Node( rsync, sync_files )
        self.assertTrue( rsync_files.actual( vfile ) )
        bm.add( rsync_files )
        bm.build()
      
      finally:
        vfile.close()
        bm.close()

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
