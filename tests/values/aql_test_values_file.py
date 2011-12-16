import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_temp_file import Tempfile
from aql_value import Value, NoContent
from aql_depends_value import DependsValue
from aql_value_pickler import ValuePickler, pickleable
from aql_data_file import DataFile
from aql_values_file import ValuesFile


#//===========================================================================//

@testcase
def test_value_file(self):
  
  with Tempfile() as tmp:
    vfile = ValuesFile( tmp.name )
    vfile.selfTest()
    
    value1 = Value( "target_url1", "http://aql.org/download" )
    value2 = Value( "target_url2", "http://aql.org/download2" )
    value3 = Value( "target_url3", "http://aql.org/download3" )
    
    values = [ value1, value2, value3 ]
    
    vfile.addValues( values ); vfile.selfTest()
    
    s_values = vfile.findValues( values ); vfile.selfTest()
    
    self.assertEqual( values, s_values )
    
    vfile.clear(); vfile.selfTest()
    #//-------------------------------------------------------//
    
    dep_value = DependsValue( "urls", values )
    values.insert( 0, dep_value )
    
    vfile.addValues( values ); vfile.selfTest()
    s_values = vfile.findValues( values ); vfile.selfTest()
    
    self.assertEqual( values, s_values )
    
    #//-------------------------------------------------------//
    
    vfile2 = ValuesFile( tmp.name ); vfile2.selfTest()
    s_values2 = vfile2.findValues( values ); vfile.selfTest()
    self.assertEqual( values, s_values2 )
    
    #//-------------------------------------------------------//
    
    values[0] = DependsValue( "urls", reversed(values[1:]) )
    
    vfile2.addValues( values ); vfile2.selfTest()
    s_values = vfile.findValues( values ); vfile.selfTest()
    self.assertEqual( values, s_values )
    
    #//-------------------------------------------------------//
    
    value1.content = "http://aql.org/download1"
    
    vfile2.addValues( [ value1 ] ); vfile2.selfTest()
    s_value1 = vfile.findValues( [ value1 ] )[0]; vfile.selfTest()
    self.assertEqual( value1, s_value1 )
    
    #//-------------------------------------------------------//
    
    dep_value = DependsValue( "urls", reversed(values) )
    
    vfile2.addValues( [dep_value] ); vfile2.selfTest()
    s_dep_value = vfile.findValues( [dep_value] )[0]; vfile.selfTest()
    self.assertNotEqual( dep_value, s_dep_value )
    self.assertIsInstance( s_dep_value.content, NoContent)
    
    #//-------------------------------------------------------//
    
    dep_value2 = DependsValue( "urls2", [ dep_value ] )
    vfile2.addValues( [dep_value2] ); vfile2.selfTest()
    
    dep_value = DependsValue( "urls", [ dep_value2 ] )
    vfile2.addValues( [dep_value] ); vfile2.selfTest()
    
    s_dep_value = vfile.findValues( [dep_value] )[0]; vfile.selfTest()
    
    #//-------------------------------------------------------//
    
    dep_value = DependsValue( "urls", [ value1 ] )
    vfile.addValues( [dep_value, value1] ); vfile.selfTest()
    
    df = DataFile( tmp.name )
    
    value1_key, value1 = vfile.xash.find( value1 )
    del df[value1_key]
    
    s_value1 = vfile.findValues( [value1] )[0]; vfile.selfTest()
    self.assertNotEqual( s_value1.content, value1.content )
    
    s_value1 = vfile2.findValues( [value1] )[0]; vfile.selfTest()
    self.assertNotEqual( s_value1.content, value1.content )

#//===========================================================================//

@testcase
def test_value_file_2(self):
  
  with Tempfile() as tmp:
    vfile = ValuesFile( tmp.name )
    vfile.selfTest()
    
    value1 = Value( "target_url1", "http://aql.org/download" )
    value2 = Value( "target_url2", "http://aql.org/download2" )
    value3 = Value( "target_url3", "http://aql.org/download3" )
    
    values = [ value1, value2, value3 ]
    
    dep_value1 = DependsValue( "urls1", values )
    
    value4 = Value( "target_url4", "http://aql.org/download4" )
    dep_value2 = DependsValue( "urls2", [ dep_value1, value4 ] )
    
    value5 = Value( "target_url5", "http://aql.org/download5" )
    dep_value3 = DependsValue( "urls3", [ dep_value1, value5 ] )
    
    value6 = Value( "target_url6", "http://aql.org/download6" )
    dep_value4 = DependsValue( "urls4", [ dep_value1, dep_value2, dep_value3, value6 ] )
    
    
    all_dep_values = [dep_value4, dep_value3, dep_value2, dep_value1]
    
    all_values = all_dep_values + values +[ value4, value5, value6 ]
    
    vfile.addValues( all_values ); vfile.selfTest()
    self.assertTrue( vfile.actual( all_values ) )
    
    vfile.close()
    vfile.open( tmp.name ); vfile.selfTest()
    
    s_all_values = vfile.findValues( all_values ); vfile.selfTest()
    for value, s_value in zip( all_values, s_all_values ):
      self.assertEqual( value, s_value )
    
    value3 = Value( "target_url3", "http://aql.org/download3/0" )
    
    vfile.addValues( [value3] ); vfile.selfTest()
    
    s_all_dep_values = vfile.findValues( all_dep_values ); vfile.selfTest()
    self.assertFalse( vfile.actual( all_dep_values ) )
    for value, s_value in zip( all_dep_values, s_all_dep_values ):
      self.assertEqual( value.name, s_value.name )
      self.assertNotEqual( value.content, s_value.content )
      self.assertIsInstance( s_value.content, NoContent )

#//===========================================================================//

@testcase
def test_value_file_3(self):
  
  with Tempfile() as tmp:
    vfile = ValuesFile( tmp.name )
    vfile.selfTest()
    
    values = []
    
    value1 = Value( "target_url1", "http://aql.org/download" )
    value2 = Value( "target_url2", "http://aql.org/download2" )
    dep_value = DependsValue( "urls1", [ value1, value2 ] )
    
    values += [value1, value2, dep_value ]
    
    vfile.addValues( values ); vfile.selfTest()
    
    value1 = Value( "target_url3", "http://aql.org/download3" )
    value2 = Value( "target_url4", "http://aql.org/download4" )
    
    dep_value = DependsValue( "urls1", [ value1, value2 ] )
    vfile.addValues( [ dep_value, value1, value2 ] ); vfile.selfTest()

#//===========================================================================//

@skip
@testcase
def   test_value_file_speed(self):
  
  values = []
  for i in range(0, 100000):
    value = Value( "target_url%s" % i, "http://aql.org/download" )
    values.append( value )
  
  with Tempfile() as tmp:
    vf = ValuesFile( tmp.name )
    
    t = lambda addValues = vf.addValues, values = values: addValues( values )
    t = timeit.timeit( t, number = 1 )
    print("value picker: %s" % t)


#//===========================================================================//

if __name__ == "__main__":
  runTests()
