import sys
import os.path
import time
import threading

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import fileChecksum, Tempdir, \
  disableDefaultHandlers, enableDefaultHandlers, addUserHandler, removeUserHandler

from aql.values import SimpleEntity, FileChecksumEntity
from aql.options import builtinOptions
from aql.nodes import Node, BatchNode, Builder, FileBuilder, BuildManager
from aql.nodes.aql_build_manager import ErrorNodeDependencyCyclic, ErrorNodeSignatureDifferent

#//===========================================================================//

class FailedBuilder (Builder):
  def   build( self, node ):
    raise Exception("Builder always fail.") 

#//===========================================================================//

_sync_lock = threading.Lock()
_sync_value = 0

class SyncValueBuilder (Builder):
  NAME_ATTRS = ('name',)
  
  def   __init__(self, options, name, number, sleep_interval = 1 ):
    self.signature = b''
    
    self.name = name
    self.sleep_interval = sleep_interval
    self.number = number
    
    # self.initLocks( lock_names )
  
  #//-------------------------------------------------------//
  
  def   getTraceName(self, brief ):
    name = self.__class__.__name__
    name += "(%s:%s)" % (self.name, self.number,)
    return name
  
  #//-------------------------------------------------------//
  
  def   initLocks(self, lock_names, sync_locks ):
    self.locks = locks = []
    self.lock_names = lock_names
    
    for lock_name in lock_names:
      lock = sync_locks.get( lock_name, None )
      if lock is None:
        lock = threading.Lock()
        sync_locks[ lock_name ] = lock
      
      locks.append( lock )
  
  #//-------------------------------------------------------//
  
  def   acquireLocks( self ):
    locks = []
    
    try:
      for i, lock in enumerate( self.locks ):
        if not lock.acquire( False ):
          raise Exception("Lock '%s' is already acquired." % (self.lock_names[i]))
        
        locks.insert( 0, lock )
    except:
      self.releaseLocks( locks )
      raise
    
    return locks
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   releaseLocks( locks ):
    for lock in locks:
      lock.release()
    
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    if self.number:
      global _sync_value
      
      with _sync_lock:
        _sync_value = _sync_value + self.number
        
        if (_sync_value % self.number) != 0:
          raise Exception( "_sync_value: %s, number: %s, node: %s" % (_sync_value, self.number, node))
        
    time.sleep( self.sleep_interval )
    
    if self.number:  
      with _sync_lock:
        if (_sync_value % self.number) != 0:
          raise Exception( "_sync_value: %s, number: %s, node: %s" % (_sync_value, self.number, node))
        
        _sync_value = _sync_value - self.number
    
    target = [ src for src in node.getSources() ]
    target = self.makeSimpleEntity( target )
    
    # self.releaseLocks( locks )
    
    node.addTargets( target )

#//===========================================================================//

class CopyValueBuilder (Builder):
  
  def   __init__(self, options ):
    self.signature = b''
  
  def   build( self, node ):
    target_entities = []
    
    for source_value in node.getSourceEntities():
      copy_value = SimpleEntity( source_value.get(), name = source_value.name + '_copy' )
      target_entities.append( copy_value )
    
    node.addTargets( target_entities )
  
  def   getTraceTargets( self, node, brief ):
    return tuple( value.name for value in node.getTargetEntities() )
  
  def   getTraceSources( self, node, brief ):
    return tuple( value.name for value in node.getSourceEntities() )


#//===========================================================================//

