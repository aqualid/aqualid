import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempfile, Tempdir

from aql.main import Project, ProjectConfig, ErrorToolNotFound

#//===========================================================================//

class TestToolGcc( AqlTestCase ):
  
  #//-------------------------------------------------------//
  
  def test_gcc_compiler(self):
    
    with Tempdir() as tmp_dir:
      
      build_dir = os.path.join( tmp_dir, 'build' )
      src_dir   = os.path.join( tmp_dir, 'src')
      os.makedirs( src_dir )
      
      num_src_files = 5
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', num_src_files )
      
      cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir] )
      
      prj = Project( cfg )
      try:
        gcc = prj.tools.Tool('g++', tools_path = os.path.join( os.path.dirname(__file__), '../../tools' ))
      except  ErrorToolNotFound:
        print("WARNING: GCC tool has not been found. Skip the test.")
        return
      
      gcc.Compile( src_files, batch_build = False )
      self.buildPrj( prj, num_src_files )
      
      gcc.Compile( src_files, batch_build = False )
      self.buildPrj( prj, 0 )
      
      gcc.Compile( src_files, batch_build = False )
      
      self.touchCppFile( hdr_files[0] )
      self.buildPrj( prj, 1 )
      
      gcc.Compile( src_files, batch_build = False )
      self.buildPrj( prj, 0 )
  
  #//-------------------------------------------------------//
  
  def test_gcc_res_compiler(self):
    
    with Tempdir() as tmp_dir:
      
      build_dir = os.path.join( tmp_dir, 'build' )
      src_dir   = os.path.join( tmp_dir, 'src')
      os.makedirs( src_dir )
      
      num_src_files = 2
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', num_src_files )
      res_file = self.generateResFile( src_dir, 'foo' )
      
      cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir] )
      
      prj = Project( cfg )
      try:
        gcc = prj.tools.Tool('g++', tools_path = os.path.join( os.path.dirname(__file__), '../../tools' ))
      except  ErrorToolNotFound:
        print("WARNING: GCC tool has not been found. Skip the test.")
        return
      try:
        rc = prj.tools.Tool('windres', tools_path = os.path.join( os.path.dirname(__file__), '../../tools' ))
      except  ErrorToolNotFound:
        print("WARNING: Windres tool has not been found. Skip the test.")
        return
      
      gcc.Compile( src_files, batch_build = False )
      rc.Compile( res_file )
      self.buildPrj( prj, num_src_files )
      
      gcc.Compile( src_files, batch_build = False )
      gcc.CompileResource( res_file )
      self.buildPrj( prj, 0 )
      
      gcc.Compile( src_files, batch_build = False )
      rc.Compile( res_file )
      
      self.touchCppFile( res_file )
      self.buildPrj( prj, 1 )
      
      gcc.Compile( src_files, batch_build = False )
      rc.Compile( res_file )
      self.buildPrj( prj, 0 )
      
  
  #//-------------------------------------------------------//
  
  def   test_gcc_archiver(self):
    with Tempdir() as tmp_dir:
      
      build_dir = os.path.join( tmp_dir, 'output')
      src_dir = os.path.join( tmp_dir, 'src')
      
      os.makedirs( src_dir )
      
      num_groups = 4
      group_size = 8
      num_src_files = num_groups * group_size
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', num_src_files )
      
      cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir] )
      
      prj = Project( cfg )
      
      try:
        cpp = prj.tools.Tool('g++', tools_path = os.path.join( os.path.dirname(__file__), '../../tools' ))
      except  ErrorToolNotFound:
        print("WARNING: GCC tool has not been found. Skip the test.")
        return
      
      cpp.LinkLibrary( src_files, target = 'foo', batch_build = False )
      
      self.buildPrj( prj, num_src_files + 1 )
      
      cpp.LinkLibrary( src_files, target = 'foo' )
      self.buildPrj( prj, 0 )
      
      self.touchCppFile( hdr_files[0] )
      
      cpp.LinkLibrary( src_files, target = 'foo' )
      self.buildPrj( prj, 1 )
      
      cpp.LinkLibrary( src_files, target = 'foo', batch_build = False )
      self.buildPrj( prj, 0 )
      
      self.touchCppFiles( hdr_files )
      cpp.LinkLibrary( src_files, target = 'foo', batch_build = False )
      self.buildPrj( prj, num_src_files )
  
  #//-------------------------------------------------------//
  
  def   test_gcc_linker(self):
    with Tempdir() as tmp_dir:
      
      build_dir = os.path.join( tmp_dir, 'output')
      src_dir = os.path.join( tmp_dir, 'src')
      
      os.makedirs( src_dir )
      
      num_groups = 4
      group_size = 8
      num_src_files = num_groups * group_size
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', num_src_files )
      main_src_file = self.generateMainCppFile( src_dir, 'main')
      
      cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir, "batch_build=0"] )
      
      prj = Project( cfg )
      
      try:
        cpp = prj.tools.Tool('g++', tools_path = os.path.join( os.path.dirname(__file__), '../../tools' ))
      except  ErrorToolNotFound:
        print("WARNING: GCC tool has not been found. Skip the test.")
        return
      
      cpp.LinkSharedLibrary( src_files, target = 'foo' )
      cpp.LinkSharedLibrary( src_files, target = 'foo' )
      cpp.LinkProgram( src_files, main_src_file, target = 'foo' )
      
      self.buildPrj( prj, num_src_files + 3 )
      
      cpp.LinkSharedLibrary( src_files, target = 'foo' )
      cpp.LinkProgram( src_files, main_src_file, target = 'foo' )
      self.buildPrj( prj, 0 )
      
      self.touchCppFile( hdr_files[0] )
      
      cpp.LinkSharedLibrary( src_files, target = 'foo' )
      cpp.LinkProgram( src_files, main_src_file, target = 'foo' )
      self.buildPrj( prj, 1 )
      
      self.touchCppFiles( hdr_files )
      cpp.LinkSharedLibrary( src_files, target = 'foo', batch_build = False )
      cpp.LinkProgram( src_files, main_src_file, target = 'foo', batch_build = False )
      self.buildPrj( prj, num_src_files )
  
  #//-------------------------------------------------------//
  
  def   test_gcc_compiler_batch(self):
    with Tempdir() as tmp_dir:
      
      build_dir = os.path.join( tmp_dir, 'output')
      src_dir = os.path.join( tmp_dir, 'src')
      
      os.makedirs( src_dir )
      
      num_groups = 4
      group_size = 8
      num_src_files = num_groups * group_size
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', num_src_files )
      
      cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir] )
      
      prj = Project( cfg )
      
      try:
        cpp = prj.tools.Tool('g++', tools_path = os.path.join( os.path.dirname(__file__), '../../tools' ))
      except  ErrorToolNotFound:
        print("WARNING: g++ tool has not been found. Skip the test.")
        return
      
      cpp.Compile( src_files, batch_build = True )
      self.buildPrj( prj, num_groups, jobs = num_groups )
      
      cpp.Compile( src_files, batch_build = False )
      self.buildPrj( prj, 0 )
      
      self.touchCppFile( hdr_files[0] )
      cpp.Compile( src_files, batch_build = False )
      self.buildPrj( prj, 1 )
      
      self.touchCppFiles( hdr_files[:group_size] )
      
      cpp.Compile( src_files, batch_build = True, batch_groups = num_groups)
      self.buildPrj( prj, num_groups )
  
  #//-------------------------------------------------------//
  
  def   test_gcc_compiler_batch_error(self):
    with Tempdir() as tmp_dir:
      
      build_dir = os.path.join( tmp_dir, 'output')
      src_dir = os.path.join( tmp_dir, 'src')
      
      os.makedirs( src_dir )
      
      num_src_files = 5
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', num_src_files )
      
      src_file_orig = Tempfile( dir = tmp_dir )
      src_file_orig.close()
      
      self.copyFile( src_files[0], src_file_orig )
      
      self.addErrorToCppFile( src_files[0] )
      
      cfg = ProjectConfig( args = [ "build_dir=%s" % build_dir] )
      
      prj = Project( cfg )
      
      try:
        cpp = prj.tools.Tool('g++', tools_path = os.path.join( os.path.dirname(__file__), '../../tools' ))
      except  ErrorToolNotFound:
        print("WARNING: g++ tool has not been found. Skip the test.")
        return
      
      cpp.Compile( src_files, batch_build = True, batch_groups = 1 )
      
      self.buildPrj( prj, 0, num_failed_nodes = 1 )
      
      self.copyFile( src_file_orig, src_files[0] )
      
      cpp.Compile( src_files )
      
      self.buildPrj( prj, 1 )
  
#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
