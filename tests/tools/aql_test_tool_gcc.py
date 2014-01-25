import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempfile, Tempdir, whereProgram, \
    removeUserHandler, addUserHandler, disableDefaultHandlers, enableDefaultHandlers

from aql.util_types import FilePath
from aql.values import FileValue, FileContentChecksum, ValuesFile
from aql.nodes import Node, BuildManager, BuildSplitter
from aql.options import builtinOptions

from gcc import GccCompiler, GccArchiver, GccLinker, ToolGccCommon

#//===========================================================================//

class TestToolGcc( AqlTestCase ):
  
  #//-------------------------------------------------------//
  
  # noinspection PyUnusedLocal
  def   eventNodeBuildingFinished( self, node, out, brief ):
    self.built_nodes += 1
  
  #//-------------------------------------------------------//
  
  def   setUp( self ):
    # disableDefaultHandlers()
    
    self.built_nodes = 0
    addUserHandler( self.eventNodeBuildingFinished, "eventNodeBuildingFinished" )
  
  #//-------------------------------------------------------//
  
  def   tearDown( self ):
    removeUserHandler( self.eventNodeBuildingFinished )

    enableDefaultHandlers()
  
  #//-------------------------------------------------------//

  def   _buildObj(self, obj, vfile ):
    obj.initiate()
    
    pre_nodes = obj.builder.prebuild( obj )
    self.assertTrue( pre_nodes )

    for node in pre_nodes:
      node.initiate()
      builder = node.builder
      if not builder.actual( vfile, node ):
        builder.build( node )
        builder.save( vfile, node )

    obj.builder.prebuildFinished( obj, pre_nodes )
    
    self._verifyActual( obj, vfile )
  
  #//-------------------------------------------------------//
  
  def   _verifyActual(self, obj, vfile, num_of_unactuals = 0 ):
    obj.initiate()
    
    actual = True
    
    for node in obj.builder.prebuild( obj ):
      node.initiate()
      if not node.builder.actual( vfile, node ):
        num_of_unactuals -= 1
        actual = False
    
    if actual:
      self.assertTrue( obj.builder.actual( vfile, obj ))
    
    self.assertEqual( num_of_unactuals, 0 )
    
  #//-------------------------------------------------------//

  def test_gcc_compiler(self):
    
    with Tempdir() as tmp_dir:
      
      root_dir = FilePath(tmp_dir)
      build_dir = root_dir.join('build')
      
      src_dir   = root_dir.join('src')
      os.makedirs( src_dir )
      
      num_src_files = 5
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', num_src_files )

      options = builtinOptions()
      options.merge( ToolGccCommon.options() )
      
      if not options.cxx:
        options.cxx = whereProgram( "g++" )

      options.build_dir = build_dir
      
      cpp_compiler = BuildSplitter( options, GccCompiler( options, 'c++', shared = False ) )
      
      vfilename = Tempfile( dir = root_dir, suffix = '.aql.values' ).name
      
      vfile = ValuesFile( vfilename )
      
      try:
        obj = Node( cpp_compiler, src_files )
        
        self._buildObj( obj, vfile )
        
        vfile.close(); vfile.open( vfilename )
        
        obj = Node( cpp_compiler, src_files )
        self._verifyActual( obj, vfile )
        
        vfile.close(); vfile.open( vfilename )
        
        with open( hdr_files[0], 'a' ) as f:
          f.write("// end of file")
        
        FileValue( hdr_files[0], use_cache = False )
        
        obj = Node( cpp_compiler, src_files )
        self._verifyActual( obj, vfile, 1 )

        self._buildObj( obj, vfile )

        vfile.close(); vfile.open( vfilename )
        
        obj = Node( cpp_compiler, src_files )
        
        self._verifyActual( obj, vfile )
      finally:
        vfile.close()
  
  #//-------------------------------------------------------//
  
  def test_gcc_compiler_bm(self):
    
    with Tempdir() as tmp_dir:
      
      root_dir = FilePath(tmp_dir)
      build_dir = root_dir.join('build')
      
      src_dir   = root_dir.join('src')
      os.makedirs( src_dir )
      
      num_src_files = 5
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', num_src_files )

      options = builtinOptions()
      options.merge( ToolGccCommon.options() )

      if not options.cxx:
        options.cxx = whereProgram( "g++" )

      options.build_dir = build_dir
      
      cpp_compiler = BuildSplitter(options, GccCompiler( options, 'c++', shared = False ) )
      
      bm = BuildManager()
      try:
        
        obj = Node( cpp_compiler, src_files )

        bm.add( obj )
        
        self.built_nodes = 0
        
        bm.build( jobs = 4, keep_going = False )
        
        self.assertEqual( self.built_nodes, num_src_files )
        
        bm.close()
        
        with open( hdr_files[0], 'a' ) as f:
          f.write("// end of file")
        
        FileValue( hdr_files[0], use_cache = False )
        
        bm = BuildManager()
        obj = Node( cpp_compiler, src_files )
        bm.add( obj )
        
        self.built_nodes = 0
        bm.build( jobs = 4, keep_going = False )
        
        self.assertEqual( self.built_nodes, 1 )
        
      finally:
        bm.close()
  
  #//-------------------------------------------------------//

  def test_gcc_ar(self):
    
    with Tempdir() as tmp_dir:
      
      root_dir = FilePath(tmp_dir)
      build_dir = root_dir.join('build')
      
      src_dir   = root_dir.join('src')
      os.makedirs( src_dir )
      
      num_src_files = 5
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', num_src_files )
      
      options = builtinOptions()
      options.merge( ToolGccCommon.options() )
      
      if not options.cxx:
        options.cxx = whereProgram( "g++" )
      
      if not options.lib:
        options.lib = whereProgram( "ar" )
      
      options.build_dir = build_dir
      
      cpp_compiler = BuildSplitter( options, GccCompiler( options, 'c++', shared = False ) )
      archiver = GccArchiver( options, target = 'foo' )
      
      bm = BuildManager()
      try:
        obj = Node( cpp_compiler, src_files )
        lib = Node( archiver, obj )
        
        bm.add( lib )
        
        self.built_nodes = 0
        bm.build( jobs = 1, keep_going = False)
        self.assertEqual( self.built_nodes, num_src_files + 1 )
        
        bm.close()
        
        with open( hdr_files[0], 'a' ) as f:
          f.write("// end of file")
        
        FileValue( hdr_files[0], use_cache = False )
        
        bm = BuildManager()
        obj = Node( cpp_compiler, src_files )
        lib = Node( archiver, obj )
        bm.add( obj )
        bm.add( lib )
        
        self.built_nodes = 0
        bm.build( jobs = 4, keep_going = False)
        self.assertEqual( self.built_nodes, 1 )
        
      finally:
        bm.close()
  
  #//-------------------------------------------------------//
  
  def test_gcc_link(self):
    
    with Tempdir() as tmp_dir:
      
      root_dir = FilePath(tmp_dir)
      build_dir = root_dir.join('build')
      
      src_dir   = root_dir.join('src')
      os.makedirs( src_dir )
      
      num_src_files = 5
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', num_src_files )
      
      main_src_file = self.generateMainCppFile( src_dir, 'main')
      
      options = builtinOptions()
      options.merge( ToolGccCommon.options() )
      
      if not options.cxx:
        options.cxx = whereProgram( "g++" )
      
      if not options.lib:
        options.lib = whereProgram( "ar" )
      
      options.build_dir = build_dir
      
      cpp_compiler = BuildSplitter( options, GccCompiler( options, 'c++', shared = False ) )
      archiver = GccArchiver( options, target = 'foo' )
      linker = GccLinker( options, target = 'main_foo', language = 'c++', shared = False )
      
      bm = BuildManager()
      try:
        obj = Node( cpp_compiler, src_files )
        main_obj = Node( cpp_compiler, main_src_file )
        foo_lib = Node( archiver, obj )
        foo_prog = Node( linker, [ foo_lib, main_obj ] )
        
        bm.add( foo_prog )
        
        self.built_nodes = 0
        bm.build( jobs = 1, keep_going = False)
        self.assertEqual( self.built_nodes, num_src_files + 3 )
        
        bm.close()
        
        obj = Node( cpp_compiler, src_files )
        lib = Node( archiver, obj )
        
        with open( hdr_files[0], 'a' ) as f:
          f.write("// end of file")
        
        FileValue( hdr_files[0], use_cache = False )
        
        bm = BuildManager()
        obj = Node( cpp_compiler, src_files )
        main_obj = Node( cpp_compiler, main_src_file )
        foo_lib = Node( archiver, obj )
        foo_prog = Node( linker, [ foo_lib, main_obj ] )
        
        bm.add( foo_prog )
        
        self.built_nodes = 0
        bm.build( jobs = 1, keep_going = False)
        self.assertEqual( self.built_nodes, 1 )
        
      finally:
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
    
    cpp_compiler = BuildSplitter( options, GccCompiler( options, 'c++' ) )
  
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
