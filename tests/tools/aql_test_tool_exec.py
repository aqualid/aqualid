import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import AqlTestCase, runLocalTests

from aql.utils import Tempdir, whereProgram,\
    removeUserHandler, addUserHandler, disableDefaultHandlers, enableDefaultHandlers
from aql.util_types import FilePath
from aql.nodes import Node, BuildManager
from aql.options import builtinOptions

from aql.main import ExecuteCommand

#//===========================================================================//

class TestToolExec( AqlTestCase ):
  
  #//-------------------------------------------------------//

  # noinspection PyUnusedLocal
  def   eventNodeBuilding( self, node ):
    self.building_started += 1
  
  #//-------------------------------------------------------//
  
  # noinspection PyUnusedLocal
  def   eventNodeBuildingFinished( self, node ):
    self.building_finished += 1
  
  #//-------------------------------------------------------//
  
  def   setUp( self ):
    disableDefaultHandlers()
    
    self.building_started = 0
    addUserHandler( self.eventNodeBuilding, "eventNodeBuilding" )
    
    self.building_finished = 0
    addUserHandler( self.eventNodeBuildingFinished, "eventNodeBuildingFinished" )
  
  #//-------------------------------------------------------//
  
  def   tearDown( self ):
    removeUserHandler( self.eventNodeBuilding )
    removeUserHandler( self.eventNodeBuildingFinished )

    enableDefaultHandlers()
  
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
        
        bm.build( jobs = 1, keep_going = False )
        
        self.assertEqual( self.building_started, 1 )
        self.assertEqual( self.building_started, self.building_finished )
        
        bm.close()
        
        result = Node( exec_cmd, cmd )

        bm = BuildManager()
        bm.add( result )
        
        self.building_started = 0
        bm.build( jobs = 1, keep_going = False )
        
        self.assertEqual( self.building_started, 0 )
        
      finally:
        bm.close()
  
  #//-------------------------------------------------------//

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
