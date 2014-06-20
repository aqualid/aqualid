import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempfile, Tempdir, whereProgram, \
    removeUserHandler, addUserHandler, disableDefaultHandlers, enableDefaultHandlers

from aql.util_types import FilePath
from aql.values import FileChecksumValue, ValuesFile
from aql.nodes import Node, BuildManager, BuildSingle
from aql.options import builtinOptions

from gcc import GccCompiler, GccArchiver, GccLinker, ToolGxx, ToolGcc

#//===========================================================================//

class TestToolGcc( AqlTestCase ):
  
  #//-------------------------------------------------------//
  
  # noinspection PyUnusedLocal
  def   eventNodeBuildingFinished( self, node, builder_output, progress, brief ):
    self.built_nodes += 1
  
  #//-------------------------------------------------------//
  
  def   setUp( self ):
    super(TestToolGcc,self).setUp()
    # disableDefaultHandlers()
    
    self.built_nodes = 0
    addUserHandler( self.eventNodeBuildingFinished )
  
  #//-------------------------------------------------------//
  
  def   tearDown( self ):
    removeUserHandler( self.eventNodeBuildingFinished )

    enableDefaultHandlers()
    
    super(TestToolGcc,self).tearDown()
  
  #//-------------------------------------------------------//

  def   _buildObj(self, obj, vfile ):
    obj.initiate()
    
    pre_nodes = obj.prebuild()
    self.assertTrue( pre_nodes )

    for node in pre_nodes:
      node.initiate()
      if not node.isActual( vfile ):
        node.build()
        node.save( vfile )
    
    if pre_nodes:
      actual = obj.prebuildFinished( pre_nodes )
      self.assertTrue( actual )
    else:
      self._verifyActual( obj, vfile )
  
  #//-------------------------------------------------------//
  
  def   _verifyActual(self, obj, vfile, num_of_unactuals = 0 ):
    obj.initiate()
    
    actual = True
    
    pre_nodes = obj.prebuild()
    
    for node in pre_nodes:
      node.initiate()
      if not node.isActual( vfile ):
        num_of_unactuals -= 1
        actual = False
    
    if actual:
      if pre_nodes:
        actual = obj.prebuildFinished( pre_nodes )
      else:
        actual = obj.isActual( vfile )
      
      self.assertTrue( actual )
    
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
      options.merge( ToolGxx.options() )
      env = options.env.get().dump()
      ToolGxx.setup( options, env )

      options.build_dir = build_dir
      
      gcc = ToolGxx( options )
      cpp_compiler = gcc.Compile( options )
      
      vfilename = Tempfile( dir = root_dir, suffix = '.aql.values' )
      vfilename.close()

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
        
        FileChecksumValue( hdr_files[0], use_cache = False )
        
        obj = Node( cpp_compiler, src_files )
        self._verifyActual( obj, vfile, 1 )

        self._buildObj( obj, vfile )

        vfile.close(); vfile.open( vfilename )
        
        obj = Node( cpp_compiler, src_files )
        
        self._verifyActual( obj, vfile )
      finally:
        vfile.close()
  
  #//-------------------------------------------------------//
  
  def   _build( self, bm, **kw ):

    kw.setdefault('jobs', 1 )
    kw.setdefault('keep_going', False )
    kw.setdefault('brief', False )

    is_ok = bm.build( **kw )
    bm.printFails()
    self.assertTrue( is_ok )
  
  #//-------------------------------------------------------//
  
  def test_gcc_compiler_bm(self):
    
    with Tempdir() as tmp_dir:
      
      root_dir = FilePath(tmp_dir)
      build_dir = root_dir.join('build')
      
      src_dir   = root_dir.join('src')
      os.makedirs( src_dir )
      
      num_src_files = 5
      
      src_files, hdr_files = self.generateCppFiles( src_dir, 'foo', num_src_files )
      res_file = self.generateResFile( src_dir, 'foo' )
      
      options = builtinOptions()
      options.merge( ToolGxx.options() )
      env = options.env.get().dump()
      ToolGxx.setup( options, env )

      options.build_dir = build_dir
      
      gcc = ToolGxx( options )
      cpp_compiler = gcc.Compile( options )
      res_compiler = gcc.CompileResource( options )
      
      bm = BuildManager()
      try:
        
        obj = Node( cpp_compiler, src_files )
        res = Node( res_compiler, res_file )
        
        bm.add( obj )
        bm.add( res )
        
        self.built_nodes = 0
        
        self._build( bm, jobs = 4 )
        
        self.assertEqual( self.built_nodes, num_src_files + 1 )
        
        bm.close()
        
        with open( hdr_files[0], 'a' ) as f:
          f.write("// end of file")
        
        FileChecksumValue( hdr_files[0], use_cache = False )
        
        bm = BuildManager()
        obj = Node( cpp_compiler, src_files )
        res = Node( res_compiler, res_file )
        bm.add( obj )
        bm.add( res )
        
        self.built_nodes = 0
        self._build( bm )
        
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
      options.merge( ToolGxx.options() )
      env = options.env.get().dump()
      ToolGxx.setup( options, env )
      
      options.build_dir = build_dir
      
      gcc = ToolGxx( options )
      cpp_compiler = gcc.Compile( options )
      archiver = gcc.LinkLibrary( options, target = 'foo' )
      
      bm = BuildManager()
      try:
        obj = Node( cpp_compiler, src_files )
        lib = Node( archiver, obj )
        
        bm.add( lib )
        
        self.built_nodes = 0
        self._build( bm )
        self.assertEqual( self.built_nodes, num_src_files + 1 )
        
        bm.close()
        
        with open( hdr_files[0], 'a' ) as f:
          f.write("// end of file")
        
        FileChecksumValue( hdr_files[0], use_cache = False )
        
        bm = BuildManager()
        obj = Node( cpp_compiler, src_files )
        lib = Node( archiver, obj )
        bm.add( obj )
        bm.add( lib )
        
        self.built_nodes = 0
        self._build( bm )
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
      options.merge( ToolGxx.options() )
      env = options.env.get().dump()
      ToolGxx.setup( options, env )

      options.build_dir = build_dir
      
      gcc = ToolGxx( options )
      cpp_compiler = gcc.Compile( options )
      archiver = gcc.LinkLibrary( options, target = 'foo' )
      linker = gcc.LinkProgram( options, target = 'foo' )
      
      bm = BuildManager()
      try:
        obj = Node( cpp_compiler, src_files )
        main_obj = Node( cpp_compiler, main_src_file )
        foo_lib = Node( archiver, obj )
        foo_prog = Node( linker, [ foo_lib, main_obj ] )
        
        bm.add( foo_prog )
        
        self.built_nodes = 0
        self._build( bm )
        self.assertEqual( self.built_nodes, num_src_files + 3 )
        
        bm.close()
        
        obj = Node( cpp_compiler, src_files )
        lib = Node( archiver, obj )
        
        with open( hdr_files[0], 'a' ) as f:
          f.write("// end of file")
        
        FileChecksumValue( hdr_files[0], use_cache = False )
        
        bm = BuildManager()
        obj = Node( cpp_compiler, src_files )
        main_obj = Node( cpp_compiler, main_src_file )
        foo_lib = Node( archiver, obj )
        foo_prog = Node( linker, [ foo_lib, main_obj ] )
        
        bm.add( foo_prog )
        
        self.built_nodes = 0
        self._build( bm )
        self.assertEqual( self.built_nodes, 1 )
        
      finally:
        bm.close()

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
