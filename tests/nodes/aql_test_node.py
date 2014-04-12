import sys
import os.path
import timeit
import shutil
import hashlib

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))
from aql_tests import skip, AqlTestCase, runLocalTests

from aql.util_types import toSequence
from aql.utils import Tempfile, Tempdir, writeBinFile, disableDefaultHandlers, enableDefaultHandlers
from aql.options import builtinOptions
from aql.values import SimpleValue, NullValue, FileChecksumValue, ValuesFile
from aql.nodes import Node, BatchNode, Builder, FileBuilder


#//===========================================================================//

def   _splitNodes( items ):
  nodes = []
  values = []
  for item in toSequence( items ):
    if isinstance( item, Node ):
      nodes.append( item )
    else:
      values.append( item )
  
  return nodes, values

#//===========================================================================//

class ChecksumBuilder (Builder):
  
  #//-------------------------------------------------------//
  
  def   __init__(self, options ):
    self.signature = b''
  
  def   build( self, node ):
    target_values = []
    itarget_values = []
    
    for source_value in node.getSourceValues():
      content = source_value.data.encode()
      chcksum = hashlib.md5()
      chcksum.update( content )
      chcksum_sha512 = hashlib.sha512()
      chcksum_sha512.update( content )
      target_values.append( chcksum.digest() )
      itarget_values.append( chcksum_sha512.digest() )
    
    node.setTargets( target_values, itarget_values )

#//===========================================================================//

class CopyBuilder (FileBuilder):
  
  SIGNATURE_ATTRS = ('ext', 'iext')
  
  def   __init__(self, options, ext, iext ):
    self.ext = ext
    self.iext = iext
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    target_values = []
    itarget_values = []
    
    idep = SimpleValue( b'1234' )
    
    for src in node.getSources():
      new_name = src + '.' + self.ext
      new_iname = src + '.' + self.iext
      
      shutil.copy( src, new_name )
      shutil.copy( src, new_iname )
      
      target_values.append( new_name )
      itarget_values.append( new_iname )
    
    node.setFileTargets( target_values, itarget_values, idep )
  
  #//-------------------------------------------------------//
  
  def   buildBatch( self, node ):
    
    idep = SimpleValue( b'1234' )
    
    for src_value in node.getSourceValues():
      src = src_value.get()
      
      new_name = src + '.' + self.ext
      new_iname = src + '.' + self.iext
      
      shutil.copy( src, new_name )
      shutil.copy( src, new_iname )
      
      node.setSourceFileTargets( src_value, new_name, new_iname, idep )

#//===========================================================================//

