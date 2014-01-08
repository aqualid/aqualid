import sys
import os.path
import timeit
import shutil
import hashlib

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))
from aql_tests import skip, AqlTestCase, runLocalTests

from aql.util_types import toSequence
from aql.utils import Tempfile, disableDefaultHandlers, enableDefaultHandlers
from aql.options import builtinOptions
from aql.values import StringValue, Value, FileValue, FileContentChecksum, ValuesFile
from aql.nodes import Node, Builder


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
    
    for source_value in node.sourceValues():
      content = source_value.content.data.encode()
      chcksum = hashlib.md5()
      chcksum.update( content )
      chcksum_sha512 = hashlib.sha512()
      chcksum_sha512.update( content )
      target_values.append( chcksum.digest() )
      itarget_values.append( chcksum_sha512.digest() )
    
    node.setTargets( target_values, itarget_values )

#//===========================================================================//

class CopyBuilder (Builder):
  
  __slots__ = ('ext', 'iext')
  
  def   __init__(self, options, ext, iext ):
    self.ext = ext
    self.iext = iext
    self.signature = str(ext + '|' + iext).encode('utf-8')
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    target_values = []
    itarget_values = []
    idep_values = []
    
    idep = self.makeValue( b'' )
    
    for src in node.sources():
      new_name = src + '.' + self.ext
      new_iname = src + '.' + self.iext
      
      shutil.copy( src, new_name )
      shutil.copy( src, new_iname )
      
      target_values.append( new_name )
      itarget_values.append( new_iname )
    
    node.setFileTargets( target_values, itarget_values, idep )

#//===========================================================================//

