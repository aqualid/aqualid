import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import AqlTestCase, runLocalTests

from aql.utils import Tempdir, whereProgram, \
    removeUserHandler, addUserHandler, disableDefaultHandlers, enableDefaultHandlers
from aql.util_types import FilePath
from aql.nodes import Node, BuildManager
from aql.options import builtinOptions

from aql.main import ExecuteCommand, InstallBuilder

#//===========================================================================//

class TestBuiltinTools( AqlTestCase ):
  
  #//-------------------------------------------------------//

  # noinspection PyUnusedLocal
  def   eventNodeBuilding( self, node, brief ):
    self.building_started += 1
  
  #//-------------------------------------------------------//
  
  # noinspection PyUnusedLocal
  def   eventNodeBuildingFinished( self, node, builder_output, progress, brief ):
    self.building_finished += 1
  
  #//-------------------------------------------------------//
  
  def   setUp( self ):
    super(TestBuiltinTools,self).setUp()
    # disableDefaultHandlers()
    
    self.building_started = 0
    addUserHandler( self.eventNodeBuilding )
    
    self.building_finished = 0
    addUserHandler( self.eventNodeBuildingFinished )
  
  #//-------------------------------------------------------//
  
  def   tearDown( self ):
    removeUserHandler( self.eventNodeBuilding )
    removeUserHandler( self.eventNodeBuildingFinished )

    enableDefaultHandlers()
  
  #//-------------------------------------------------------//

  def   _build(self, bm, **kw ):
    is_ok = bm.build( **kw )
    if not is_ok:
      bm.printFails()

    self.assertTrue( is_ok )

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
        
        self._build( bm, jobs = 1, keep_going = False )
        
        self.assertEqual( self.building_started, 1 )
        self.assertEqual( self.building_started, self.building_finished )
        
        bm.close()
        
        result = Node( exec_cmd, cmd )

        bm = BuildManager()
        bm.add( result )
        
        self.building_started = 0
        self._build( bm, jobs = 1, keep_going = False )
        
        self.assertEqual( self.building_started, 0 )
        
      finally:
        bm.close()
  
  #//-------------------------------------------------------//

  def test_install(self):
    
    with Tempdir() as tmp_install_dir:
      with Tempdir() as tmp_dir:
        # tmp_install_dir = Tempdir()
        # tmp_dir = Tempdir()
        
        build_dir = os.path.join( tmp_dir, 'output' )
        
        options = builtinOptions()
  
        options.build_dir = build_dir
        
        num_sources = 3
        
        sources = self.generateSourceFiles( tmp_dir, num_sources, 200 )
        
        installer = InstallBuilder( options, str(tmp_install_dir) )
        
        bm = BuildManager()
        try:
          
          result = Node( installer, sources )
  
          bm.add( result )
          
          self._build( bm, jobs = 1, keep_going = False, brief = False )
          
          self.assertEqual( self.building_started, 1 )
          self.assertEqual( self.building_started, self.building_finished )
          
          bm.close()
          
          result = Node( installer, sources )
  
          bm = BuildManager()
          bm.add( result )
          
          self.building_started = 0
          self._build( bm, jobs = 1, keep_going = False )
          
          self.assertEqual( self.building_started, 0 )
          
        finally:
          bm.close()

  
  #//-------------------------------------------------------//

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
