import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_utils import findProgram
from aql_temp_file import Tempfile, Tempdir
from aql_file_value import FileValue, DirValue
from aql_values_file import ValuesFile
from aql_node import Node
from aql_build_manager import BuildManager
from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_builtin_options import builtinOptions
from aql_builtin_options import builtinOptions

from rsync import RSyncGetBuilder, RSyncPutBuilder, rsyncOptions

#//===========================================================================//

@skip
class TestToolRsync( AqlTestCase ):
  
  @classmethod
  def   setUpClass( cls ):
    event_manager.setHandlers( EventHandler() )
  
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
        event_manager.finish()
  
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
        event_manager.finish()

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
