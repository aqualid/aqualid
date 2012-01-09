import sys
import os.path
import timeit
import hashlib
import shutil

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_temp_file import Tempfile
from aql_value import Value, NoContent
from aql_file_value import FileValue, FileContentTimeStamp, FileContentChecksum
from aql_values_file import ValuesFile
from aql_node import Node
from aql_builder import Builder
from aql_build_manager import BuildManager

#//===========================================================================//

class CopyValueBuilder (Builder):
  
  __slots__ = ('name', 'long_name')
  
  def   __init__(self, name ):
    chcksum = hashlib.md5()
    chcksum.update( name.encode() )
    
    self.name = chcksum.digest()
    self.long_name = name
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    target_values = []
    
    for source_value in node.sources():
      target_values.append( Value( source_value.name + '_copy', source_value.content ) )
    
    return target_values, [], []
  
  #//-------------------------------------------------------//
  
  def   values( self ):
    return [Value(self.name, "")]

#//===========================================================================//

@testcase
def test_bm_deps(self):
  
  bm = BuildManager()
  
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
  
  bm.addNode( node0 ); bm.selfTest(); self.assertEqual( len(bm), 1 )
  bm.addNode( node1 ); bm.selfTest(); self.assertEqual( len(bm), 2 )
  bm.addNode( node2 ); bm.selfTest(); self.assertEqual( len(bm), 3 )
  bm.addNode( node3 ); bm.selfTest(); self.assertEqual( len(bm), 4 )
  bm.addNode( node4 ); bm.selfTest(); self.assertEqual( len(bm), 5 )
  bm.addNode( node5 ); bm.selfTest(); self.assertEqual( len(bm), 6 )
  
  node0.addDeps( node3 ); bm.addDeps( node0, node3 ); bm.selfTest()
  node1.addDeps( node3 ); bm.addDeps( node1, node3 ); bm.selfTest()
  node2.addDeps( node3 ); bm.addDeps( node2, node3 ); bm.selfTest()
  node3.addDeps( node4 ); bm.addDeps( node3, node4 ); bm.selfTest()
  node0.addDeps( node5 ); bm.addDeps( node0, node5 ); bm.selfTest()
  node5.addDeps( node3 ); bm.addDeps( node5, node3 ); bm.selfTest()
  #~ node4.addDeps( node3 ); bm.addDeps( node4, node3 ); bm.selfTest()
  
#//===========================================================================//

def   _generateNodeTree( bm, builder, node, depth ):
  while depth:
    node = Node( builder, node )
    bm.addNode( node )
    depth -= 1

#//===========================================================================//

@skip
@testcase
def test_bm_deps_speed(self):
  
  bm = BuildManager()
  
  value = Value( "target_url1", "http://aql.org/download" )
  builder = CopyValueBuilder("CopyValueBuilder")
  
  node = Node( builder, value )
  bm.addNode( node )
  
  _generateNodeTree( bm, builder, node, 5000 )
  

#//===========================================================================//

if __name__ == "__main__":
  runTests()