class TestNodes( AqlTestCase ):
  
  def   setUp( self ):
    super(TestNodes,self).setUp()
    # disableDefaultHandlers()
  
  def   tearDown( self ):
    enableDefaultHandlers()
    super(TestNodes,self).tearDown()
  
  def test_node_value(self):
    
    with Tempfile() as tmp:
      
      vfile = ValuesFile( tmp )
      try:
        value1 = SimpleValue( "http://aql.org/download1", name = "target_url1" )
        value2 = SimpleValue( "http://aql.org/download2", name = "target_url2" )
        value3 = SimpleValue( "http://aql.org/download3", name = "target_url3" )
        
        options = builtinOptions()
        builder = ChecksumBuilder( options )
        
        node = Node( builder, [value1, value2, value3] )
        node.initiate()
        
        self.assertFalse( node.isActual( vfile ) )
        node.build()
        node.save( vfile )
        self.assertTrue( node.isActual( vfile ) )
        
        node = Node( builder, [value1, value2, value3] )
        node.initiate()
        
        self.assertTrue( node.isActual( vfile ) )
        node.build()
        node.save( vfile )
        self.assertTrue( node.isActual( vfile ) )
        
        node = Node( builder, [value1, value2, value3] )
        node.depends( NullValue() )
        node.initiate()
        
        self.assertFalse( node.isActual( vfile ) )
        node.build()
        node.save( vfile )
        self.assertFalse( node.isActual( vfile ) )
      
      finally:
        vfile.close()

  #//===========================================================================//

  def   _rebuildNode( self, vfile, builder, values, deps, tmp_files):
    node = Node( builder, values )
    node.depends( deps )
    
    node.initiate()
    
    self.assertFalse( node.isActual( vfile ) )
    node.build()
    node.save( vfile )
    self.assertTrue( node.isActual( vfile ) )
    
    node = Node( builder, values )
    node.depends( deps )
    
    node.initiate()
    
    self.assertTrue( node.isActual( vfile ) )
    node.build()
    node.save( vfile )
    self.assertTrue( node.isActual( vfile ) )
    
    for tmp_file in node.getTargetValues():
      tmp_files.append( tmp_file.name )
    
    for tmp_file in node.getSideEffectValues():
      tmp_files.append( tmp_file.name )
    
    return node

  #//=======================================================//

  def test_node_file(self):
    
    try:
      tmp_files = []
      
      with Tempfile() as tmp:
        
        vfile = ValuesFile( tmp )
        try:
          with Tempfile( suffix = '.1' ) as tmp1:
            with Tempfile( suffix = '.2' ) as tmp2:
              value1 = FileChecksumValue( tmp1 )
              value2 = FileChecksumValue( tmp2 )
              
              options = builtinOptions()
              
              builder = CopyBuilder( options, "tmp", "i")
              node = self._rebuildNode( vfile, builder, [value1, value2], [], tmp_files )
              
              builder = CopyBuilder( options, "ttt", "i")
              node = self._rebuildNode( vfile, builder, [value1, value2], [], tmp_files )
              
              builder = CopyBuilder( options, "ttt", "d")
              node = self._rebuildNode( vfile, builder, [value1, value2], [], tmp_files )
              
              tmp1.write(b'123')
              tmp1.flush()
              value1 = FileChecksumValue( tmp1 )
              node = self._rebuildNode( vfile, builder, [value1, value2], [], tmp_files )
              
              with Tempfile( suffix = '.3' ) as tmp3:
                value3 = FileChecksumValue( tmp3 )
                
                node3 = self._rebuildNode( vfile, builder, [value3], [], tmp_files )
                
                node = self._rebuildNode( vfile, builder, [value1, node3], [], tmp_files )
                
                # node3: CopyBuilder, tmp, i, tmp3 -> tmp3.tmp, ,tmp3.i
                # node: CopyBuilder, tmp, i, tmp1, tmp3.tmp -> tmp1.tmp, tmp3.tmp.tmp, , tmp1.i, tmp3.tmp.i
                
                builder3 = CopyBuilder( options, "xxx", "3")
                node3 = self._rebuildNode( vfile, builder3, [value3], [], tmp_files )
                
                # node3: CopyBuilder, xxx, 3, tmp3 -> tmp3.xxx, ,tmp3.3
                
                node = self._rebuildNode( vfile, builder, [value1, node3], [], tmp_files )
                
                # node: CopyBuilder, tmp, i, tmp1, tmp3.xxx -> tmp1.tmp, tmp3.xxx.tmp, , tmp1.i, tmp3.xxx.i
                
                node = self._rebuildNode( vfile, builder, [value1], [node3], tmp_files )
                
                dep = SimpleValue( "1", name = "dep1" )
                node = self._rebuildNode( vfile, builder, [value1, node3], [dep], tmp_files )
                
                dep = SimpleValue( "11", name = "dep1" )
                node = self._rebuildNode( vfile, builder, [value1, node3], [dep], tmp_files )
                node3 = self._rebuildNode( vfile, builder3, [value1], [], tmp_files )
                node = self._rebuildNode( vfile, builder, [value1], [node3], tmp_files )
                node3 = self._rebuildNode( vfile, builder3, [value2], [], tmp_files )
                node = self._rebuildNode( vfile, builder, [value1], [node3], tmp_files )
                
                node_tname = node.getTargetValues()[0].name
                
                with open( node_tname, 'wb' ) as f:
                  f.write( b'333' )
                  f.flush()
                
                FileChecksumValue( node_tname, use_cache = False )
                
                node = self._rebuildNode( vfile, builder, [value1], [node3], tmp_files )
                
                with open( node.getSideEffectValues()[0].name, 'wb' ) as f:
                  f.write( b'abc' )
                  f.flush()
                
                FileChecksumValue( node.getSideEffectValues()[0].name, use_cache = False )
                
                node = Node( builder, [value1] )
                node.depends( [node3] )
                node.initiate()
                
                self.assertTrue( node.isActual( vfile ) )
                # node = self._rebuildNode( vfile, builder, [value1], [node3], tmp_files )
        finally:
          vfile.close()
    finally:
      for tmp_file in tmp_files:
        try:
          os.remove( tmp_file )
        except OSError:
          pass
  
  #//=======================================================//
  
  def   _rebuildBatchNode(self, vfile, src_files, built_count ):
    options = builtinOptions()
    
    builder = CopyBuilder( options, "tmp", "i" )
    
    node = BatchNode( builder, src_files )
    dep = SimpleValue( "11", name = "dep1" )
    node.depends( dep )
    
    node.initiate()
    
    if built_count == 0:
      self.assertTrue( node.isActual( vfile ) )
    else:
      self.assertFalse( node.isActual( vfile ) )
      node.build()
      node.save( vfile )
      self.assertEqual( len(node.batch_source_values), built_count )
      self.assertTrue( node.isActual( vfile ) )
  
  #//=======================================================//
  
  def test_node_batch(self):
    
    with Tempdir() as tmp_dir:
      vfile_name = Tempfile( dir = tmp_dir )
      with ValuesFile( vfile_name ) as vfile:
        src_files = self.generateSourceFiles( tmp_dir, 5, 100 )
        
        self._rebuildBatchNode( vfile, src_files, len(src_files) )
        self._rebuildBatchNode( vfile, src_files, 0 )
        self._rebuildBatchNode( vfile, src_files[:-2], 0 )
        self._rebuildBatchNode( vfile, src_files[0:1], 0 )
        
        #//-------------------------------------------------------//
        
        writeBinFile( src_files[1], b"src_file1" )
        writeBinFile( src_files[2], b"src_file1" )
        FileChecksumValue( src_files[1] )   # clear cached value
        FileChecksumValue( src_files[2] )   # clear cached value
        
        self._rebuildBatchNode( vfile, src_files, 2 )

