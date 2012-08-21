import sys
import os.path
import timeit
import hashlib
import shutil

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))
from aql_tests import skip, AqlTestCase, runLocalTests

from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_temp_file import Tempfile
from aql_value import Value, NoContent
from aql_file_value import FileValue, FileContentTimeStamp, FileContentChecksum
from aql_depends_value import DependsValue
from aql_values_file import ValuesFile
from aql_node import Node
from aql_builder import Builder

#//===========================================================================//

class ChecksumBuilder (Builder):
  
  def   __init__(self, name ):
    self.name = [ name ]
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, vfile, node ):
    target_values = []
    itarget_values = []
    
    for source_value in node.sources():
      content = source_value.content.encode()
      chcksum = hashlib.md5()
      chcksum.update( content )
      chcksum_sha512 = hashlib.sha512()
      chcksum_sha512.update( content )
      target_values.append( Value( source_value.name + '_chksum', chcksum.digest() ) )
      itarget_values.append( Value( source_value.name + '_chcksum_sha512', chcksum_sha512.digest() ) )
    
    return target_values, itarget_values, []
  
  #//-------------------------------------------------------//
  
  def   signature( self ):
    return ""
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    return ' '.join( self.name )


#//===========================================================================//

class CopyBuilder (Builder):
  
  __slots__ = ('ext', 'iext')
  
  def   __init__(self, name, ext, iext ):
    self.name = [ name ]
    self.ext = ext
    self.iext = iext
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, vfile, node ):
    target_values = []
    itarget_values = []
    idep_values = []
    
    idep = Value( ",".join(node.name) + "CopyBuilderDep", node.name_key )
    
    for source_value in node.sources():
      new_name = source_value.name + '.' + self.ext
      new_iname = source_value.name + '.' + self.iext
      
      shutil.copy( source_value.name, new_name )
      shutil.copy( source_value.name, new_iname )
      
      target_values.append( FileValue( new_name ) )
      itarget_values.append( FileValue( new_iname ) )
    
    return target_values, itarget_values, [idep]
  
  #//-------------------------------------------------------//
  
  def   signature( self ):
    return [self.ext, self.iext]
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    return ' '.join( self.name )

#//===========================================================================//

