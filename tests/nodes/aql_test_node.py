import sys
import os.path
import timeit
import hashlib
import shutil

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_temp_file import Tempfile
from aql_value import Value, NoContent
from aql_str_value import StringValue
from aql_file_value import FileValue
from aql_depends_value import DependsValue
from aql_values_file import ValuesFile
from aql_node import Node
from aql_builder import Builder

#//===========================================================================//

class ChecksumBuilder (Builder):
  
  __slots__ = ('name', 'long_name')
  
  def   __init__(self, name ):
    chcksum = hashlib.md5()
    chcksum.update( name.encode() )
    
    self.name = chcksum.digest()
    self.long_name = name
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
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
  
  def   values( self ):
    return [StringValue(self.name, "")]

#//===========================================================================//

class CopyBuilder (Builder):
  
  __slots__ = ('name', 'long_name', 'ext', 'iext')
  
  def   __init__(self, name, ext, iext ):
    chcksum = hashlib.md5()
    chcksum.update( name.encode() )
    
    self.name = chcksum.digest()
    self.long_name = name
    self.ext = ext
    self.iext = iext
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    target_values = []
    itarget_values = []
    idep_values = []
    
    idep = Value( ",".join(node.long_name) + "CopyBuilderDep", node.name )
    
    for source_value in node.sources():
      new_name = source_value.name + '.' + self.ext
      new_iname = source_value.name + '.' + self.iext
      
      shutil.copy( source_value.name, new_name )
      shutil.copy( source_value.name, new_iname )
      
      target_values.append( FileValue( new_name ) )
      itarget_values.append( FileValue( new_iname ) )
    
    return target_values, itarget_values, [idep]
  
  #//-------------------------------------------------------//
  
  def   values( self ):
    return [StringValue(self.name, self.ext + '|' + self.iext)]


#//===========================================================================//

@testcase
def test_node_value(self):
  
  with Tempfile() as tmp:
    
    vfile = ValuesFile( tmp.name )
    
    value1 = StringValue( "target_url1", "http://aql.org/download" )
    value2 = StringValue( "target_url2", "http://aql.org/download2" )
    value3 = StringValue( "target_url3", "http://aql.org/download3" )
    
    builder = ChecksumBuilder("ChecksumBuilder")
    
    node = Node( builder, [value1, value2, value3] )
    
    self.assertFalse( node.actual( vfile ) )
    node.build( vfile )
    self.assertTrue( node.actual( vfile ) )
    
    node = Node( builder, [value1, value2, value3] )
    self.assertTrue( node.actual( vfile ) )
    node.build( vfile )
    self.assertTrue( node.actual( vfile ) )

#//===========================================================================//

def   _rebuildNode( self, vfile, builder, values, deps, tmp_files):
  node = Node( builder, values )
  node.addDeps( deps )
  
  self.assertFalse( node.actual( vfile ) )
  node.build( vfile )
  self.assertTrue( node.actual( vfile ) )
  
  node = Node( builder, values )
  node.addDeps( deps )
  
  self.assertTrue( node.actual( vfile ) )
  node.build( vfile )
  self.assertTrue( node.actual( vfile ) )
  
  for tmp_file in node.target_values:
    tmp_files.append( tmp_file.name )
  
  for tmp_file in node.itarget_values:
    tmp_files.append( tmp_file.name )
  
  return node

#//=======================================================//

@testcase
def test_node_file(self):
  
  try:
    tmp_files = []
    
    with Tempfile() as tmp:
      
      vfile = ValuesFile( tmp.name )
      
      with Tempfile() as tmp1:
        with Tempfile() as tmp2:
          value1 = FileValue( tmp1.name )
          value2 = FileValue( tmp2.name )
          
          builder = CopyBuilder("CopyBuilder", "tmp", "i")
          node = _rebuildNode( self, vfile, builder, [value1, value2], [], tmp_files )
          
          builder = CopyBuilder("CopyBuilder", "ttt", "i")
          node = _rebuildNode( self, vfile, builder, [value1, value2], [], tmp_files )
          
          builder = CopyBuilder("CopyBuilder", "ttt", "d")
          node = _rebuildNode( self, vfile, builder, [value1, value2], [], tmp_files )
          
          tmp1.write(b'123')
          tmp1.flush()
          value1 = FileValue( tmp1.name )
          node = _rebuildNode( self, vfile, builder, [value1, value2], [], tmp_files )
          
          with Tempfile() as tmp3:
            value3 = FileValue( tmp3.name )
            node3 = _rebuildNode( self, vfile, builder, [value3], [], tmp_files )
            node = _rebuildNode( self, vfile, builder, [value1, node3], [], tmp_files )
            
            builder3 = CopyBuilder("CopyBuilder", "xxx", "3")
            node3 = _rebuildNode( self, vfile, builder3, [value3], [], tmp_files )
            node = _rebuildNode( self, vfile, builder, [value1, node3], [], tmp_files )
            node = _rebuildNode( self, vfile, builder, [value1], [node3], tmp_files )
            
            dep = StringValue( "dep1", "1" )
            node = _rebuildNode( self, vfile, builder, [value1, node3], [dep], tmp_files )
            
            dep = StringValue( "dep1", "11" )
            node = _rebuildNode( self, vfile, builder, [value1, node3], [dep], tmp_files )
            node3 = _rebuildNode( self, vfile, builder3, [value1], [], tmp_files )
            node = _rebuildNode( self, vfile, builder, [value1], [node3], tmp_files )
            node3 = _rebuildNode( self, vfile, builder3, [value2], [], tmp_files )
            node = _rebuildNode( self, vfile, builder, [value1], [node3], tmp_files )
            
            with open( node.targets()[0].name, 'wb' ) as f:
              f.write( b'333' )
              f.flush()
            
            node = _rebuildNode( self, vfile, builder, [value1], [node3], tmp_files )
            
            with open( node.sideEffects()[0].name, 'wb' ) as f:
              f.write( b'abc' )
              f.flush()
            
            node = _rebuildNode( self, vfile, builder, [value1], [node3], tmp_files )
            
            v = Value( node.idep_values[0].name, None )
            vfile.addValues( [v] )
            
            node = _rebuildNode( self, vfile, builder, [value1], [node3], tmp_files )
          
  finally:
    for tmp_file in tmp_files:
      try:
        os.remove( tmp_file )
      except OSError:
        pass

#//===========================================================================//

if __name__ == "__main__":
  runTests()
