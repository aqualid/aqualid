import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.values import FileChecksumValue
from aql.utils import Tempdir, removeUserHandler, addUserHandler, enableDefaultHandlers
from aql.main import Project, ProjectConfig

import msvc

#//===========================================================================//

def   _build( prj ):
  if not prj.Build( verbose = True, jobs = 1):
    prj.build_manager.printFails()
    assert False, "Build failed"

#//===========================================================================//

class TestToolMsvc( AqlTestCase ):
  
  #//-------------------------------------------------------//
  
  # noinspection PyUnusedLocal
  def   eventNodeBuildingFinished( self, node, builder_output, progress, brief ):
    self.built_nodes += 1
  
  #//-------------------------------------------------------//
  
  def   setUp( self ):
    super(TestToolMsvc,self).setUp()
    # disableDefaultHandlers()
    
    self.built_nodes = 0
    addUserHandler( self.eventNodeBuildingFinished )
  
  #//-------------------------------------------------------//
  
  def   tearDown( self ):
    removeUserHandler( self.eventNodeBuildingFinished )

    enableDefaultHandlers()
    
    super(TestToolMsvc,self).tearDown()
  
  #//-------------------------------------------------------//
  
  def   test_msvc_compiler(self):
    with Tempdir() as tmp_dir:
      
      build_dir = os.path.join( tmp_dir, 'output')
      src_dir = os.path.join( tmp_dir, 'src')
      
      os.makedirs( src_dir )
      
      num_src_files = 5
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', num_src_files )
      
      cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir] )
      
      prj = Project( cfg.options, cfg.targets )
      
      cpp = prj.tools.cpp
      
      cpp.Compile( src_files )
      _build( prj )
      self.assertEqual( self.built_nodes, num_src_files )
      
      self.built_nodes = 0
      cpp.Compile( src_files )
      _build( prj )
      self.assertEqual( self.built_nodes, 0 )
      
      with open( hdr_files[0], 'a' ) as f:
        f.write("// end of file")
      
      FileChecksumValue( hdr_files[0], use_cache = False )
      
      self.built_nodes = 0
      cpp.Compile( src_files )
      _build( prj )
      self.assertEqual( self.built_nodes, 1 )
  
  #//-------------------------------------------------------//
  
  def   test_msvc_archiver(self):
    with Tempdir() as tmp_dir:
      
      build_dir = os.path.join( tmp_dir, 'output')
      src_dir = os.path.join( tmp_dir, 'src')
      
      os.makedirs( src_dir )
      
      num_src_files = 5
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', num_src_files )
      
      cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir] )
      
      prj = Project( cfg.options, cfg.targets )
      
      cpp = prj.tools.cpp
      
      cpp.LinkLibrary( src_files, target = 'foo' )
      _build( prj )
      self.assertEqual( self.built_nodes, num_src_files + 1)
      
      self.built_nodes = 0
      cpp.LinkLibrary( src_files, target = 'foo' )
      _build( prj )
      self.assertEqual( self.built_nodes, 0 )
      
      with open( hdr_files[0], 'a' ) as f:
        f.write("// end of file")
      
      FileChecksumValue( hdr_files[0], use_cache = False )
      
      self.built_nodes = 0
      cpp.LinkLibrary( src_files, target = 'foo' )
      _build( prj )
      self.assertEqual( self.built_nodes, 1 )
  #//-------------------------------------------------------//
  
  def   test_msvc_linker(self):
    with Tempdir() as tmp_dir:
      
      build_dir = os.path.join( tmp_dir, 'output')
      src_dir = os.path.join( tmp_dir, 'src')
      
      os.makedirs( src_dir )
      
      num_src_files = 5
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', num_src_files )
      main_src_file = self.generateMainCppFile( src_dir, 'main')
      
      cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir] )
      
      prj = Project( cfg.options, cfg.targets )
      
      cpp = prj.tools.cpp
      
      cpp.LinkSharedLibrary( src_files, target = 'foo' )
      cpp.LinkProgram( src_files, main_src_file, target = 'foo' )
      _build( prj )
      self.assertEqual( self.built_nodes, num_src_files + 1)
      
      self.built_nodes = 0
      cpp.LinkSharedLibrary( src_files, target = 'foo' )
      _build( prj )
      self.assertEqual( self.built_nodes, 0 )
      
      with open( hdr_files[0], 'a' ) as f:
        f.write("// end of file")
      
      FileChecksumValue( hdr_files[0], use_cache = False )
      
      self.built_nodes = 0
      cpp.LinkSharedLibrary( src_files, target = 'foo' )
      _build( prj )
      self.assertEqual( self.built_nodes, 1 )
      
#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
