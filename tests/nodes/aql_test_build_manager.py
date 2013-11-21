import sys
import os.path

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import fileChecksum, Tempfile, Tempdir, eventHandler, finishHandleEvents, disableDefaultHandlers, enableDefaultHandlers
from aql.values import Value, StringValue, FileValue
from aql.options import builtinOptions
from aql.nodes import Node, Builder, BuildManager, ErrorNodeDependencyCyclic

#//===========================================================================//

class CopyValueBuilder (Builder):
  
  def   __init__(self, options ):
    self.signature = b''
  
  def   build( self, node ):
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
  
  def   __init__(self, options, offset, length, replace_ext = False ):
    
    self.offset = offset
    self.length = length
    self.replace_ext = replace_ext
    self.signature = str(str(self.offset) + '.' + str(self.length)).encode('utf-8')
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    target_values = []
    
    for source_value in node.sources():
      
      chcksum = fileChecksum( source_value.name, self.offset, self.length, 'sha512' )
      if self.replace_ext:
        chcksum_filename = os.path.splitext(source_value.name)[0] + '.chksum'
      else:
        chcksum_filename = source_value.name + '.chksum'
      
      chcksum_filename = self.buildPath( chcksum_filename )
      
      with open( chcksum_filename, 'wb' ) as f:
        f.write( chcksum.digest() )
      
      target_values.append( FileValue( chcksum_filename ) )
    
    return node.setTargets( target_values )

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

def   _addNodesToBM( builder, src_files ):
  bm = BuildManager()
  try:
    
    src_values = []
    for s in src_files:
      src_values.append( FileValue( s ) )
    
    checksums_node = Node( builder, None, src_values )
    checksums_node2 = Node( builder, checksums_node, None )
    
    bm.add( checksums_node ); bm.selfTest()
    bm.add( checksums_node2 ); bm.selfTest()
  except:
    bm.close()
  
  return bm

#//===========================================================================//

def   _build( bm ):
  try:
    bm.selfTest()
    failed_nodes = bm.build( 1, False )
    for node,err in failed_nodes:
      
      print( "Failed node: %s" % (err,))
      try:
        import traceback
        traceback.print_tb( err.__traceback__ )
      except AttributeError:
        pass
    
    if failed_nodes:
      raise Exception("Nodes failed")
    
  finally:
    bm.selfTest()
    bm.close()
    bm.selfTest()
    finishHandleEvents()

#//===========================================================================//

def   _buildChecksums( builder, src_files ):
  
  bm = _addNodesToBM( builder, src_files )
  _build( bm )

#//===========================================================================//

class MultiChecksumBuilder (Builder):
  
  __slots__ = (
    'builder',
  )
  
  def   __init__(self, options, offset, length ):
    
    self.builder = ChecksumBuilder( options, offset, length )
    self.signature = self.builder.signature
  
  #//-------------------------------------------------------//
  
  def   prebuild( self, vfile, node ):
    
    targets = []
    sub_nodes = []
    
    for source_value in node.sources():
      
      n = Node( self.builder, None, source_value )
      if n.actual( vfile ):
        targets += n.targets()
      else:
        sub_nodes.append( n )
    
    node.setTargets( targets )
    
    return sub_nodes
  
  #//-------------------------------------------------------//
  
  def   prebuildFinished( self, vfile, node, sub_nodes ):
    
    targets = list( node.targets() )
    for sub_node in sub_nodes:
      targets += sub_node.targets()
    
    node.setTargets( targets )
  
  #//-------------------------------------------------------//
  
  def   actual( self, vfile, node ):
    return True

#//===========================================================================//

_building_started = [0]

@eventHandler
def   eventNodeBuilding( node ):
  global _building_started
  _building_started[0] += 1

#//-------------------------------------------------------//

_building_finished = [0]

@eventHandler
def   eventNodeBuildingFinished( node ):
  global _building_finished
  _building_finished[0] += 1

#//-------------------------------------------------------//

_actual_node = [0]
@eventHandler
def   eventBuildStatusActualNode( node ):
  global _actual_node
  _actual_node[0] += 1

#//-------------------------------------------------------//

_outdated_node = [0]
@eventHandler
def   eventBuildStatusOutdatedNode( node ):
  global _outdated_node
  _outdated_node[0] += 1

#//===========================================================================//

