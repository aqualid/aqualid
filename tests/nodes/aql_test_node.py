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
  
  def   build( self, source_values ):
    target_values = []
    itarget_values = []
    
    for source_value in source_values:
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
  
  __slots__ = ('name', 'long_name', 'ext')
  
  def   __init__(self, name, ext ):
    chcksum = hashlib.md5()
    chcksum.update( name.encode() )
    
    self.name = chcksum.digest()
    self.long_name = name
    self.ext = ext
  
  #//-------------------------------------------------------//
  
  def   build( self, source_values ):
    target_values = []
    
    for source_value in source_values:
      new_name = source_value.name + '.' + self.ext
      shutil.copy( source_value.name, new_name )
      
      target_values.append( FileValue( new_name ) )
    
    return target_values, [], []
  
  #//-------------------------------------------------------//
  
  def   values( self ):
    return [StringValue(self.name, self.ext)]


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
          
          builder = CopyBuilder("CopyBuilder", "tmp")
          
          node = Node( builder, [value1, value2] )
          
          self.assertFalse( node.actual( vfile ) )
          node.build( vfile )
          self.assertTrue( node.actual( vfile ) )
          
          node = Node( builder, [value1, value2] )
          self.assertTrue( node.actual( vfile ) )
          node.build( vfile )
          self.assertTrue( node.actual( vfile ) )
          
          for tmp_file in node.target_values:
            tmp_files.append( tmp_file.name )
          
          builder = CopyBuilder("CopyBuilder", "ttt")
          node = Node( builder, [value1, value2] )
          self.assertFalse( node.actual( vfile ) )
          
          node.build( vfile )
          self.assertTrue( node.actual( vfile ) )
          
          for tmp_file in node.target_values:
            tmp_files.append( tmp_file.name )
          
  finally:
    for tmp_file in tmp_files:
      try:
        os.remove( tmp_file )
      except OSError:
        pass


#//===========================================================================//

@skip
@testcase
def   test_node_speed(self):
  
  values = []
  for i in range(0, 100000):
    value = StringValue( "target_url%s" % i, "http://aql.org/download" )
    values.append( value )
  
  with Tempfile() as tmp:
    vf = ValuesFile( tmp.name )
    
    t = lambda addValues = vf.addValues, values = values: addValues( values )
    t = timeit.timeit( t, number = 1 )
    print("value picker: %s" % t)


#//===========================================================================//

if __name__ == "__main__":
  runTests()
