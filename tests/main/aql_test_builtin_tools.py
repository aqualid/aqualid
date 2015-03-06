import os
import sys
import shutil

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import AqlTestCase, runLocalTests

from aql.utils import Tempdir, removeUserHandler, addUserHandler
from aql.utils import EventSettings, setEventSettings
from aql.nodes import Node, BuildManager
from aql.options import builtinOptions

from aql.main import Project, ProjectConfig
from aql.main.aql_builtin_tools import ExecuteCommandBuilder

#//===========================================================================//

class TestBuiltinTools( AqlTestCase ):
  
  #//-------------------------------------------------------//

  # noinspection PyUnusedLocal
  def   eventNodeBuilding( self, settings, node ):
    self.building_started += 1
  
  #//-------------------------------------------------------//
  
  def   setUp( self ):
    super(TestBuiltinTools,self).setUp()
    # disableDefaultHandlers()
    
    self.building_started = 0
    addUserHandler( self.eventNodeBuilding )
  
  #//-------------------------------------------------------//
  
  def   tearDown( self ):
    removeUserHandler( self.eventNodeBuilding )

    super(TestBuiltinTools, self).tearDown()
  
  #//-------------------------------------------------------//

  def   _build(self, bm, **kw ):
    is_ok = bm.build( **kw )
    if not is_ok:
      bm.printFails()

    self.assertTrue( is_ok )

  #//-------------------------------------------------------//

  def test_exec(self):
    
    with Tempdir() as tmp_dir:
      
      build_dir = os.path.join(tmp_dir, 'build')
      
      options = builtinOptions()

      cmd = [ sys.executable, '-c', 'print("TEST EXEC")']

      options.build_dir = build_dir
      
      exec_cmd = ExecuteCommandBuilder( options )
      
      bm = BuildManager()
      try:
        
        result = Node( exec_cmd, cmd )

        bm.add( [result] )
        
        self._build( bm, jobs = 1, keep_going = False )
        
        self.assertEqual( self.building_started, 1 )
        self.assertEqual( self.building_started, self.built_nodes )
        
        bm.close()
        
        result = Node( exec_cmd, cmd )

        bm = BuildManager()
        bm.add( [result] )
        
        self.building_started = 0
        self._build( bm, jobs = 1, keep_going = False )
        
        self.assertEqual( self.building_started, 0 )
        
      finally:
        bm.close()
  
  #//-------------------------------------------------------//

  def test_copy_files(self):
    
    with Tempdir() as tmp_install_dir:
      with Tempdir() as tmp_dir:
        # tmp_install_dir = Tempdir()
        # tmp_dir = Tempdir()
        
        build_dir = os.path.join( tmp_dir, 'output' )
        
        num_sources = 3
        sources = self.generateSourceFiles( tmp_dir, num_sources, 200 )
        
        cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir] )
        
        prj = Project( cfg )
        
        node = prj.tools.CopyFiles( sources, target = tmp_install_dir )
        
        node.options.batch_groups = 1
        
        self.buildPrj( prj, 1 )
        
        prj.tools.CopyFiles( sources, target = tmp_install_dir )
        
        self.buildPrj( prj, 0 )
  
  #//-------------------------------------------------------//

  def test_exec_method(self):
    
    def   CopyFileExt( builder, source_entities, targets, ext ):
      src_file = source_entities[0].get()
      dst_file = os.path.splitext(src_file)[0] + ext
      shutil.copy( src_file, dst_file )
      targets.add( dst_file )
    
    with Tempdir() as tmp_dir:
      
      setEventSettings( EventSettings( brief = True, with_output = True, trace_exec = False ) )
      
      build_dir = os.path.join( tmp_dir, 'build_output' )
      
      num_sources = 2
      sources, headers = self.generateCppFiles( tmp_dir, 'test_method_', num_sources )
      
      cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir] )
      
      prj = Project( cfg )
      
      prj.tools.ExecuteMethod( sources, method = CopyFileExt, args = ('.cxx',) )
      prj.tools.ExecuteMethod( headers, method = CopyFileExt, args = ('.hxx',) )
      
      self.buildPrj( prj, len(sources) + len(headers) )
      
      prj.tools.ExecuteMethod( sources, method = CopyFileExt, args = ('.cxx',) )
      prj.tools.ExecuteMethod( headers, method = CopyFileExt, args = ('.hxx',) )
      
      self.buildPrj( prj, 0 )
      
      prj.tools.ExecuteMethod( sources, method = CopyFileExt, args = ('.cc',) )
      self.buildPrj( prj, len(sources) )
      
      prj.tools.ExecuteMethod( sources, method = CopyFileExt, args = ('.cxx',) )
      self.buildPrj( prj, len(sources) )
      
      #//-------------------------------------------------------//
      
      for src in sources:
        self.assertTrue( os.path.isfile( os.path.splitext(src)[0] + '.cxx') )
      
      prj.tools.ExecuteMethod( sources, method = CopyFileExt, args = ('.cxx',) )
      self.clearPrj( prj )
      
      for src in sources:
        self.assertFalse( os.path.isfile( os.path.splitext(src)[0] + '.cxx') )
      
      #//-------------------------------------------------------//
      
      prj.tools.ExecuteMethod( sources, method = CopyFileExt, args = ('.cxx',) )
      self.buildPrj( prj, len(sources) )
      
      for src in sources:
        self.assertTrue( os.path.isfile( os.path.splitext(src)[0] + '.cxx') )
        
      prj.tools.ExecuteMethod( sources, method = CopyFileExt, args = ('.cxx',), clear_targets = False )
      self.clearPrj( prj )
      
      for src in sources:
        self.assertTrue( os.path.isfile( os.path.splitext(src)[0] + '.cxx') )
      
  
  #//-------------------------------------------------------//

  def   test_node_filter_dirname(self):
    
    with Tempdir() as tmp_install_dir:
      with Tempdir() as tmp_dir:
        
        build_dir = os.path.join( tmp_dir, 'output' )
        
        num_sources = 3
        sources = self.generateSourceFiles( tmp_dir, num_sources, 200 )
        
        # setEventSettings( EventSettings( brief = False, with_output = True ) )
        
        cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir] )
        cfg.debug_backtrace = True
        
        prj = Project( cfg )
        
        node = prj.tools.CopyFiles( sources[0], target = tmp_install_dir )
        
        prj.tools.CopyFiles( sources[1:], target = prj.DirName( node ) )
        
        self.buildPrj( prj, 3 )
        
        for src in sources:
          tgt = os.path.join( tmp_install_dir, os.path.basename( src ) )
          self.assertTrue( os.path.isfile( tgt ) )
        
        node = prj.tools.CopyFiles( sources[0], target = tmp_install_dir )
        prj.tools.CopyFiles( sources[1:], target = prj.DirName( node ) )
        
        self.buildPrj( prj, 0 )
  
  #//-------------------------------------------------------//

  def   test_copy_file_as(self):
    
    with Tempdir() as tmp_install_dir:
      with Tempdir() as tmp_dir:
        # tmp_install_dir = Tempdir()
        # tmp_dir = Tempdir()
        
        build_dir = os.path.join( tmp_dir, 'output' )
        
        source = self.generateFile( tmp_dir, 0, 200 )
        target = os.path.join( tmp_install_dir, 'copy_as_source.dat' )
        
        cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir] )
        
        prj = Project( cfg )
        
        prj.tools.CopyFileAs( source, target = target )
        
        self.buildPrj( prj, 1 )
        
        prj.tools.CopyFileAs( source, target = target )
        
        self.buildPrj( prj, 0 )
  
  #//-------------------------------------------------------//

  def   test_write_file(self):
    
    with Tempdir() as tmp_install_dir:
      with Tempdir() as tmp_dir:
        # tmp_install_dir = Tempdir()
        # tmp_dir = Tempdir()
        
        build_dir = os.path.join( tmp_dir, 'output' )
        
        cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir] )
        
        prj = Project( cfg )
        
        buf = "Test buffer content"
        
        target = os.path.join( tmp_install_dir, 'write_content.txt' )
        prj.tools.WriteFile( buf, target = target )
        
        self.buildPrj( prj, 1 )
        
        prj.tools.WriteFile( buf, target = target )
        
        self.buildPrj( prj, 0 )
  
  #//-------------------------------------------------------//

  def test_zip_files(self):
    
    with Tempdir() as tmp_install_dir:
      with Tempdir() as tmp_dir:
        # tmp_install_dir = Tempdir()
        # tmp_dir = Tempdir()
        
        build_dir = os.path.join( tmp_dir, 'output' )
        
        num_sources = 3
        sources = self.generateSourceFiles( tmp_dir, num_sources, 200 )
        
        zip_file = tmp_install_dir + "/test.zip"
        
        cfg = ProjectConfig( args = [ "--bt", "build_dir=%s" % build_dir] )
        
        prj = Project( cfg )
        
        value = prj.Entity( "test_content.txt", "To add to a ZIP file")
        rename = [('test_file', sources[0])]
        
        prj.tools.CreateZip( sources, value, target = zip_file, rename = rename )
        
        self.buildPrj( prj, 1 )
        
        prj.tools.CreateZip( sources, value, target = zip_file, rename = rename )
        
        self.buildPrj( prj, 0 )
        
        self.touchCppFile( sources[-1] )
        
        prj.tools.CreateZip( sources, value, target = zip_file, rename = rename )
        self.buildPrj( prj, 1 )

        
#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
