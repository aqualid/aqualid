import sys
import os.path
import shutil

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_utils import fileChecksum, printStacks
from aql_temp_file import Tempfile
from aql_value import Value, NoContent
from aql_file_value import FileValue, FileContentTimeStamp, FileContentChecksum
from aql_values_file import ValuesFile
from aql_node import Node
from aql_builder import Builder, RebuildNode
from aql_build_manager import BuildManager
from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_logging import logLevel, CRITICAL

#//===========================================================================//

class CopyValueBuilder (Builder):
  
  def   __init__(self):
    self.signature = b''
  
  def   build( self, build_manager, vfile, node ):
    target_values = []
    
    for source_value in node.sources():
      target_values.append( Value( source_value.name + '_copy', source_value.content ) )
    
    return self.nodeTargets( target_values )

#//===========================================================================//

class ChecksumBuilder (Builder):
  
  __slots__ = (
    'offset',
    'length',
    'replace_ext',
  )
  
  def   __init__(self, offset, length, replace_ext = False ):
    
    self.offset = offset
    self.length = length
    self.replace_ext = replace_ext
    self.signature = str(str(self.offset) + '.' + str(self.length)).encode('utf-8')
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, vfile, node ):
    target_values = []
    
    for source_value in node.sources():
      
      chcksum = fileChecksum( source_value.name, self.offset, self.length, 'sha512' )
      if self.replace_ext:
        chcksum_filename = os.path.splitext(source_value.name)[0] + '.chksum'
      else:
        chcksum_filename = source_value.name + '.chksum'
      
      with open( chcksum_filename, 'wb' ) as f:
        f.write( chcksum.digest() )
      
      target_values.append( FileValue( chcksum_filename ) )
    
    return self.nodeTargets( target_values )

#//===========================================================================//

def   _generateFile( start, stop ):
  tmp = Tempfile()
  tmp.write( bytearray( map( lambda v: v % 256, range( start, stop ) ) ) )
  
  tmp.close()
  
  return tmp.name

#//===========================================================================//

def   _removeFiles( files ):
  for f in files:
    try:
      os.remove( f )
    except (OSError, IOError):
      pass

#//===========================================================================//

def   _generateSourceFiles( num, size ):
  
  src_files = []
  
  start = 0
  
  try:
    while num > 0:
      num -= 1
      src_files.append( _generateFile( start, start + size ) )
      start += size
  except:
    _removeFiles( src_files )
    raise
  
  return src_files

#//===========================================================================//

def   _addNodesToBM( vfilename, builder, src_files ):
  bm = BuildManager( vfilename, 4, True )
  try:
    
    src_values = []
    for s in src_files:
      src_values.append( FileValue( s ) )
    
    checksums_node = Node( builder, src_values )
    checksums_node2 = Node( builder, checksums_node )
    
    bm.add( checksums_node ); bm.selfTest()
    bm.add( checksums_node2 ); bm.selfTest()
  except:
    bm.close()
  
  return bm

#//===========================================================================//

def   _buildChecksums( vfilename, builder, src_files ):
  
  bm = _addNodesToBM( vfilename, builder, src_files )
  try:
    failed_nodes = bm.build()
    for node,err in failed_nodes:
      try:
        import traceback
        traceback.print_tb( err.__traceback__ )
      except AttributeError:
        pass
  finally:
    bm.close()

#//===========================================================================//

def   _clearTargets( vfilename, builder, src_files ):
  
  bm = _addNodesToBM( vfilename, builder, src_files )
  try:
    bm.clear(); bm.selfTest()
  finally:
    bm.close()

#//===========================================================================//

class MultiChecksumBuilder (Builder):
  
  __slots__ = (
    'builder',
  )
  
  def   __init__(self, offset, length ):
    
    self.builder = ChecksumBuilder( offset, length )
    self.signature = self.builder.signature
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, vfile, node ):
    target_values = []
    
    sub_nodes = []
    
    for source_value in node.sources():
      
      n = Node( self.builder, source_value )
      if n.actual( vfile ):
        target_values += n.targets()
      else:
        sub_nodes.append( n )
    
    if sub_nodes:
      build_manager.depends( node, sub_nodes ); build_manager.selfTest()
      raise RebuildNode()
    
    return self.nodeTargets( target_values )

#//===========================================================================//

