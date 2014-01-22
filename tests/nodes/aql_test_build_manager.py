import sys
import os.path

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import fileChecksum, Tempfile, Tempdir, \
  disableDefaultHandlers, enableDefaultHandlers, addUserHandler, removeUserHandler

from aql.values import Value, StringValue, FileValue
from aql.options import builtinOptions
from aql.nodes import Node, Builder, BuildManager, ErrorNodeDependencyCyclic

#//===========================================================================//

class CopyValueBuilder (Builder):
  
  def   __init__(self, options ):
    self.signature = b''
  
  def   build( self, node ):
    target_values = []
    
    for source_value in node.getSourceValues():
      target_values.append( Value( name = source_value.name + '_copy', content = source_value.content ) )
    
    node.setTargets( target_values )

#//===========================================================================//

class ChecksumBuilder (Builder):
  
  NAME_ATTRS = ('replace_ext',)
  SIGNATURE_ATTRS = ('offset', 'length')
  
  def   __init__(self, options, offset, length, replace_ext = False ):
    
    self.offset = offset
    self.length = length
    self.replace_ext = replace_ext
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    target_values = []
    
    for src in node.getSources():
      
      chcksum = fileChecksum( src, self.offset, self.length, 'sha512' )
      if self.replace_ext:
        chcksum_filename = os.path.splitext(src)[0] + '.chksum'
      else:
        chcksum_filename = src + '.chksum'
      
      chcksum_filename = self.getBuildPath( chcksum_filename )
      
      with open( chcksum_filename, 'wb' ) as f:
        f.write( chcksum.digest() )
      
      target_values.append( chcksum_filename )
    
    node.setFileTargets( target_values )

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
    
    checksums_node = Node( builder, src_values )
    checksums_node2 = Node( builder, checksums_node )
    
    bm.add( checksums_node ); bm.selfTest()
    bm.add( checksums_node2 ); bm.selfTest()
  except Exception:
    bm.close()
    raise
  
  return bm

#//===========================================================================//

def   _build( bm ):
  try:
    bm.selfTest()
    failed_nodes = bm.build( jobs = 1, keep_going = False )
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
    
    for source_value in node.getSourceValues():
      
      n = Node( self.builder, source_value )
      if n.actual( vfile ):
        targets += n.getTargetValues()
      else:
        sub_nodes.append( n )
    
    node.setTargets( targets )
    
    return sub_nodes
  
  #//-------------------------------------------------------//
  
  def   prebuildFinished( self, vfile, node, sub_nodes ):
    
    targets = list( node.getTargetValues() )
    for sub_node in sub_nodes:
      targets += sub_node.getTargetValues()
    
    node.setTargets( targets )
  
  #//-------------------------------------------------------//
  
  def   actual( self, vfile, node ):
    return True

#//===========================================================================//