class TestNodes( AqlTestCase ):

  def test_node_value(self):
    event_manager.reset()
    event_manager.addHandlers( EventHandler() )
    
    with Tempfile() as tmp:
      
      vfile = ValuesFile( tmp.name )
      
      value1 = Value( "target_url1", "http://aql.org/download" )
      value2 = Value( "target_url2", "http://aql.org/download2" )
      value3 = Value( "target_url3", "http://aql.org/download3" )
      
      builder = ChecksumBuilder("ChecksumBuilder")
      
      node = Node( builder, [value1, value2, value3] )
      
      self.assertFalse( node.actual( vfile ) )
      node.build( None, vfile )
      self.assertTrue( node.actual( vfile ) )
      
      node = Node( builder, [value1, value2, value3] )
      self.assertTrue( node.actual( vfile ) )
      node.build( None, vfile )
      self.assertTrue( node.actual( vfile ) )

  #//===========================================================================//

  def   _rebuildNode( self, vfile, builder, values, deps, tmp_files):
    node = Node( builder, values )
    node.addDeps( deps )
    
    self.assertFalse( node.actual( vfile ) )
    node.build( None, vfile )
    self.assertTrue( node.actual( vfile ) )
    
    node = Node( builder, values )
    node.addDeps( deps )
    
    self.assertTrue( node.actual( vfile ) )
    node.build( None, vfile )
    self.assertTrue( node.actual( vfile ) )
    
    for tmp_file in node.target_values:
      tmp_files.append( tmp_file.name )
    
    for tmp_file in node.itarget_values:
      tmp_files.append( tmp_file.name )
    
    return node

  #//=======================================================//

  def test_node_file(self):
    event_manager.reset()
    event_manager.addHandlers( EventHandler() )
    
    try:
      tmp_files = []
      
      with Tempfile() as tmp:
        
        vfile = ValuesFile( tmp.name )
        
        with Tempfile() as tmp1:
          with Tempfile() as tmp2:
            value1 = FileValue( tmp1.name )
            value2 = FileValue( tmp2.name )
            
            builder = CopyBuilder("CopyBuilder", "tmp", "i")
            node = self._rebuildNode( vfile, builder, [value1, value2], [], tmp_files )
            
            builder = CopyBuilder("CopyBuilder", "ttt", "i")
            node = self._rebuildNode( vfile, builder, [value1, value2], [], tmp_files )
            
            builder = CopyBuilder("CopyBuilder", "ttt", "d")
            node = self._rebuildNode( vfile, builder, [value1, value2], [], tmp_files )
            
            tmp1.write(b'123')
            tmp1.flush()
            value1 = FileValue( tmp1.name )
            node = self._rebuildNode( vfile, builder, [value1, value2], [], tmp_files )
            
            with Tempfile() as tmp3:
              value3 = FileValue( tmp3.name )
              node3 = self._rebuildNode( vfile, builder, [value3], [], tmp_files )
              node = self._rebuildNode( vfile, builder, [value1, node3], [], tmp_files )
              
              builder3 = CopyBuilder("CopyBuilder", "xxx", "3")
              node3 = self._rebuildNode( vfile, builder3, [value3], [], tmp_files )
              node = self._rebuildNode( vfile, builder, [value1, node3], [], tmp_files )
              node = self._rebuildNode( vfile, builder, [value1], [node3], tmp_files )
              
              dep = Value( "dep1", "1" )
              node = self._rebuildNode( vfile, builder, [value1, node3], [dep], tmp_files )
              
              dep = Value( "dep1", "11" )
              node = self._rebuildNode( vfile, builder, [value1, node3], [dep], tmp_files )
              node3 = self._rebuildNode( vfile, builder3, [value1], [], tmp_files )
              node = self._rebuildNode( vfile, builder, [value1], [node3], tmp_files )
              node3 = self._rebuildNode( vfile, builder3, [value2], [], tmp_files )
              node = self._rebuildNode( vfile, builder, [value1], [node3], tmp_files )
              
              with open( node.target_values[0].name, 'wb' ) as f:
                f.write( b'333' )
                f.flush()
              
              node = self._rebuildNode( vfile, builder, [value1], [node3], tmp_files )
              
              with open( node.itarget_values[0].name, 'wb' ) as f:
                f.write( b'abc' )
                f.flush()
              
              node = self._rebuildNode( vfile, builder, [value1], [node3], tmp_files )
              
              v = Value( node.idep_values[0].name, None )
              vfile.addValues( [v] )
              
              node = self._rebuildNode( vfile, builder, [value1], [node3], tmp_files )
            
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
  
  def   __init__(self, name, ext, idep ):
    self.name = [ name ]
    self.ext = ext
    self.idep = idep
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, vfile, node ):
    target_values = []
    itarget_values = []
    idep_values = []
    
    for source_value in node.sources():
      new_name = source_value.name + '.' + self.ext
      idep_name = source_value.name + '.' + self.idep
      
      shutil.copy( source_value.name, new_name )
      
      target_values.append( FileValue( new_name, _FileContentType ) )
      idep_values.append( FileValue( idep_name, _FileContentType ) )
    
    return target_values, itarget_values, idep_values
  
  #//-------------------------------------------------------//
  
  def   signature( self ):
    return [self.ext, self.idep]
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    return ' '.join( self.name )

#//===========================================================================//

def   _testNoBuildSpeed( vfile, builder, source_values ):
  for source in source_values:
    node = Node( builder, [ FileValue( source, _FileContentType ) ] )
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
    event_manager.reset()
    event_manager.addHandlers( EventHandler() )
    
    try:
      tmp_files = []
      
      source_files = _generateFiles( tmp_files, 4000, 50 * 1024 )
      idep_files = _copyFiles( tmp_files, source_files, 'h' )
      
      with Tempfile() as tmp:
        
        vfile = ValuesFile( tmp.name )
        
        builder = TestSpeedBuilder("TestSpeedBuilder", "tmp", "h")
        
        for source in source_files:
          node = Node( builder, [ FileValue( source, _FileContentType ) ] )
          self.assertFalse( node.actual( vfile ) )
          node.build( None, vfile )
          for tmp_file in node.target_values:
            tmp_files.append( tmp_file.name )
        
        t = lambda vfile = vfile, builder = builder, source_files = source_files, testNoBuildSpeed = _testNoBuildSpeed: testNoBuildSpeed( vfile, builder, source_files )
        t = timeit.timeit( t, number = 1 )
        print("load actual nodes: %s" % t)
        
    finally:
      for tmp_file in tmp_files:
        try:
          os.remove( tmp_file )
        except OSError:
          pass

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