class TestNodes( AqlTestCase ):
  
  def   setUp( self ):
    disableDefaultHandlers()
    pass
  
  def   tearDown( self ):
    enableDefaultHandlers()
    pass
  
  def test_node_value(self):
    
    with Tempfile() as tmp:
      
      vfile = ValuesFile( tmp.name )
      try:
        value1 = StringValue( "target_url1", "http://aql.org/download" )
        value2 = StringValue( "target_url2", "http://aql.org/download2" )
        value3 = StringValue( "target_url3", "http://aql.org/download3" )
        
        options = builtinOptions()
        builder = ChecksumBuilder( options )
        
        node = Node( builder, [value1, value2, value3] )
        
        self.assertFalse( node.actual( vfile ) )
        builder.build( node )
        builder.save( vfile, node )
        self.assertTrue( node.actual( vfile ) )
        
        node = Node( builder, [value1, value2, value3] )
        self.assertTrue( node.actual( vfile ) )
        builder.build( node )
        builder.save( vfile, node )
        self.assertTrue( node.actual( vfile ) )
        
        node = Node( builder, [value1, value2, value3] )
        node.depends( Value() )
        self.assertFalse( node.actual( vfile ) )
        builder.build( node )
        builder.save( vfile, node )
        self.assertFalse( node.actual( vfile ) )
      
      finally:
        vfile.close()

  #//===========================================================================//

  def   _rebuildNode( self, vfile, builder, values, deps, tmp_files):
    node = Node( builder, values )
    node.depends( deps )
    
    self.assertFalse( node.actual( vfile ) )
    builder.build( node )
    builder.save( vfile, node )
    self.assertTrue( node.actual( vfile ) )
    
    node = Node( builder, values )
    node.depends( deps )
    
    self.assertTrue( node.actual( vfile ) )
    builder.build( node )
    builder.save( vfile, node )
    self.assertTrue( node.actual( vfile ) )
    
    for tmp_file in node.targets():
      tmp_files.append( tmp_file.name )
    
    for tmp_file in node.sideEffects():
      tmp_files.append( tmp_file.name )
    
    return node

  #//=======================================================//

  def test_node_file(self):
    
    try:
      tmp_files = []
      
      with Tempfile() as tmp:
        
        vfile = ValuesFile( tmp.name )
        try:
          with Tempfile( suffix = '.1' ) as tmp1:
            with Tempfile( suffix = '.2' ) as tmp2:
              value1 = FileValue( tmp1.name )
              value2 = FileValue( tmp2.name )
              
              options = builtinOptions()
              
              builder = CopyBuilder( options, "tmp", "i")
              node = self._rebuildNode( vfile, builder, [value1, value2], [], tmp_files )
              
              builder = CopyBuilder( options, "ttt", "i")
              node = self._rebuildNode( vfile, builder, [value1, value2], [], tmp_files )
              
              builder = CopyBuilder( options, "ttt", "d")
              node = self._rebuildNode( vfile, builder, [value1, value2], [], tmp_files )
              
              tmp1.write(b'123')
              tmp1.flush()
              value1 = FileValue( tmp1.name )
              node = self._rebuildNode( vfile, builder, [value1, value2], [], tmp_files )
              
              with Tempfile( suffix = '.3' ) as tmp3:
                value3 = FileValue( tmp3.name )
                
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
                
                dep = StringValue( "dep1", "1" )
                node = self._rebuildNode( vfile, builder, [value1, node3], [dep], tmp_files )
                
                dep = StringValue( "dep1", "11" )
                node = self._rebuildNode( vfile, builder, [value1, node3], [dep], tmp_files )
                node3 = self._rebuildNode( vfile, builder3, [value1], [], tmp_files )
                node = self._rebuildNode( vfile, builder, [value1], [node3], tmp_files )
                node3 = self._rebuildNode( vfile, builder3, [value2], [], tmp_files )
                node = self._rebuildNode( vfile, builder, [value1], [node3], tmp_files )
                
                node_tname = node.targets()[0].name
                
                with open( node_tname, 'wb' ) as f:
                  f.write( b'333' )
                  f.flush()
                
                FileValue( node_tname, use_cache = False )
                
                node = self._rebuildNode( vfile, builder, [value1], [node3], tmp_files )
                
                with open( node.sideEffects()[0].name, 'wb' ) as f:
                  f.write( b'abc' )
                  f.flush()
                
                FileValue( node.sideEffects()[0].name, use_cache = False )
                
                node = self._rebuildNode( vfile, builder, [value1], [node3], tmp_files )
                
                v = Value( name = node.ideps_value.content.data[0].name, content = None )
                vfile.addValues( [v] )
                
                node = self._rebuildNode( vfile, builder, [value1], [node3], tmp_files )
        finally:
          vfile.close()
    finally:
      for tmp_file in tmp_files:
        try:
          os.remove( tmp_file )
        except OSError:
          pass

#//===========================================================================//

_FileContentType = FileContentChecksum

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
    
    for source_value in node.sourceValues():
      new_name = source_value.name + '.' + self.ext
      idep_name = source_value.name + '.' + self.idep
      
      shutil.copy( source_value.name, new_name )
      
      target_values.append( FileValue( new_name, _FileContentType ) )
      idep_values.append( FileValue( idep_name, _FileContentType ) )
    
    node.setTargets( target_values, itarget_values, idep_values )
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    return ' '.join( self.name )

#//===========================================================================//

def   _testNoBuildSpeed( vfile, builder, source_values ):
  for source in source_values:
    node = Node( builder, FileValue( source, _FileContentType ) )
    if not node.actual( vfile ):
      raise AssertionError( "node is not actual" )

def   _generateFiles( tmp_files, number, size ):
  content = b'1' * size
  files = []
  for i in range( 0, number ):
    t = Tempfile()
    tmp_files.append( t.name )
    t.write( content )
    files.append( t.name )
  
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
        
        vfile = ValuesFile( tmp.name )
        try:
          builder = TestSpeedBuilder("TestSpeedBuilder", "tmp", "h")
          
          for source in source_files:
            node = Node( builder, FileValue( source, _FileContentType ) )
            self.assertFalse( node.actual( vfile ) )
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