#//===========================================================================//

_FileValueType = FileChecksumValue

class TestSpeedBuilder (Builder):
  
  __slots__ = ('ext', 'idep')
  
  def   __init__(self, options, name, ext, idep ):
    self.name = name
    self.ext = ext
    self.idep = idep
    self.signature = str(ext + '|' + idep).encode('utf-8')
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    target_values = []
    itarget_values = []
    idep_values = []
    
    for source_value in node.getSourceValues():
      new_name = source_value.name + '.' + self.ext
      idep_name = source_value.name + '.' + self.idep
      
      shutil.copy( source_value.name, new_name )
      
      target_values.append( _FileValueType( new_name ) )
      idep_values.append( _FileValueType( idep_name ) )
    
    node.setTargets( target_values, itarget_values, idep_values )
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    return ' '.join( self.name )

#//===========================================================================//

def   _testNoBuildSpeed( vfile, builder, source_values ):
  for source in source_values:
    node = Node( builder, _FileValueType( source ) )
    node.initiate()
    if not node.isActual( vfile ):
      raise AssertionError( "node is not actual" )

def   _generateFiles( tmp_files, number, size ):
  content = b'1' * size
  files = []
  for i in range( 0, number ):
    t = Tempfile()
    tmp_files.append( t )
    t.write( content )
    files.append( t )
  
  return files

def   _copyFiles( tmp_files, files, ext ):
  copied_files= []
  
  for f in files:
    name = f + '.' + ext
    shutil.copy( f, f + '.' + ext )
    tmp_files.append( name )
    copied_files.append( name )
  
  return copied_files

@skip
class TestNodesSpeed ( AqlTestCase ):
  def test_node_speed( self ):
    
    try:
      tmp_files = []
      
      source_files = _generateFiles( tmp_files, 4000, 50 * 1024 )
      idep_files = _copyFiles( tmp_files, source_files, 'h' )
      
      with Tempfile() as tmp:
        
        vfile = ValuesFile( tmp )
        try:
          builder = TestSpeedBuilder("TestSpeedBuilder", "tmp", "h")
          
          for source in source_files:
            node = Node( builder, _FileValueType( source ) )
            node.initiate()
            self.assertFalse( node.isActual( vfile ) )
            builder.build( node )
            builder.save( vfile, node )
            for tmp_file in node.target_values:
              tmp_files.append( tmp_file.name )
          
          t = lambda vfile = vfile, builder = builder, source_files = source_files, testNoBuildSpeed = _testNoBuildSpeed: testNoBuildSpeed( vfile, builder, source_files )
          t = timeit.timeit( t, number = 1 )
        finally:
          vfile.close()
    
    finally:
      for tmp_file in tmp_files:
        try:
          os.remove( tmp_file )
        except OSError:
          pass

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
