import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))
from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempfile, DataFile
from aql.values import Value, NoContent, DependsValue, ValuesFile

#//===========================================================================//

class TestValuesFile( AqlTestCase ):
  
  def test_values_file(self):
    with Tempfile() as tmp:
      with ValuesFile( tmp.name ) as vfile:
        vfile.selfTest()
        
        value1 = Value( name = "target_url1", content = "http://aql.org/download" )
        value2 = Value( name = "target_url2", content = "http://aql.org/download2" )
        value3 = Value( name = "target_url3", content = "http://aql.org/download3" )
        
        values = [ value1, value2, value3 ]
        
        vfile.addValues( values ); vfile.selfTest()
        
        s_values = vfile.findValues( values ); vfile.selfTest()
        
        self.assertEqual( values, s_values )
        
        vfile.clear(); vfile.selfTest()
        #//-------------------------------------------------------//
        
        dep_value = DependsValue( name = "urls", content = values )
        values.append( dep_value )
        
        vfile.addValues( values ); vfile.selfTest()
        s_values = vfile.findValues( values ); vfile.selfTest()
        
        self.assertEqual( values[-1].content, s_values[-1].content )
        
        #//-------------------------------------------------------//
        
        dep_value = DependsValue( name = "urls", content = [ value1 ] )
        vfile.addValues( [dep_value, value1] ); vfile.selfTest()
        
        s_dep_value = vfile.findValues( [dep_value] )[0]; vfile.selfTest()
        self.assertEqual( dep_value, s_dep_value )
        
        value1 = Value( name = value1.name, content = "abc" )
        
        vfile.addValues( [value1] ); vfile.selfTest()
        
        s_dep_value = vfile.findValues( [dep_value] )[0]; vfile.selfTest()
        self.assertNotEqual( dep_value, s_dep_value )

  #//===========================================================================//

  def test_value_file_2(self):
    with Tempfile() as tmp:
      vfile = ValuesFile( tmp.name )
      try:
        vfile.selfTest()
        
        value1 = Value( name = "target_url1", content = "http://aql.org/download" )
        value2 = Value( name = "target_url2", content = "http://aql.org/download2" )
        value3 = Value( name = "target_url3", content = "http://aql.org/download3" )
        
        values = [ value1, value2, value3 ]
        
        dep_value1 = DependsValue( name = "urls1", content = values )
        
        value4 = Value( name = "target_url4", content = "http://aql.org/download4" )
        dep_value2 = DependsValue( name = "urls2", content = [ dep_value1, value4 ] )
        
        value5 = Value( name = "target_url5", content = "http://aql.org/download5" )
        dep_value3 = DependsValue( name = "urls3", content = [ dep_value1, value5 ] )
        
        value6 = Value( name = "target_url6", content = "http://aql.org/download6" )
        dep_value4 = DependsValue( name = "urls4", content = [ dep_value1, dep_value2, dep_value3, value6 ] )
        
        all_dep_values = [dep_value1, dep_value2, dep_value3, dep_value4]
        
        all_values = values + [ value4, value5, value6 ] + all_dep_values
        
        vfile.addValues( all_values ); vfile.selfTest()
        self.assertEqual( vfile.findValues( all_values ), all_values )
        
        vfile.close()
        vfile.open( tmp.name ); vfile.selfTest()
        
        s_all_values = vfile.findValues( all_values ); vfile.selfTest()
        for value, s_value in zip( all_values, s_all_values ):
          self.assertEqual( value, s_value )
        
        value3 = Value( name = "target_url3", content = "http://aql.org/download3/0" )
        
        vfile.addValues( [value3] ); vfile.selfTest()
        
        s_all_dep_values = vfile.findValues( all_dep_values ); vfile.selfTest()
        self.assertNotEqual( vfile.findValues( all_dep_values ), all_dep_values )
        for value, s_value in zip( all_dep_values, s_all_dep_values ):
          self.assertEqual( value.name, s_value.name )
          self.assertNotEqual( value.content, s_value.content )
          self.assertIs( s_value.content, NoContent )
      finally:
        vfile.close()
    
  #//===========================================================================//

  def test_value_file_3(self):
    with Tempfile() as tmp:
      with ValuesFile( tmp.name ) as vfile:
        vfile.selfTest()
        
        values = []
        
        value1 = Value( name = "target_url1", content = "http://aql.org/download" )
        value2 = Value( name = "target_url2", content = "http://aql.org/download2" )
        dep_value = DependsValue( name = "urls1", content = [ value1, value2 ] )
        
        values += [value1, value2, dep_value ]
        
        vfile.addValues( values ); vfile.selfTest()
        
        value1 = Value( name = "target_url3", content = "http://aql.org/download3" )
        value2 = Value( name = "target_url4", content = "http://aql.org/download4" )
        
        dep_value = DependsValue( name = "urls1", content = [ value1, value2 ] )
        vfile.addValues( [ value1, value2, dep_value ] ); vfile.selfTest()

  #//===========================================================================//

  def test_value_file_empty_deps(self):
    with Tempfile() as tmp:
      vfile = ValuesFile( tmp.name )
      try:
        vfile.selfTest()
        
        values = []
        
        dep_value = DependsValue( name = "urls1", content = [] )
        
        values += [dep_value ]
        
        vfile.addValues( values ); vfile.selfTest()
        
        vfile.close()
        vfile.open( tmp.name ); vfile.selfTest()
      finally:
        vfile.close()

  #//===========================================================================//

  @skip
  def   test_value_file_speed(self):
    values = []
    for i in range(0, 100000):
      value = Value( name = "target_url%s" % i, content = "http://aql.org/download" )
      values.append( value )
    
    with Tempfile() as tmp:
      with ValuesFile( tmp.name ) as vf:
        t = lambda addValues = vf.addValues, values = values: addValues( values )
        t = timeit.timeit( t, number = 1 )
        print("value picker: %s" % t)

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
