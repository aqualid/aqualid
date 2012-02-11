import sys
import os.path
import timeit
import hashlib
import shutil

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_utils import fileChecksum
from aql_temp_file import Tempfile
from aql_value import Value, NoContent
from aql_file_value import FileValue, FileContentTimeStamp, FileContentChecksum
from aql_values_file import ValuesFile
from aql_node import Node
from aql_builder import Builder, RebuildNode
from aql_errors import NodeHasCyclicDependency
from aql_build_manager import BuildManager
from aql_event_manager import event_manager
from aql_event_handler import EventHandler

#//===========================================================================//

class CopyValueBuilder (Builder):
  
  def   __init__(self, name ):
    chcksum = hashlib.md5()
    chcksum.update( name.encode() )
    
    self.name = chcksum.digest()
    self.long_name = [ name ]
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    target_values = []
    
    for source_value in node.sources():
      target_values.append( Value( source_value.name + '_copy', source_value.content ) )
    
    return target_values, [], []
  
  #//-------------------------------------------------------//
  
  def   values( self ):
    return [Value(self.name, "")]
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    return ' '.join( self.long_name )

#//===========================================================================//

@testcase
def test_bm_deps(self):
  
  bm = BuildManager( None, 0, True )
  
  value1 = Value( "target_url1", "http://aql.org/download" )
  value2 = Value( "target_url2", "http://aql.org/download2" )
  value3 = Value( "target_url3", "http://aql.org/download3" )
  
  builder = CopyValueBuilder("CopyValueBuilder")
  
  node0 = Node( builder, value1 )
  node1 = Node( builder, node0 )
  node2 = Node( builder, node1 )
  node3 = Node( builder, value2 )
  node4 = Node( builder, value3 )
  node5 = Node( builder, node4 )
  
  node6 = Node( builder, node5 )
  node6.addDeps( [node0, node1] )
  
  bm.addNodes( node0 ); bm.selfTest(); self.assertEqual( len(bm), 1 )
  bm.addNodes( node1 ); bm.selfTest(); self.assertEqual( len(bm), 2 )
  bm.addNodes( node2 ); bm.selfTest(); self.assertEqual( len(bm), 3 )
  bm.addNodes( node3 ); bm.selfTest(); self.assertEqual( len(bm), 4 )
  bm.addNodes( node4 ); bm.selfTest(); self.assertEqual( len(bm), 5 )
  bm.addNodes( node5 ); bm.selfTest(); self.assertEqual( len(bm), 6 )
  bm.addNodes( node6 ); bm.selfTest(); self.assertEqual( len(bm), 7 )
  
  node0.addDeps( node3 ); bm.addDeps( node0, node3 ); bm.selfTest()
  node1.addDeps( node3 ); bm.addDeps( node1, node3 ); bm.selfTest()
  node2.addDeps( node3 ); bm.addDeps( node2, node3 ); bm.selfTest()
  node3.addDeps( node4 ); bm.addDeps( node3, node4 ); bm.selfTest()
  node0.addDeps( node5 ); bm.addDeps( node0, node5 ); bm.selfTest()
  node5.addDeps( node3 ); bm.addDeps( node5, node3 ); bm.selfTest()
  
  with self.assertRaises(NodeHasCyclicDependency):
    node4.addDeps( node3 ); bm.addDeps( node4, node3 ); bm.selfTest()
  
#//===========================================================================//

class ChecksumBuilder (Builder):
  
  __slots__ = (
    'offset',
    'length',
    'replace_ext',
  )
  
  def   __init__(self, name, offset, length, replace_ext = False ):
    
    chcksum = hashlib.md5()
    chcksum.update( name.encode() )
    
    self.name = chcksum.digest()
    self.long_name = [ name ]
    
    self.offset = offset
    self.length = length
    self.replace_ext = replace_ext
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
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
    
    return target_values, [], []
  
  #//-------------------------------------------------------//
  
  def   clear( self, node, target_values, itarget_values ):
    for value in target_values:
      value.remove()
  
  #//-------------------------------------------------------//
  
  def   values( self ):
    return [ Value(self.name, (self.offset, self.length) ) ]
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    return ' '.join( self.long_name )


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
  
  src_values = []
  for s in src_files:
    src_values.append( FileValue( s ) )
  
  checksums_node = Node( builder, src_values )
  checksums_node2 = Node( builder, checksums_node )
  
  bm.addNodes( checksums_node ); bm.selfTest()
  bm.addNodes( checksums_node2 ); bm.selfTest()
  
  return bm

#//===========================================================================//

def   _buildChecksums( vfilename, builder, src_files ):
  
  bm = _addNodesToBM( vfilename, builder, src_files )
  
  failed_nodes = bm.build()
  for node,err in failed_nodes:
    import traceback
    print("err: %s" % str(err) )
    traceback.print_tb( err.__traceback__ )

#//===========================================================================//

def   _clearTargets( vfilename, builder, src_files ):
  
  bm = _addNodesToBM( vfilename, builder, src_files )
  
  bm.clear(); bm.selfTest()

#//===========================================================================//