class TestBuildManager( AqlTestCase ):
  
  @classmethod
  def setUpClass( cls ):
    logLevel( CRITICAL )
  
  def test_bm_deps(self):
    
    bm = BuildManager( None, 0, True )
    
    value1 = Value( "target_url1", "http://aql.org/download" )
    value2 = Value( "target_url2", "http://aql.org/download2" )
    value3 = Value( "target_url3", "http://aql.org/download3" )
    
    builder = CopyValueBuilder()
    
    node0 = Node( builder, value1 )
    node1 = Node( builder, node0 )
    node2 = Node( builder, node1 )
    node3 = Node( builder, value2 )
    node4 = Node( builder, value3 )
    node5 = Node( builder, node4 )
    
    node6 = Node( builder, node5 )
    node6.depends( [node0, node1] )
    
    bm.add( node0 ); bm.selfTest(); self.assertEqual( len(bm), 1 )
    bm.add( node1 ); bm.selfTest(); self.assertEqual( len(bm), 2 )
    bm.add( node2 ); bm.selfTest(); self.assertEqual( len(bm), 3 )
    bm.add( node3 ); bm.selfTest(); self.assertEqual( len(bm), 4 )
    bm.add( node4 ); bm.selfTest(); self.assertEqual( len(bm), 5 )
    bm.add( node5 ); bm.selfTest(); self.assertEqual( len(bm), 6 )
    bm.add( node6 ); bm.selfTest(); self.assertEqual( len(bm), 7 )
    
    node0.depends( node3 ); bm.depends( node0, node3 ); bm.selfTest()
    node1.depends( node3 ); bm.depends( node1, node3 ); bm.selfTest()
    node2.depends( node3 ); bm.depends( node2, node3 ); bm.selfTest()
    node3.depends( node4 ); bm.depends( node3, node4 ); bm.selfTest()
    node0.depends( node5 ); bm.depends( node0, node5 ); bm.selfTest()
    node5.depends( node3 ); bm.depends( node5, node3 ); bm.selfTest()
    
    with self.assertRaises(ErrorNodeCyclicDependency):
      node4.depends( node3 ); bm.depends( node4, node3 ); bm.selfTest()
  
  #//-------------------------------------------------------//
  
  def test_bm_build(self):
  
    #~ event_manager.reset()
    #~ event_manager.addHandlers( EventHandler() )
    
    with Tempfile() as tmp:
      src_files = _generateSourceFiles( 3, 201 )
      try:
        builder = ChecksumBuilder(0, 256 )
        _buildChecksums( tmp.name, builder, src_files )
        #~ _buildChecksums( tmp.name, builder, src_files )
        #~ builder = ChecksumBuilder(32, 1024 )
        #~ _buildChecksums( tmp.name, builder, src_files )
        #~ _buildChecksums( tmp.name, builder, src_files )
        
      finally:
        _clearTargets( tmp.name, builder, src_files )
        _removeFiles( src_files )
  
  #//-------------------------------------------------------//
  
  def test_bm_check(self):
    
    event_manager.reset()
    event_manager.addHandlers( EventHandler() )
    
    with Tempfile() as tmp:
      
      src_files = _generateSourceFiles( 3, 201 )
      try:
        builder = ChecksumBuilder( 0, 256, replace_ext = True )
        _buildChecksums( tmp.name, builder, src_files )
        
        bm = _addNodesToBM( tmp.name, builder, src_files )
        try:
          bm.status(); bm.selfTest()
        finally:
          bm.close()
      
      finally:
        _clearTargets( tmp.name, builder, src_files )
        _removeFiles( src_files )
  
  #//-------------------------------------------------------//
  
  def test_bm_rebuild(self):
    
    event_manager.reset()
    event_manager.addHandlers( EventHandler() )
    
    with Tempfile() as vfilename:
      
      src_files = _generateSourceFiles( 3, 201 )
      try:
        bm = BuildManager( vfilename.name, 4, True )
        try:
          builder = MultiChecksumBuilder( 0, 256 )
          
          src_values = []
          for s in src_files:
            src_values.append( FileValue( s ) )
          
          node = Node( builder, src_values )
          
          bm.add( node ); bm.selfTest()
          failed_nodes = bm.build()
          
          #//-------------------------------------------------------//
          bm.close()
          
          bm = BuildManager( vfilename.name, 4, True )
          builder = MultiChecksumBuilder( 0, 256 )
          
          node = Node( builder, src_values )
          bm.add( node ); bm.selfTest()
          bm.status(); bm.selfTest()
        
        finally:
          bm.close()
        
        #//-------------------------------------------------------//
      
      finally:
        _removeFiles( src_files )
  
  #//-------------------------------------------------------//
  
  @skip
  def test_bm_node_names(self):
    
    event_manager.reset()
    event_manager.addHandlers( EventHandler() )
    
    with Tempfile() as tmp:
      #~ tmp = Tempfile()
      
      src_files = _generateSourceFiles( 3, 201 )
      try:
        builder = ChecksumBuilder( 0, 256, replace_ext = False )
        bm = BuildManager( tmp.name, 4, True )
        try:
          src_values = []
          for s in src_files:
            src_values.append( FileValue( s ) )
          
          node0 = Node( builder, [] )
          node1 = Node( builder, src_values )
          node2 = Node( builder, node1 )
          node3 = Node( builder, node2 )
          node4 = Node( builder, node3 )
          
          bm.add( node0 )
          bm.add( node1 )
          bm.add( node2 )
          bm.add( node3 )
          bm.add( node4 )
          
          #~ bm.build()
          
          print("node2: %s" % str(node4) )
          print("node2: %s" % str(node3) )
          print("node2: %s" % str(node2) )
          print("node1: %s" % str(node1) )
          print("node0: %s" % str(node0) )
        finally:
          bm.close()
      
      finally:
        _removeFiles( src_files )

#//===========================================================================//

def   _generateNodeTree( bm, builder, node, depth ):
  while depth:
    node = Node( builder, node )
    bm.add( node )
    depth -= 1

#//===========================================================================//

@skip
class TestBuildManagerSpeed( AqlTestCase ):
  
  def test_bm_deps_speed(self):
    
    event_manager.reset()
    event_manager.addHandlers( EventHandler() )
    
    bm = BuildManager()
    
    value = Value( "target_url1", "http://aql.org/download" )
    builder = CopyValueBuilder()
    
    node = Node( builder, value )
    bm.add( node )
    
    _generateNodeTree( bm, builder, node, 5000 )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
