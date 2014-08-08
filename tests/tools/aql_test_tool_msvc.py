import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.values import FileChecksumValue, FileTimestampValue
from aql.utils import Tempdir, removeUserHandler, addUserHandler, enableDefaultHandlers
from aql.main import Project, ProjectConfig, ErrorToolNotFound

import msvc

#//===========================================================================//

def   _build( prj, verbose = True, jobs = 4 ):
  if not prj.Build( verbose = verbose, jobs = jobs ):
    prj.build_manager.printFails()
    assert False, "Build failed"

#//===========================================================================//

def   _touchFile( cpp_file ):
  with open( cpp_file, 'a' ) as f:
    f.write("// end of file")
  
  FileChecksumValue( cpp_file, use_cache = False )
  FileTimestampValue( cpp_file, use_cache = False )

def   _touchFiles( cpp_files ):
  for cpp_file in cpp_files:
    _touchFile( cpp_file )

#//===========================================================================//

class TestToolMsvc( AqlTestCase ):
  
  def   _build( self, prj, num_built_nodes, verbose = True, jobs = 4 ):
    self.built_nodes = 0
    _build( prj, verbose = verbose, jobs = jobs )
    self.assertEqual( self.built_nodes, num_built_nodes )
  
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
      res_file = self.generateResFile( src_dir, 'foo' )
      
      cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir] )
      
      prj = Project( cfg.options, cfg.targets )
      
      try:
        cpp = prj.tools['msvc++']
      except  ErrorToolNotFound:
        print("WARNING: MSVC tool has not been found. Skip the test.")
        return
      
      cpp.Compile( src_files )
      cpp.CompileResource( res_file )
      
      self._build( prj, num_src_files + 1 )
      
      cpp.Compile( src_files )
      cpp.CompileResource( res_file )
      
      self._build( prj, 0 )
      
      _touchFile( hdr_files[0] )
      
      cpp.Compile( src_files )
      self._build( prj, 1 )
  
  #//-------------------------------------------------------//
  
  def   test_msvc_compiler_batch(self):
    with Tempdir() as tmp_dir:
      
      build_dir = os.path.join( tmp_dir, 'output')
      src_dir = os.path.join( tmp_dir, 'src')
      
      os.makedirs( src_dir )
      
      num_groups = 4
      group_size = 8
      num_src_files = num_groups * group_size
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', num_src_files )
      
      cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir] )
      
      prj = Project( cfg.options, cfg.targets )
      
      try:
        cpp = prj.tools['msvc++']
      except  ErrorToolNotFound:
        print("WARNING: MSVC tool has not been found. Skip the test.")
        return
      
      cpp.Compile( src_files, batch = True )
      self._build( prj, num_groups, jobs = num_groups )
      
      cpp.Compile( src_files, batch = False )
      self._build( prj, 0 )
      
      _touchFile( hdr_files[0] )
      cpp.Compile( src_files, batch = False )
      self._build( prj, 1 )
      
      _touchFiles( hdr_files[:group_size] )
      
      cpp.Compile( src_files, batch = True )
      self._build( prj, 1 )
  
  #//-------------------------------------------------------//
  
  def   test_msvc_archiver(self):
    with Tempdir() as tmp_dir:
      
      build_dir = os.path.join( tmp_dir, 'output')
      src_dir = os.path.join( tmp_dir, 'src')
      
      os.makedirs( src_dir )
      
      num_groups = 4
      group_size = 8
      num_src_files = num_groups * group_size
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', num_src_files )
      res_file = self.generateResFile( src_dir, 'foo' )
      
      cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir] )
      
      prj = Project( cfg.options, cfg.targets )
      
      try:
        cpp = prj.tools['msvc++']
      except  ErrorToolNotFound:
        print("WARNING: MSVC tool has not been found. Skip the test.")
        return
      
      cpp.LinkLibrary( src_files, res_file, target = 'foo' )
      
      self._build( prj, num_src_files + 2 )
      
      cpp.LinkLibrary( src_files, res_file, target = 'foo' )
      self._build( prj, 0 )
      
      _touchFile( hdr_files[0] )
      
      cpp.LinkLibrary( src_files, res_file, target = 'foo' )
      self._build( prj, 1 )
      
      cpp.LinkLibrary( src_files, res_file, target = 'foo', batch = True )
      self._build( prj, 0 )
      
      _touchFiles( hdr_files )
      cpp.LinkLibrary( src_files, res_file, target = 'foo', batch = True )
      self._build( prj, num_groups )
      
      
  #//-------------------------------------------------------//
  
  def   test_msvc_linker(self):
    with Tempdir() as tmp_dir:
      
      build_dir = os.path.join( tmp_dir, 'output')
      src_dir = os.path.join( tmp_dir, 'src')
      
      os.makedirs( src_dir )
      
      num_groups = 4
      group_size = 8
      num_src_files = num_groups * group_size
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', num_src_files )
      res_file = self.generateResFile( src_dir, 'foo' )
      main_src_file = self.generateMainCppFile( src_dir, 'main')
      
      cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir] )
      
      prj = Project( cfg.options, cfg.targets )
      
      try:
        cpp = prj.tools['msvc++']
      except  ErrorToolNotFound:
        print("WARNING: MSVC tool has not been found. Skip the test.")
        return
      
      cpp.LinkSharedLibrary( src_files, res_file, target = 'foo' )
      cpp.LinkSharedLibrary( src_files, res_file, target = 'foo' )
      cpp.LinkProgram( src_files, main_src_file, res_file, target = 'foo' )
      
      self._build( prj, num_src_files + 4 )
      
      cpp.LinkSharedLibrary( src_files, res_file, target = 'foo' )
      cpp.LinkProgram( src_files, main_src_file, res_file, target = 'foo' )
      self._build( prj, 0 )
      
      _touchFile( hdr_files[0] )
      
      cpp.LinkSharedLibrary( src_files, res_file, target = 'foo' )
      cpp.LinkProgram( src_files, main_src_file, res_file, target = 'foo' )
      self._build( prj, 1 )
      
      _touchFiles( hdr_files )
      cpp.LinkSharedLibrary( src_files, res_file, target = 'foo', batch = True )
      cpp.LinkProgram( src_files, main_src_file, res_file, target = 'foo', batch = True )
      self._build( prj, num_groups )
      
#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