class ChecksumBuilder (FileBuilder):
  
  NAME_ATTRS = ('replace_ext',)
  SIGNATURE_ATTRS = ('offset', 'length')
  
  def   __init__(self, options, offset, length, replace_ext = False ):
    
    self.offset = offset
    self.length = length
    self.replace_ext = replace_ext
  
  #//-------------------------------------------------------//
  
  def   _buildSrc( self, src, alg ):
    chcksum = fileChecksum( src, self.offset, self.length, alg )
    if self.replace_ext:
      chcksum_filename = os.path.splitext(src)[0]
    else:
      chcksum_filename = src
    
    chcksum_filename += '.%s.chksum' % alg
    
    chcksum_filename = self.getTargetFromSourceFilePath( chcksum_filename )
    
    with open( chcksum_filename, 'wb' ) as f:
      f.write( chcksum.digest() )
    
    return self.makeFileEntity( chcksum_filename, tags = alg )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    target_entities = []
    
    for src in node.getSources():
      target_entities.append( self._buildSrc( src, 'md5' ) )
      target_entities.append( self._buildSrc( src, 'sha512' ) )
    
    node.addTargets( target_entities )
  
  #//-------------------------------------------------------//
  
  def   buildBatch( self, node ):
    for src_value in node.getSourceEntities():
      targets = [ self._buildSrc( src_value.get(), 'md5' ),
                  self._buildSrc( src_value.get(), 'sha512' ) ]
      
      node.addSourceTargets( src_value, targets )

#//===========================================================================//

class ChecksumSingleBuilder (ChecksumBuilder):
  
  split = ChecksumBuilder.splitSingle

#//===========================================================================//

def   _addNodesToBM( builder, src_files, Node = Node ):
  bm = BuildManager()
  try:
    checksums_node = Node( builder, src_files )
    checksums_node2 = Node( builder, checksums_node )
    
    bm.add( [checksums_node] ); bm.selfTest()
    bm.add( [checksums_node2] ); bm.selfTest()
  except Exception:
    bm.close()
    raise
  
  return bm

#//===========================================================================//

def   _build( bm, jobs = 1, keep_going = False, explain = False ):
  try:
    bm.selfTest()
    success = bm.build( jobs = jobs, keep_going = keep_going, explain = explain )
    bm.selfTest()
    if not success:
      bm.printFails()
      raise Exception("Nodes failed")
    
  finally:
    bm.close()
    bm.selfTest()

#//===========================================================================//

def   _buildChecksums( builder, src_files, Node = Node ):
  
  bm = _addNodesToBM( builder, src_files, Node )
  _build( bm )

#//===========================================================================//

