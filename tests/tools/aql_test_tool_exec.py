import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempdir, finishHandleEvents, whereProgram
from aql.util_types import FilePath
from aql.nodes import Node, BuildManager
from aql.options import builtinOptions

from exeprog import ExecuteCommand

#//===========================================================================//

class TestToolExec( AqlTestCase ):
  
  #//-------------------------------------------------------//
  
  @classmethod
  def   tearDownClass( cls ):
    finishHandleEvents()
  
  #//-------------------------------------------------------//

  def test_exec(self):
    
    with Tempdir() as tmp_dir:
      
      build_dir = FilePath(tmp_dir).join('build')
      
      options = builtinOptions()

      cmd = [ whereProgram( "python" ), '-c', 'print("TEST EXEC")']

      options.build_dir = build_dir
      
      exec_cmd = ExecuteCommand( options )
      
      bm = BuildManager()
      try:
        
        result = Node( exec_cmd, cmd )

        bm.add( result )
        bm.build( jobs = 4, keep_going = False )
        
        bm.close()
        
        result = Node( exec_cmd, cmd )

        bm = BuildManager()
        bm.add( result )
        bm.build( jobs = 4, keep_going = False )
        
      finally:
        bm.close()
  
  #//-------------------------------------------------------//

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
