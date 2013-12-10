import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempfile, Tempdir, finishHandleEvents, whereProgram
from aql.util_types import FilePath
from aql.values import FileValue, FileContentChecksum, ValuesFile
from aql.nodes import Node, BuildManager
from aql.options import builtinOptions

from gcc import GccCompiler, GccArchiver, ToolGccCommon

#//===========================================================================//

class TestToolGcc( AqlTestCase ):
  
  #//-------------------------------------------------------//
  
  @classmethod
  def   tearDownClass( cls ):
    finishHandleEvents()
  
  #//-------------------------------------------------------//

  def   _buildObj(self, obj, vfile ):
    pre_nodes = obj.builder.prebuild( vfile, obj )
    self.assertTrue( pre_nodes )

    for node in pre_nodes:
      builder = node.builder
      self.assertFalse( builder.actual( vfile, node ) )
      builder.build( node )
      builder.save( vfile, node )

    obj.builder.prebuildFinished( vfile, obj, pre_nodes )

    self.assertTrue( obj.builder.actual( vfile, obj ) )
    self.assertFalse( obj.builder.prebuild( vfile, obj ) )

  #//-------------------------------------------------------//

  def test_gcc_compiler(self):
    
    with Tempdir() as tmp_dir:
      
      root_dir = FilePath(tmp_dir)
      build_dir = root_dir.join('build')
      
      src_dir   = root_dir.join('src')
      os.makedirs( src_dir )
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', 5 )

      options = builtinOptions()
      options.merge( ToolGccCommon.options() )
      
      if not options.cxx:
        options.cxx = whereProgram( "g++" )

      options.build_dir = build_dir
      
      cpp_compiler = GccCompiler( options, 'c++', shared = False )
      
      vfilename = Tempfile( dir = root_dir, suffix = '.aql.values' ).name
      
      vfile = ValuesFile( vfilename )
      
      try:
        obj = Node( cpp_compiler, src_files )

        self._buildObj( obj, vfile )

        vfile.close(); vfile.open( vfilename )
        
        obj = Node( cpp_compiler, src_files )

        self.assertTrue( obj.builder.actual( vfile, obj ) )
        self.assertFalse( obj.builder.prebuild( vfile, obj ) )
        
        vfile.close(); vfile.open( vfilename )
        
        with open( hdr_files[0], 'a' ) as f:
          f.write("// end of file")
        
        FileValue( hdr_files[0], use_cache = False )
        
        obj = Node( cpp_compiler, src_files )
        self.assertEqual( len(obj.builder.prebuild( vfile, obj )), 1 )

        self._buildObj( obj, vfile )

        vfile.close(); vfile.open( vfilename )
        
        obj = Node( cpp_compiler, src_files )

        self.assertTrue( obj.builder.actual( vfile, obj ) )
        self.assertFalse( obj.builder.prebuild( vfile, obj ) )
        
      finally:
        vfile.close()
  
  #//-------------------------------------------------------//
  
  def test_gcc_compiler_bm(self):
    
    with Tempdir() as tmp_dir:
      
      root_dir = FilePath(tmp_dir)
      build_dir = root_dir.join('build')
      
      src_dir   = root_dir.join('src')
      os.makedirs( src_dir )
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', 5 )

      options = builtinOptions()
      options.merge( ToolGccCommon.options() )

      if not options.cxx:
        options.cxx = whereProgram( "g++" )

      options.build_dir = build_dir
      
      cpp_compiler = GccCompiler( options, 'c++', shared = False )
      
      bm = BuildManager()
      try:
        
        obj = Node( cpp_compiler, src_files )

        bm.add( obj )
        bm.build( jobs = 4, keep_going = False )
        
        bm.close()
        
        obj = Node( cpp_compiler, src_files )

        with open( hdr_files[0], 'a' ) as f:
          f.write("// end of file")
        
        FileValue( hdr_files[0], use_cache = False )
        
        bm = BuildManager()
        obj = Node( cpp_compiler, src_files )
        bm.add( obj )
        bm.build( jobs = 4, keep_going = False )
        
        obj = Node( cpp_compiler, src_files )

      finally:
        bm.close()
  
  #//-------------------------------------------------------//

  @skip
  def test_gcc_ar(self):
    
    #~ with Tempdir() as tmp_dir:
      tmp_dir = Tempdir()
      
      root_dir = FilePath(tmp_dir)
      build_dir = root_dir.join('build')
      
      src_dir   = root_dir.join('src')
      os.makedirs( src_dir )
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', 5 )
      
      options = builtinOptions()
      options.merge( ToolGccCommon.options() )
      
      options.cxx = "C:\\MinGW32\\bin\\g++.exe"
      options.lib = "C:\\MinGW32\\bin\\ar.exe"
      
      options.build_dir_prefix = build_dir
      
      cpp_compiler = GccCompiler( options, 'c++' )
      archiver = GccArchiver( 'foo', options )
      
      vfilename = Tempfile( dir = root_dir, suffix = '.aql.values' ).name
      
      bm = BuildManager( vfilename, 4, True )
      vfile = ValuesFile( vfilename )
      try:
        
        obj = Node( cpp_compiler, src_files )
        lib = Node( archiver, obj )
        self.assertFalse( obj.actual( vfile ) )
        
        bm.add( obj )
        bm.add( lib )
        bm.build()
        
        bm.close()
        
        obj = Node( cpp_compiler, src_files )
        self.assertTrue( obj.actual( vfile ) )
        lib = Node( archiver, obj )
        self.assertTrue( lib.actual( vfile ) )
        
        with open( hdr_files[0], 'a' ) as f:
          f.write("// end of file")
        
        FileValue( hdr_files[0], use_cache = False )
        
        bm = BuildManager( vfilename, 4, True )
        obj = Node( cpp_compiler, src_files )
        lib = Node( archiver, obj )
        bm.add( obj )
        bm.add( lib )
        bm.build()
        
        obj = Node( cpp_compiler, src_files )
        self.assertTrue( obj.actual( vfile ) )
        
        lib = Node( archiver, obj )
        self.assertTrue( lib.actual( vfile ) )
        
      finally:
        vfile.close()
        bm.close()
  
#//===========================================================================//

@skip
class TestToolGccSpeed( AqlTestCase ):

  def test_gcc_compiler_speed(self):
    
    root_dir = FilePath("D:\\build_bench")
    build_dir = root_dir.join('build')
    
    #//-------------------------------------------------------//
    
    options = builtinOptions()
    options.merge( ToolGccCommon.options() )
    
    options.cxx = "C:\\MinGW32\\bin\\g++.exe"
    
    options.build_dir_prefix = build_dir
    
    cpp_compiler = GccCompiler( options, 'c++' )
  
    #//-------------------------------------------------------//
    
    vfilename = root_dir.join( '.aql.values' )
    
    bm = BuildManager( vfilename, 4, True )
    
    options.cpppath += root_dir
    
    for i in range(200):
      src_files = [root_dir + '/lib_%d/class_%d.cpp' % (i, j) for j in range(20)]
      obj = Node( cpp_compiler, src_files, src_content_type = FileContentChecksum, target_content_type = FileContentChecksum )
      bm.add( obj )
    
    #~ for i in range(200):
      #~ src_files = [root_dir + '/lib_%d/class_%d.cpp' % (i, j) for j in range(20)]
      #~ for src_file in src_files:
        #~ obj = Node( cpp_compiler, [ FileValue( src_file, FileContentType ) ] )
        #~ bm.addNodes( obj )
    
    bm.build()
    

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
