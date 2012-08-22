import sys
import os.path
import shutil

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_utils import fileChecksum, printStacks
from aql_temp_file import Tempfile, Tempdir
from aql_value import Value, NoContent
from aql_file_value import FileValue, FileContentTimeStamp, FileContentChecksum
from aql_node import Node
from aql_errors import NodeHasCyclicDependency
from aql_build_manager import BuildManager
from aql_event_manager import event_manager
from aql_event_handler import EventHandler

from gcc import GccCompileCppBuilder

#//===========================================================================//

SRC_FILE_TEMPLATE = """
#include <cstdio>
#include "%s.h"

void  %s()
{}
"""

HDR_FILE_TEMPLATE = """
#ifndef HEADER_%s_INCLUDED
#define HEADER_%s_INCLUDED

extern void  %s();

#endif
"""

#//===========================================================================//

def   _generateSrcFile( name, dir ):
  src = Tempfile( dir = dir )
  
  src_content = SRC_FILE_TEMPLATE % ( name, 'foo_' + name )
  hdr_content = HDR_FILE_TEMPLATE % ( name, name, 'foo_' + name )
  
  src_file = os.path.join( dir, name + '.cpp' )
  hdr_file = os.path.join( dir, name + '.h' )
  
  with open( src_file, 'wb' ) as f:
    f.write( src_content )
  
  with open( hdr_file, 'wb' ) as f:
    f.write( hdr_content )
  
  return src_file, hdr_file

#//===========================================================================//

class TestToolGcc( AqlTestCase ):

  def test_gcc_compile(self):
    
    event_manager.setHandlers( EventHandler() )
    
    with Tempdir() as tmp_dir:
      _generateSrcFile( 'foo', str( tmp_dir ) )
  
  #//-------------------------------------------------------//
  
  @skip
  def test_bm_node_names(self):
    
    event_manager.reset()
    event_manager.addHandlers( EventHandler() )
    
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
class TestBuildManagerSpeed( AqlTestCase ):
  def test_bm_deps_speed(self):
    
    event_manager.reset()
    event_manager.addHandlers( EventHandler() )
    
    bm = BuildManager()
    
    value = Value( "target_url1", "http://aql.org/download" )
    builder = CopyValueBuilder("CopyValueBuilder")
    
    node = Node( builder, value )
    bm.addNodes( node )
    
    _generateNodeTree( bm, builder, node, 5000 )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