class TestBuildManager( AqlTestCase ):
  
  def   eventNodeBuilding( self, settings, node ):
    self.building_nodes += 1
  
  #//-------------------------------------------------------//
  
  def   eventNodeActual( self, settings, node, progress ):
    self.actual_nodes += 1
  
  #//-------------------------------------------------------//
  
  def   eventNodeOutdated( self, settings, node, progress ):
    self.outdated_nodes += 1
  
  #//-------------------------------------------------------//
  
  def   eventNodeRemoved( self, settings, node, progress ):
    self.removed_nodes += 1
  
  #//-------------------------------------------------------//
  
  def   setUp( self ):
    super(TestBuildManager,self).setUp()
    
    self.building_nodes = 0
    addUserHandler( self.eventNodeBuilding )
    
    self.actual_nodes = 0
    addUserHandler( self.eventNodeActual )
    
    self.outdated_nodes = 0
    addUserHandler( self.eventNodeOutdated )
    
    self.removed_nodes = 0
    addUserHandler( self.eventNodeRemoved )
  
  #//-------------------------------------------------------//
  
  def   tearDown( self ):
    removeUserHandler( [  self.eventNodeBuilding,
                          self.eventNodeOutdated,
                          self.eventNodeActual,
                          self.eventNodeRemoved,
                      ] )

    super(TestBuildManager,self).tearDown()
  
  #//-------------------------------------------------------//
  
  def test_bm_deps(self):
    
    bm = BuildManager()
    
    value1 = SimpleEntity( "http://aql.org/download1", name = "target_url1" )
    value2 = SimpleEntity( "http://aql.org/download2", name = "target_url2" )
    value3 = SimpleEntity( "http://aql.org/download3", name = "target_url3" )
    
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
    
    bm.add( [node0] ); bm.selfTest(); self.assertEqual( len(bm), 1 )
    bm.add( [node1] ); bm.selfTest(); self.assertEqual( len(bm), 2 )
    bm.add( [node2] ); bm.selfTest(); self.assertEqual( len(bm), 3 )
    bm.add( [node3] ); bm.selfTest(); self.assertEqual( len(bm), 4 )
    bm.add( [node4] ); bm.selfTest(); self.assertEqual( len(bm), 5 )
    bm.add( [node5] ); bm.selfTest(); self.assertEqual( len(bm), 6 )
    bm.add( [node6] ); bm.selfTest(); self.assertEqual( len(bm), 7 )
    
    node0.depends( node3 ); bm.depends( node0, [node3] ); bm.selfTest()
    node1.depends( node3 ); bm.depends( node1, [node3] ); bm.selfTest()
    node2.depends( node3 ); bm.depends( node2, [node3] ); bm.selfTest()
    node3.depends( node4 ); bm.depends( node3, [node4] ); bm.selfTest()
    node0.depends( node5 ); bm.depends( node0, [node5] ); bm.selfTest()
    node5.depends( node3 ); bm.depends( node5, [node3] ); bm.selfTest()
    
    def   _cyclicDeps( src_node, dep_node ):
      src_node.depends( dep_node ); bm.depends( src_node, [dep_node] )
    
    self.assertRaises(ErrorNodeDependencyCyclic, _cyclicDeps, node4, node3 )
  
  #//-------------------------------------------------------//
  
  def test_bm_build(self):
    
    with Tempdir() as tmp_dir:
      
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      src_files = self.generateSourceFiles( tmp_dir, 5, 201 )
      
      builder = ChecksumBuilder( options, 0, 256 )
      
      self.building_nodes = self.built_nodes = 0
      _buildChecksums( builder, src_files )
      self.assertEqual( self.building_nodes, 2 )
      self.assertEqual( self.building_nodes, self.built_nodes )
      
      #//-------------------------------------------------------//
      
      self.building_nodes = self.built_nodes = 0
      _buildChecksums( builder, src_files )
      self.assertEqual( self.building_nodes, 0 )
      self.assertEqual( self.building_nodes, self.built_nodes )
      
      #//-------------------------------------------------------//
      
      builder = ChecksumBuilder( options, 32, 1024 )
      
      self.building_nodes = self.built_nodes = 0
      _buildChecksums( builder, src_files )
      self.assertEqual( self.building_nodes, 2 )
      self.assertEqual( self.building_nodes, self.built_nodes )
      
      #//-------------------------------------------------------//
      
      self.building_nodes = self.built_nodes = 0
      _buildChecksums( builder, src_files )
      self.assertEqual( self.building_nodes, 0 )
      self.assertEqual( self.building_nodes, self.building_nodes )
  
  #//-------------------------------------------------------//
  
  def test_bm_nodes(self):
    
    def _makeNodes( builder ):
      node1 = Node( builder, value1 )
      copy_node1 = Node( builder, node1 )
      copy2_node1 = Node( builder, copy_node1 )
      node2 = Node( builder, value2 )
      node3 = Node( builder, value3 )
      copy_node3 = Node( builder, node3 )
      
      copy2_node3 = Node( builder, copy_node3 )
      copy2_node3.depends( [node1, copy_node1] )
      return node1, node2, node3, copy_node1, copy_node3, copy2_node1, copy2_node3
    
    with Tempdir() as tmp_dir:
      options = builtinOptions()
      options.build_dir = tmp_dir
    
      bm = BuildManager()
      
      value1 = SimpleEntity( "http://aql.org/download1", name = "target_url1" )
      value2 = SimpleEntity( "http://aql.org/download2", name = "target_url2" )
      value3 = SimpleEntity( "http://aql.org/download3", name = "target_url3" )
      
      builder = CopyValueBuilder( options )
      
      bm.add( _makeNodes( builder ) )
      
      self.built_nodes = 0
      bm.build( jobs = 1, keep_going = False )
      bm.close()
      self.assertEqual( self.built_nodes, 7 )
      
      #// --------- //
      
      bm.add( _makeNodes( builder ) )
      
      self.actual_nodes = 0
      bm.status()
      bm.close()
      self.assertEqual( self.actual_nodes, 7 )
      
      #// --------- //
      
      bm.add( _makeNodes( builder ) )
      
      self.removed_nodes = 0
      bm.clear()
      bm.close()
      self.assertEqual( self.removed_nodes, 7 )
      
      #// --------- //
      
      bm.add( _makeNodes( builder ) )
      
      self.actual_nodes = 0
      self.outdated_nodes = 0
      bm.status()
      bm.close()
      self.assertEqual( self.actual_nodes, 0 )
      self.assertEqual( self.outdated_nodes, 3 )
      
      #// --------- //
      
      nodes = _makeNodes( builder )
      copy_node3 = nodes[4]
      bm.add( nodes )
      
      self.built_nodes = 0
      bm.build( jobs = 1, keep_going = False, nodes = [copy_node3] )
      bm.close()
      self.assertEqual( self.built_nodes, 2 )
      
      #// --------- //
      
      nodes = _makeNodes( builder )
      node2 = nodes[1]; copy_node3  = nodes[4]
      bm.add( nodes )
      
      self.built_nodes = 0
      bm.build( jobs = 1, keep_going = False, nodes = [node2, copy_node3] )
      bm.close()
      self.assertEqual( self.built_nodes, 1 )
      
      #// --------- //
  
  #//-------------------------------------------------------//
  
  def test_bm_check(self):
    
    with Tempdir() as tmp_dir:
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      src_files = self.generateSourceFiles( tmp_dir, 3, 201 )
      
      builder = ChecksumBuilder( options, 0, 256, replace_ext = True )
      
      self.building_nodes = self.built_nodes = 0
      _buildChecksums( builder, src_files )
      self.assertEqual( self.building_nodes, 2 )
      self.assertEqual( self.building_nodes, self.built_nodes )
      
      bm = _addNodesToBM( builder, src_files )
      try:
        self.actual_nodes = self.outdated_nodes = 0
        bm.status(); bm.selfTest()
        
        self.assertEqual( self.outdated_nodes, 0)
        self.assertEqual( self.actual_nodes, 2 )
        
      finally:
        bm.close()
  
  #//-------------------------------------------------------//
  
  def test_bm_batch(self):
    
    with Tempdir() as tmp_dir:
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      src_files = self.generateSourceFiles( tmp_dir, 3, 201 )
      
      builder = ChecksumBuilder( options, 0, 256, replace_ext = True )
      
      self.building_nodes = self.built_nodes = 0
      _buildChecksums( builder, src_files, Node = BatchNode )
      self.assertEqual( self.building_nodes, 2 )
      self.assertEqual( self.building_nodes, self.built_nodes )
      
      bm = _addNodesToBM( builder, src_files, Node = BatchNode )
      try:
        self.actual_nodes = self.outdated_nodes = 0
        bm.status(); bm.selfTest()
        
        self.assertEqual( self.outdated_nodes, 0)
        self.assertEqual( self.actual_nodes, 2 )
        
      finally:
        bm.close()
  
  #//-------------------------------------------------------//
  
  def test_bm_rebuild(self):
    
    with Tempdir() as tmp_dir:
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      num_src_files = 3
      src_files = self.generateSourceFiles( tmp_dir, num_src_files, 201 )
      
      bm = BuildManager()
      
      self.building_nodes = self.built_nodes = 0
      self.actual_nodes = self.outdated_nodes = 0
      
      builder = ChecksumSingleBuilder( options, 0, 256 )
      
      src_entities = []
      for s in src_files:
        src_entities.append( FileChecksumEntity( s ) )
      
      node = Node( builder, src_entities )
      node = Node( builder, node )
      node = Node( builder, node )
      
      bm.add( [node] )
      _build( bm )
      
      self.assertEqual( self.building_nodes, num_src_files * 7 )
      
      #//-------------------------------------------------------//
      
      self.actual_nodes = self.outdated_nodes = 0
      
      bm = BuildManager()
      builder = ChecksumSingleBuilder( options, 0, 256 )
      
      node = Node( builder, src_entities )
      bm.add( [node] ); bm.selfTest()
      bm.status(); bm.selfTest()
      
      self.assertEqual( self.outdated_nodes, 0 )
      self.assertEqual( self.actual_nodes, num_src_files )
  
  #//-------------------------------------------------------//
  
  def test_bm_tags(self):
    
    with Tempdir() as tmp_dir:
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      num_src_files = 3
      src_files = self.generateSourceFiles( tmp_dir, num_src_files, 201 )
      
      builder = ChecksumSingleBuilder( options, 0, 256 )
      
      bm = BuildManager()
      
      self.built_nodes = 0
      
      node = Node( builder, src_files )
      
      node_md5 = Node( builder, node.at('md5') )
      
      bm.add( [node_md5] )
      
      _build( bm )
      
      self.assertEqual( self.built_nodes, num_src_files * 2 )
      
      #//-------------------------------------------------------//
      
      self.touchCppFile( src_files[0] )
      
      bm = BuildManager()
      
      self.built_nodes = 0
      
      node = Node( builder, src_files )
      
      node_md5 = Node( builder, node.at('md5') )
      
      bm.add( [node_md5] )
      
      _build( bm )
      
      self.assertEqual( self.built_nodes, 2 )
  
  #//-------------------------------------------------------//
  
  def test_bm_tags_batch(self):
    
    with Tempdir() as tmp_dir:
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      num_src_files = 3
      src_files = self.generateSourceFiles( tmp_dir, num_src_files, 201 )
      
      builder = ChecksumBuilder( options, 0, 256 )
      single_builder = ChecksumSingleBuilder( options, 0, 256 )
      bm = BuildManager()
      
      self.built_nodes = 0
      
      node = BatchNode( builder, src_files )
      
      node_md5 = Node( single_builder, node.at('md5') )
      
      bm.add( [node_md5] )
      
      _build( bm )
      
      self.assertEqual( self.built_nodes, num_src_files + 1 )
      
      #//-------------------------------------------------------//
      
      self.touchCppFile( src_files[0] )
      
      bm = BuildManager()
      
      self.built_nodes = 0
      
      node = BatchNode( builder, src_files )
      
      node_md5 = Node( single_builder, node.at('md5') )
      
      bm.add( [node_md5] )
      
      _build( bm )
      
      self.assertEqual( self.built_nodes, 2 )

  #//-------------------------------------------------------//
  
  def test_bm_conflicts(self):
    
    with Tempdir() as tmp_dir:
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      num_src_files = 3
      src_files = self.generateSourceFiles( tmp_dir, num_src_files, 201 )
      
      bm = BuildManager()
      
      self.built_nodes = 0
      
      builder1 = ChecksumSingleBuilder( options, 0, 256 )
      builder2 = ChecksumSingleBuilder( options, 0, 1024 )
      
      node1 = Node( builder1, src_files )
      node2 = Node( builder2, src_files )
      # node1 = Node( builder1, node1 )
      # node2 = Node( builder2, node2 )
      
      bm.add( [node1, node2])
      self.assertRaises( ErrorNodeSignatureDifferent, _build, bm )
  
  #//-------------------------------------------------------//
  
  def test_bm_no_conflicts(self):
    
    with Tempdir() as tmp_dir:
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      num_src_files = 3
      src_files = self.generateSourceFiles( tmp_dir, num_src_files, 201 )
      
      bm = BuildManager()
      
      self.built_nodes = 0
      
      builder1 = ChecksumSingleBuilder( options, 0, 256 )
      builder2 = ChecksumSingleBuilder( options, 0, 256 )
      
      node1 = Node( builder1, src_files )
      node2 = Node( builder2, src_files )
      node1 = Node( builder1, node1 )
      node2 = Node( builder2, node2 )
      
      bm.add( [node1, node2] )
      _build( bm )
      
      self.assertEqual( self.built_nodes, 3 * 3 )
  
  #//-------------------------------------------------------//
  
  def test_bm_node_build_fail(self):
    
    with Tempdir() as tmp_dir:
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      bm = BuildManager()
      
      self.built_nodes = 0
      
      builder = FailedBuilder( options )
      
      nodes = [ Node( builder, SimpleEntity("123-%s" % (i,)) ) for i in range(4)]
      bm.add( nodes )
      
      self.assertRaises( Exception, _build, bm )
      self.assertEqual( self.built_nodes, 0 )
  
  #//-------------------------------------------------------//
  
  def test_bm_sync_nodes(self):
    
    with Tempdir() as tmp_dir:
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      bm = BuildManager()
      
      self.built_nodes = 0
      
      nodes = [ Node( SyncValueBuilder( options, name = "%s" % i, number = n ), SimpleEntity("123-%s" % i) ) for i,n in zip( range(4), [3,5,7,11] ) ] 
      bm.add( nodes )
      bm.sync( nodes )
      
      _build( bm, jobs = 4 )
  
  #//-------------------------------------------------------//
  
  @skip
  def test_bm_sync_modules(self):
    
    with Tempdir() as tmp_dir:
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      bm = BuildManager()
      
      self.built_nodes = 0
      
      """
             10    11__
            / | \ / \  \
          20 21  22  23 24
         /  \ | / \   \ |
        30    31   32  33
      """
      
      node30 = Node( SyncValueBuilder( options, name = "30", number = 7 ), SimpleEntity("30") )
      node31 = Node( SyncValueBuilder( options, name = "31", number = 0, sleep_interval = 0 ), SimpleEntity("31") )
      node32 = Node( SyncValueBuilder( options, name = "32", number = 0, sleep_interval = 0 ), SimpleEntity("32") )
      node33 = Node( SyncValueBuilder( options, name = "33", number = 17 ), SimpleEntity("33") )
      
      node20 = Node( SyncValueBuilder( options, name = "20", number = 7 ), (node30, node31) )
      node21 = Node( SyncValueBuilder( options, name = "21", number = 7 ), (node31,) )
      node22 = Node( SyncValueBuilder( options, name = "22", number = 0, sleep_interval = 5), (node31, node32) )
      node23 = Node( SyncValueBuilder( options, name = "23", number = 17 ), (node33,) )
      node24 = Node( SyncValueBuilder( options, name = "24", number = 17 ), (node33,) )
       
      node10 = Node( SyncValueBuilder( options, name = "10", number = 7 ), (node20, node21, node22) )
      node11 = Node( SyncValueBuilder( options, name = "11", number = 17 ), (node22, node23, node24) )
      
      # print( "node30: %s" % node30 )
      # print( "node31: %s" % node31 )
      # print( "node32: %s" % node32 )
      # print( "node33: %s" % node33 )
      # 
      # print( "node20: %s" % node20 )
      # print( "node21: %s" % node21 )
      # print( "node22: %s" % node22 )
      # print( "node23: %s" % node23 )
      # print( "node24: %s" % node24 )
      # 
      # print( "node10: %s" % node10 )
      # print( "node11: %s" % node11 )
      
      bm.add( (node10, node11) )
      bm.sync( (node10, node11), deep = True )
      
      _build( bm, jobs = 4 )
  
  #//-------------------------------------------------------//
  
  def test_bm_require_modules(self):
    
    with Tempdir() as tmp_dir:
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      bm = BuildManager()
      
      self.built_nodes = 0
      
      """
             10    11__
            / | \ / \  \
          20 21  22  23 24
         /  \ | / \   \ |
        30    31   32  33
      """
      
      node30 = Node( SyncValueBuilder( options, name = "30", number = 7 ), SimpleEntity("30") )
      node31 = Node( SyncValueBuilder( options, name = "31", number = 0, sleep_interval = 0 ), SimpleEntity("31") )
      node32 = Node( SyncValueBuilder( options, name = "32", number = 0, sleep_interval = 0 ), SimpleEntity("32") )
      node33 = Node( SyncValueBuilder( options, name = "33", number = 17 ), SimpleEntity("33") )
      
      node20 = Node( SyncValueBuilder( options, name = "20", number = 7 ), (node30, node31) )
      node21 = Node( SyncValueBuilder( options, name = "21", number = 7 ), (node31,) )
      node22 = Node( SyncValueBuilder( options, name = "22", number = 0, sleep_interval = 5), (node31, node32) )
      node23 = Node( SyncValueBuilder( options, name = "23", number = 17 ), (node33,) )
      node24 = Node( SyncValueBuilder( options, name = "24", number = 17 ), (node33,) )
       
      node10 = Node( SyncValueBuilder( options, name = "10", number = 7 ), (node20, node21, node22) )
      node11 = Node( SyncValueBuilder( options, name = "11", number = 17 ), (node22, node23, node24) )
      
      # print( "node30: %s" % node30 )
      # print( "node31: %s" % node31 )
      # print( "node32: %s" % node32 )
      # print( "node33: %s" % node33 )
      # 
      # print( "node20: %s" % node20 )
      # print( "node21: %s" % node21 )
      # print( "node22: %s" % node22 )
      # print( "node23: %s" % node23 )
      # print( "node24: %s" % node24 )
      # 
      # print( "node10: %s" % node10 )
      # print( "node11: %s" % node11 )
      
      bm.add( (node10, node11) )
      bm.moduleDepends( node10, [node11] )
      
      _build( bm, jobs = 4 )
  
  #//-------------------------------------------------------//
  
  @skip
  def test_bm_node_names(self):
    
    with Tempdir() as tmp_dir:
      src_files = self.generateSourceFiles( tmp_dir, 3, 201 )
      options = builtinOptions()
      options.build_dir = tmp_dir
      
      builder = ChecksumBuilder( options, 0, 256, replace_ext = False )
      bm = BuildManager()
      try:
        src_entities = []
        for s in src_files:
          src_entities.append( FileChecksumEntity( s ) )
        
        node0 = Node( builder, None )
        node1 = Node( builder, src_entities )
        node2 = Node( builder, node1 )
        node3 = Node( builder, node2 )
        node4 = Node( builder, node3 )
        
        bm.add( [node0, node1, node2, node3, node4] )
        
        bm.build(1, False)
        
        print("node2: %s" % str(node4) )
        print("node2: %s" % str(node3) )
        print("node2: %s" % str(node2) )
        print("node1: %s" % str(node1) )
        print("node0: %s" % str(node0) )
      
      finally:
        bm.close()

#//===========================================================================//

def   _generateNodeTree( bm, builder, node, depth ):
  while depth:
    node = Node( builder, node )
    bm.add( [ node ] )
    depth -= 1

#//===========================================================================//

@skip
class TestBuildManagerSpeed( AqlTestCase ):
  
  def test_bm_deps_speed(self):
    
    bm = BuildManager()
    
    value = SimpleEntity( "http://aql.org/download", name = "target_url1" )
    builder = CopyValueBuilder()
    
    node = Node( builder, value )
    bm.add( [node] )
    
    _generateNodeTree( bm, builder, node, 5000 )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