@testcase
def test_bm_build(self):
  
  event_manager.addHandler( EventHandler() )
  
  with Tempfile() as tmp:
    #~ tmp = Tempfile()
    
    src_files = _generateSourceFiles( 3, 201 )
    try:
      builder = ChecksumBuilder("ChecksumBuilder", 0, 256 )
      _buildChecksums( tmp.name, builder, src_files )
      _buildChecksums( tmp.name, builder, src_files )
      builder = ChecksumBuilder("ChecksumBuilder", 32, 1024 )
      _buildChecksums( tmp.name, builder, src_files )
      _buildChecksums( tmp.name, builder, src_files )
      
    finally:
      _clearTargets( tmp.name, builder, src_files )
      _removeFiles( src_files )

#//===========================================================================//

@testcase
def test_bm_check(self):
  
  event_manager.addHandler( EventHandler() )
  
  with Tempfile() as tmp:
    #~ tmp = Tempfile()
    
    src_files = _generateSourceFiles( 3, 201 )
    try:
      builder = ChecksumBuilder("ChecksumBuilder", 0, 256, replace_ext = True )
      _buildChecksums( tmp.name, builder, src_files )
      #~ _buildChecksums( tmp.name, builder, src_files )
      
      bm = _addNodesToBM( tmp.name, builder, src_files )
      bm.status(); bm.selfTest()
    
    finally:
      _clearTargets( tmp.name, builder, src_files )
      _removeFiles( src_files )

#//===========================================================================//

class TestEnv( object ):
  __slots__ = ('build_manager')
  
  def   __init__(self, bm ):
    self.build_manager = bm

#//===========================================================================//

class MultiChecksumBuilder (Builder):
  
  __slots__ = (
    'builder',
  )
  
  def   __init__(self, env, name, offset, length ):
    
    chcksum = hashlib.md5()
    chcksum.update( name.encode() )
    
    self.name = chcksum.digest()
    self.long_name = [ name ]
    
    self.env = env
    self.builder = ChecksumBuilder( "ChecksumBuilder", offset, length )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    target_values = []
    
    bm = self.env.build_manager
    vfile = bm.valuesFile()
    
    sub_nodes = []
    
    print( "node.sources(): %s" % str(node.sources()) )
    
    for source_value in node.sources():
      
      print( "source_value: %s" % str(source_value) )
      
      n = Node( self.builder, source_value )
      if n.actual( vfile ):
        target_values += n.targets()
      else:
        sub_nodes.append( n )
    
    if sub_nodes:
      bm.addNodes( sub_nodes )
      raise RebuildNode()
    
    return target_values, [], []
  
  #//-------------------------------------------------------//
  
  def   clear( self, node, target_values, itarget_values ):
    for value in target_values:
      value.remove()
  
  #//-------------------------------------------------------//
  
  def   values( self ):
    return self.builder.values()
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    return ' '.join( self.long_name )

#//===========================================================================//

@testcase
def test_bm_rebuild(self):
  
  event_manager.addHandler( EventHandler() )
  
  with Tempfile() as vfilename:
    #~ tmp = Tempfile()test_bm_node_names
    
    src_files = _generateSourceFiles( 1, 201 )
    try:
      bm = BuildManager( vfilename.name, 4, True )
      
      env = TestEnv( bm )
      
      builder = MultiChecksumBuilder( env, "MultiChecksumBuilder", 0, 256 )
      
      
      src_values = []
      for s in src_files:
        src_values.append( FileValue( s ) )
      
      node = Node( builder, src_values )
      
      bm.addNodes( node ); bm.selfTest()
      failed_nodes = bm.build()
      
      for node, err in failed_nodes:
        import traceback
        print("err: %s" % str(err) )
        traceback.print_tb( err.__traceback__ )
      
      bm.status(); bm.selfTest()
    
    finally:
      _removeFiles( src_files )

#//===========================================================================//

@skip
@testcase
def test_bm_node_names(self):
  
  event_manager.addHandler( EventHandler() )
  
  with Tempfile() as tmp:
    #~ tmp = Tempfile()
    
    src_files = _generateSourceFiles( 3, 201 )
    try:
      builder = ChecksumBuilder("ChecksumBuilder", 0, 256, replace_ext = False )
      bm = BuildManager( tmp.name, 4, True )
      
      src_values = []
      for s in src_files:
        src_values.append( FileValue( s ) )
      
      node0 = Node( builder, [] )
      node1 = Node( builder, src_values )
      node2 = Node( builder, node1 )
      node3 = Node( builder, node2 )
      node4 = Node( builder, node3 )
      
      bm.addNodes( node0 )
      bm.addNodes( node1 )
      bm.addNodes( node2 )
      bm.addNodes( node3 )
      bm.addNodes( node4 )
      
      #~ bm.build()
      
      print("node2: %s" % str(node4) )
      print("node2: %s" % str(node3) )
      print("node2: %s" % str(node2) )
      print("node1: %s" % str(node1) )
      print("node0: %s" % str(node0) )
    
    finally:
      _removeFiles( src_files )


#//===========================================================================//

def   _generateNodeTree( bm, builder, node, depth ):
  while depth:
    node = Node( builder, node )
    bm.addNodes( node )
    depth -= 1

#//===========================================================================//

@skip
@testcase
def test_bm_deps_speed(self):
  
  event_manager.addHandler( EventHandler() )
  
  bm = BuildManager()
  
  value = Value( "target_url1", "http://aql.org/download" )
  builder = CopyValueBuilder("CopyValueBuilder")
  
  node = Node( builder, value )
  bm.addNodes( node )
  
  _generateNodeTree( bm, builder, node, 5000 )


#//===========================================================================//

if __name__ == "__main__":
  runTests()
