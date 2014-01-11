import sys
import os.path
import types

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.values import Value
from aql.nodes import Node, Builder
from aql.utils import Tempfile, Tempdir,\
  removeUserHandler, addUserHandler, disableDefaultHandlers, enableDefaultHandlers
from aql.main import Project, ProjectConfig, \
                     ErrorProjectBuilderMethodWithKW, \
                     ErrorProjectBuilderMethodFewArguments, \
                     ErrorProjectBuilderMethodUnbound, \
                     ErrorProjectInvalidMethod

#//===========================================================================//

class TestProject( AqlTestCase ):
  
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
  
  def test_prj_config(self):
    
    with Tempfile() as f:
      cfg = b"""
abc = 123
size = 100
keep_going = True
jobs=5
options.build_variant = "final"
"""
      f.write( cfg )
      f.flush()
      
      args = ["-v", "-c", f.name ]
      cfg = ProjectConfig( args )
      
      self.assertEqual( cfg.options.bv, 'final' )
      self.assertEqual( cfg.options.jobs, 5 )
  
  #//-------------------------------------------------------//
  
  @skip
  def   test_prj_add_builder( self ):
    cfg = ProjectConfig( [] )
    prj = Project( cfg )
    
    class TestBuilder (Builder):
      def   __init__(self):
        self.signature = b''
      def   build( self, build_manager, vfile, node ):
        return self.nodeTargets( Value( name = "value1", content = b"" ) )
    
    class TestTool:
      def   TestBuilder( self, prj, options ):
        pass
      
      def   TestBuilder2( self, prj, options, **vals ):
        pass
      
      def   TestBuilder3( self, prj ):
        pass
      
      def   TestBuildNode( self, prj, options, source ):
        return Node( TestBuilder(), '' )
    
    if isinstance( TestTool.TestBuilder, types.MethodType ):
      self.assertRaises( ErrorProjectBuilderMethodUnbound, prj.AddBuilder, TestTool.TestBuilder )
    
    #~ prj.AddBuilder( TestTool().TestBuilder )
    #~ self.assertRaises( ErrorProjectBuilderMethodResultInvalid, prj.TestBuilder )
    
    self.assertRaises( ErrorProjectBuilderMethodWithKW, prj.AddBuilder, TestTool().TestBuilder2 )
    self.assertRaises( ErrorProjectBuilderMethodFewArguments, prj.AddBuilder, TestTool().TestBuilder3 )
    self.assertRaises( ErrorProjectInvalidMethod, prj.AddBuilder, "TestTool().TestBuilder3" )
    
    prj.AddBuilder( TestTool().TestBuildNode )
    node = prj.TestBuildNode( 'a' )
    #~ self.assertRaises( ErrorProjectBuilderMethodResultInvalid, prj.TestBuilder )
  
  #//-------------------------------------------------------//
  
  def   test_prj_builtin_tools( self ):
    
    with Tempdir() as tmp_dir:
      
      cfg = ProjectConfig( args = [ "build_dir=%s" % tmp_dir] )
      
      prj = Project( cfg.options, cfg.targets )
      
      prj.tools.ExecuteCommand( "python", "-c", "print('test builtin')" )
      prj.Build()
      
      self.assertEqual( self.building_started, 1 )
      self.assertEqual( self.building_finished, 1 )
      
      self.building_started = 0
      
      prj = Project( cfg.options, cfg.targets )
      prj.tools.ExecuteCommand( "python", "-c", "print('test builtin')" )
      prj.Build()
      
      self.assertEqual( self.building_started, 0 )
  
  #//-------------------------------------------------------//
  
  def   test_prj_targets( self ):
    
    with Tempdir() as tmp_dir:
      
      cfg = ProjectConfig( args = [ "build_dir=%s" % tmp_dir, "test"] )
      
      prj = Project( cfg.options, cfg.targets )
      
      cmd = prj.tools.ExecuteCommand( "python", "-c", "print('test builtin')" )
      cmd_other = prj.tools.ExecuteCommand( "python", "-c", "print('test other')" )
      
      prj.Alias('test', cmd )
      prj.Build()
      
      self.assertEqual( self.building_finished, 1 )
  
  #//-------------------------------------------------------//
  
  def   test_prj_default_targets( self ):
    
    with Tempdir() as tmp_dir:
      
      cfg = ProjectConfig( args = [ "build_dir=%s" % tmp_dir] )
      
      prj = Project( cfg.options, cfg.targets )
      
      cmd = prj.tools.ExecuteCommand( "python", "-c", "print('test builtin')" )
      cmd_other = prj.tools.ExecuteCommand( "python", "-c", "print('test other')" )
      cmd_other2 = prj.tools.ExecuteCommand( "python", "-c", "print('test other2')" )
      
      prj.Default( [cmd_other, cmd_other2] )
      prj.Build()
      
      self.assertEqual( self.building_finished, 2 )
      
      

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