class TestBuildManager( AqlTestCase ):
  
  def   eventNodeBuilding( self, node, detailed ):
    self.building_started += 1
  
  #//-------------------------------------------------------//
  
  def   eventNodeBuildingFinished( self, node, out, detailed ):
    self.building_finished += 1
  
  #//-------------------------------------------------------//
  
  def   eventBuildStatusActualNode( self, node, detailed ):
    self.actual_node += 1
  
  #//-------------------------------------------------------//
  
  def   eventBuildStatusOutdatedNode( self, node, detailed ):
    self.outdated_node += 1
  
  #//-------------------------------------------------------//
  
  def   setUp( self ):
    # disableDefaultHandlers()
    
    self.building_started = 0
    addUserHandler( self.eventNodeBuilding, "eventNodeBuilding" )
    
    self.building_finished = 0
    addUserHandler( self.eventNodeBuildingFinished, "eventNodeBuildingFinished" )
    
    self.actual_node = 0
    addUserHandler( self.eventBuildStatusActualNode, "eventBuildStatusActualNode" )
    
    self.outdated_node = 0
    addUserHandler( self.eventBuildStatusOutdatedNode, "eventBuildStatusOutdatedNode" )
  
  #//-------------------------------------------------------//
  
  def   tearDown( self ):
    removeUserHandler( [  self.eventNodeBuilding,
                          self.eventNodeBuildingFinished,
                          self.eventNodeBuildingFinished,
                          self.eventBuildStatusOutdatedNode,
                          self.eventBuildStatusActualNode ] )

    enableDefaultHandlers()
  
  #//-------------------------------------------------------//
  
  def test_bm_deps(self):
    
    bm = BuildManager()
    
    value1 = StringValue( "target_url1", "http://aql.org/download" )
    value2 = StringValue( "target_url2", "http://aql.org/download2" )
    value3 = StringValue( "target_url3", "http://aql.org/download3" )
    
    options = builtinOptions()
    
    builder = CopyValueBuilder( options )
    
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
    
    with self.assertRaises(ErrorNodeDependencyCyclic):
      node4.depends( node3 ); bm.depends( node4, node3 ); bm.selfTest()
  
  #//-------------------------------------------------------//
  
  def test_bm_build(self):
    
    with Tempdir() as tmp_dir:
      
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      src_files = _generateSourceFiles( 1, 201 )
      try:
        
        builder = ChecksumBuilder( options, 0, 256 )
        
        self.building_started = self.building_finished = 0
        _buildChecksums( builder, src_files )
        self.assertEqual( self.building_started, 2 )
        self.assertEqual( self.building_started, self.building_finished )
        
        #//-------------------------------------------------------//
        
        self.building_started = self.building_finished = 0
        _buildChecksums( builder, src_files )
        self.assertEqual( self.building_started, 0 )
        self.assertEqual( self.building_started, self.building_finished )
        
        #//-------------------------------------------------------//
        
        builder = ChecksumBuilder( options, 32, 1024 )
        
        self.building_started = self.building_finished = 0
        _buildChecksums( builder, src_files )
        self.assertEqual( self.building_started, 2 )
        self.assertEqual( self.building_started, self.building_finished )
        
        #//-------------------------------------------------------//
        
        self.building_started = self.building_finished = 0
        _buildChecksums( builder, src_files )
        self.assertEqual( self.building_started, 0 )
        self.assertEqual( self.building_started, self.building_started )
        
      finally:
        _removeFiles( src_files )
  
  #//-------------------------------------------------------//
  
  def test_bm_nodes(self):
    
    with Tempdir() as tmp_dir:
      options = builtinOptions()
      options.build_dir = tmp_dir
    
      bm = BuildManager()
      
      value1 = StringValue( name = "target_url1", content = "http://aql.org/download" )
      value2 = StringValue( name = "target_url2", content = "http://aql.org/download2" )
      value3 = StringValue( name = "target_url3", content = "http://aql.org/download3" )
      
      builder = CopyValueBuilder( options )
      
      node1 = Node( builder, value1 )
      copy_node1 = Node( builder, node1 )
      copy2_node1 = Node( builder, copy_node1 )
      node2 = Node( builder, value2 )
      node3 = Node( builder, value3 )
      copy_node3 = Node( builder, node3 )
      
      copy2_node3 = Node( builder, copy_node3 )
      copy2_node3.depends( [node1, copy_node1] )
      
      bm.add( [copy2_node1, node2, copy2_node3])
      
      #// --------- //
      
      self.building_finished = 0
      bm.build( jobs = 1, keep_going = False )
      self.assertEqual( self.building_finished, 7 )
      
      #// --------- //
      
      bm.add( [copy2_node1, node2, copy2_node3])
      
      bm.clear()
      
      #// --------- //
      
      bm.add( [copy2_node1, node2, copy2_node3] )
      
      self.building_finished = 0
      bm.build( jobs = 1, keep_going = False, nodes = [copy_node1] )
      self.assertEqual( self.building_finished, 2 )
      
      #// --------- //
      
      bm.add( [copy2_node1, node2, copy2_node3] )
      
      self.building_finished = 0
      bm.build( jobs = 1, keep_going = False, nodes = [node2, copy_node3] )
      self.assertEqual( self.building_finished, 3 )
      
      #// --------- //
  
  #//-------------------------------------------------------//
  
  def test_bm_check(self):
    
    with Tempdir() as tmp_dir:
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      src_files = _generateSourceFiles( 3, 201 )
      try:
        builder = ChecksumBuilder( options, 0, 256, replace_ext = True )
        
        self.building_started = self.building_finished = 0
        _buildChecksums( builder, src_files )
        self.assertEqual( self.building_started, 2 )
        self.assertEqual( self.building_started, self.building_finished )
        
        bm = _addNodesToBM( builder, src_files )
        try:
          self.actual_node = self.outdated_node = 0
          bm.status( detailed = True ); bm.selfTest()
          
          self.assertEqual( self.outdated_node, 0)
          self.assertEqual( self.actual_node, 2 )
          
        finally:
          bm.close()
      
      finally:
        _removeFiles( src_files )
  
  #//-------------------------------------------------------//
  
  def test_bm_rebuild(self):
    
    with Tempdir() as tmp_dir:
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      src_files = _generateSourceFiles( 3, 201 )
      try:
        bm = BuildManager()
        try:
          self.building_started = self.building_finished = 0
          self.actual_node = self.outdated_node = 0
          
          builder = MultiChecksumBuilder( options, 0, 256 )
          
          src_values = []
          for s in src_files:
            src_values.append( FileValue( s ) )
          
          node = Node( builder, src_values )
          
          bm.add( node )
          _build( bm )
          
          self.assertEqual( self.building_started, 3 )
          
          #//-------------------------------------------------------//
          
          self.actual_node = self.outdated_node = 0
          
          bm = BuildManager()
          builder = MultiChecksumBuilder( options, 0, 256 )
          
          node = Node( builder, src_values )
          bm.add( node ); bm.selfTest()
          bm.status(); bm.selfTest()
          
          self.assertEqual( self.outdated_node, 0 )
          self.assertEqual( self.actual_node, 1 )
        
        finally:
          bm.close()
        
        #//-------------------------------------------------------//
      
      finally:
        _removeFiles( src_files )
  
  #//-------------------------------------------------------//
  
  @skip
  def test_bm_node_names(self):
    
    with Tempdir() as tmp_dir:
      #~ tmp = Tempfile()
      
      src_files = _generateSourceFiles( 3, 201 )
      try:
        
        options = builtinOptions()
        options.build_dir = tmp_dir
        
        builder = ChecksumBuilder( options, 0, 256, replace_ext = False )
        bm = BuildManager()
        try:
          src_values = []
          for s in src_files:
            src_values.append( FileValue( s ) )
          
          node0 = Node( builder, None )
          node1 = Node( builder, src_values )
          node2 = Node( builder, node1 )
          node3 = Node( builder, node2 )
          node4 = Node( builder, node3 )
          
          bm.add( node0 )
          bm.add( node1 )
          bm.add( node2 )
          bm.add( node3 )
          bm.add( node4 )
          
          bm.build(1, False)
          
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