class TestBuildManager( AqlTestCase ):
  
  def   setUp( self ):
    disableDefaultHandlers()
    pass
  
  def   tearDown( self ):
    enableDefaultHandlers()
    pass
  
  def test_bm_deps(self):
    
    bm = BuildManager()
    
    value1 = StringValue( "target_url1", "http://aql.org/download" )
    value2 = StringValue( "target_url2", "http://aql.org/download2" )
    value3 = StringValue( "target_url3", "http://aql.org/download3" )
    
    options = builtinOptions()
    
    builder = CopyValueBuilder( options )
    
    node0 = Node( builder, None, value1,  )
    node1 = Node( builder, node0, None )
    node2 = Node( builder, node1, None )
    node3 = Node( builder, None, value2 )
    node4 = Node( builder, None, value3 )
    node5 = Node( builder, node4, None )
    
    node6 = Node( builder, node5, None )
    node6.depends( [node0, node1], None )
    
    bm.add( node0 ); bm.selfTest(); self.assertEqual( len(bm), 1 )
    bm.add( node1 ); bm.selfTest(); self.assertEqual( len(bm), 2 )
    bm.add( node2 ); bm.selfTest(); self.assertEqual( len(bm), 3 )
    bm.add( node3 ); bm.selfTest(); self.assertEqual( len(bm), 4 )
    bm.add( node4 ); bm.selfTest(); self.assertEqual( len(bm), 5 )
    bm.add( node5 ); bm.selfTest(); self.assertEqual( len(bm), 6 )
    bm.add( node6 ); bm.selfTest(); self.assertEqual( len(bm), 7 )
    
    node0.depends( node3, None ); bm.depends( node0, node3 ); bm.selfTest()
    node1.depends( node3, None ); bm.depends( node1, node3 ); bm.selfTest()
    node2.depends( node3, None ); bm.depends( node2, node3 ); bm.selfTest()
    node3.depends( node4, None ); bm.depends( node3, node4 ); bm.selfTest()
    node0.depends( node5, None ); bm.depends( node0, node5 ); bm.selfTest()
    node5.depends( node3, None ); bm.depends( node5, node3 ); bm.selfTest()
    
    with self.assertRaises(ErrorNodeDependencyCyclic):
      node4.depends( node3, None ); bm.depends( node4, node3 ); bm.selfTest()
  
  #//-------------------------------------------------------//
  
  def test_bm_build(self):
    
    with Tempdir() as tmp_dir:
      
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      src_files = _generateSourceFiles( 3, 201 )
      try:
        
        builder = ChecksumBuilder( options, 0, 256 )
        
        _building_started[0] = _building_finished[0] = 0
        _buildChecksums( builder, src_files )
        self.assertEqual( _building_started[0], 2 )
        self.assertEqual( _building_started, _building_finished )
        
        #//-------------------------------------------------------//
        
        _building_started[0] = _building_finished[0] = 0
        _buildChecksums( builder, src_files )
        self.assertEqual( _building_started[0], 0 )
        self.assertEqual( _building_started, _building_finished )
        
        #//-------------------------------------------------------//
        
        builder = ChecksumBuilder( options, 32, 1024 )
        
        _building_started[0] = _building_finished[0] = 0
        _buildChecksums( builder, src_files )
        self.assertEqual( _building_started[0], 2 )
        self.assertEqual( _building_started, _building_finished )
        
        #//-------------------------------------------------------//
        
        _building_started[0] = _building_finished[0] = 0
        _buildChecksums( builder, src_files )
        self.assertEqual( _building_started[0], 0 )
        self.assertEqual( _building_started, _building_started )
        
      finally:
        _removeFiles( src_files )
  
  #//-------------------------------------------------------//
  
  def test_bm_check(self):
    
    global _building_started
    global _building_finished
    global _outdated_node
    global _actual_node
    
    with Tempdir() as tmp_dir:
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      src_files = _generateSourceFiles( 3, 201 )
      try:
        builder = ChecksumBuilder( options, 0, 256, replace_ext = True )
        
        _building_started[0] = _building_finished[0] = 0
        _buildChecksums( builder, src_files )
        self.assertEqual( _building_started[0], 2 )
        self.assertEqual( _building_started, _building_finished )
        
        bm = _addNodesToBM( builder, src_files )
        try:
          _actual_node[0] = _outdated_node[0] = 0
          bm.status(); bm.selfTest()
          
          finishHandleEvents()
          self.assertEqual( _outdated_node[0], 0)
          self.assertEqual( _actual_node[0], 2 )
          
        finally:
          bm.close()
      
      finally:
        _removeFiles( src_files )
  
  #//-------------------------------------------------------//
  
  def test_bm_rebuild(self):
    
    global _building_started
    global _building_finished
    global _outdated_node
    global _actual_node
    
    with Tempdir() as tmp_dir:
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      src_files = _generateSourceFiles( 3, 201 )
      try:
        bm = BuildManager()
        try:
          _building_started[0] = _building_finished[0] = 0
          _actual_node[0] = _outdated_node[0] = 0
          
          builder = MultiChecksumBuilder( options, 0, 256 )
          
          src_values = []
          for s in src_files:
            src_values.append( FileValue( s ) )
          
          node = Node( builder, None, src_values )
          
          bm.add( node )
          _build( bm )
          
          self.assertEqual( _building_started[0], 3 )
          
          #//-------------------------------------------------------//
          _actual_node[0] = _outdated_node[0] = 0
          
          bm = BuildManager()
          builder = MultiChecksumBuilder( options, 0, 256 )
          
          node = Node( builder, None, src_values )
          bm.add( node ); bm.selfTest()
          bm.status(); bm.selfTest()
          
          finishHandleEvents()
          self.assertEqual( _outdated_node[0], 0 )
          self.assertEqual( _actual_node[0], 1 )
        
        finally:
          bm.close()
        
        #//-------------------------------------------------------//
      
      finally:
        _removeFiles( src_files )
  
  #//-------------------------------------------------------//
  
  @skip
  def test_bm_node_names(self):
    
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
          
          node0 = Node( builder, None, None )
          node1 = Node( builder, None, src_values )
          node2 = Node( builder, node1, None )
          node3 = Node( builder, node2, None )
          node4 = Node( builder, node3, None )
          
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
    
    bm = BuildManager()
    
    value = StringValue( "target_url1", "http://aql.org/download" )
    builder = CopyValueBuilder()
    
    node = Node( builder, value )
    bm.add( node )
    
    _generateNodeTree( bm, builder, node, 5000 )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
