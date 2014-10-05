import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))
from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempfile, Chrono
from aql.values import SimpleValue, SignatureValue, ValuesFile

#//===========================================================================//

class TestValuesFile( AqlTestCase ):
  
  def test_values_file(self):
    with Tempfile() as tmp:
      with ValuesFile( tmp ) as vfile:
        vfile.selfTest()
        
        value1 = SimpleValue( "http://aql.org/download" )
        value2 = SimpleValue( "http://aql.org/download2" )
        value3 = SimpleValue( "http://aql.org/download3" )
        
        values = [ value1, value2, value3 ]
        
        vfile.addValues( values ); vfile.selfTest()
        
        s_values = vfile.findValues( values ); vfile.selfTest()
        
        self.assertSequenceEqual( values, s_values )
        
        vfile.clear(); vfile.selfTest()
        
        #//-------------------------------------------------------//
        
        value_keys = vfile.addValues( values ); vfile.selfTest()
        s_values = vfile.findValues( values ); vfile.selfTest()
        dep_values = vfile.getValuesByKeys( value_keys ); vfile.selfTest()
        
        self.assertSequenceEqual( s_values, dep_values )
        
        #//-------------------------------------------------------//
        
        value1_key = vfile.addValue( value1 ); vfile.selfTest()
        
        s_dep_value = vfile.getValueByKey( value1_key ); vfile.selfTest()
        self.assertEqual( value1, s_dep_value )
        
        value1 = SimpleValue( "abc", name = value1.name )
        
        vfile.addValue( value1 ); vfile.selfTest()
        
        s_dep_value = vfile.getValuesByKeys( value_keys ); vfile.selfTest()
        self.assertIsNone( s_dep_value[0] )

  #//===========================================================================//

  def test_values_file_2(self):
    with Tempfile() as tmp:
      vfile = ValuesFile( tmp )
      try:
        vfile.selfTest()
        
        self.assertSequenceEqual( vfile.findValues( [] ), [] )
        
        value1 = SimpleValue( "http://aql.org/download",  name = "target_url1" )
        value2 = SimpleValue( "http://aql.org/download2", name = "target_url2" )
        value3 = SimpleValue( "http://aql.org/download3", name = "target_url3" )
        value4 = SimpleValue( "http://aql.org/download4", name = "target_url4" )
        value5 = SimpleValue( "http://aql.org/download5", name = "target_url5" )
        value6 = SimpleValue( "http://aql.org/download6", name = "target_url6" )
        
        values = [ value1, value2, value3 ]
        
        dep_values_1 = values
        dep_values_2 = dep_values_1 + [ value4 ]
        dep_values_3 = dep_values_2 + [ value5 ]
        dep_values_4 = dep_values_3 + [ value6 ]
        
        all_values = dep_values_4
        
        all_keys = vfile.addValues( all_values ); vfile.selfTest()
        self.assertSequenceEqual( vfile.findValues( all_values ), all_values )
        
        dep_keys_1 = vfile.addValues( dep_values_1 ); vfile.selfTest()
        dep_keys_2 = vfile.addValues( dep_values_2 ); vfile.selfTest()
        dep_keys_3 = vfile.addValues( dep_values_3 ); vfile.selfTest()
        dep_keys_4 = vfile.addValues( dep_values_4 ); vfile.selfTest()
        
        self.assertSequenceEqual( dep_keys_1, dep_keys_2[:-1] )
        self.assertSequenceEqual( dep_keys_2, dep_keys_3[:-1] )
        self.assertSequenceEqual( dep_keys_3, dep_keys_4[:-1] )
        
        self.assertSequenceEqual( all_keys, dep_keys_4 )
        
        vfile.close()
        vfile.open( tmp ); vfile.selfTest()
        
        self.assertSequenceEqual( vfile.findValues( all_values ), all_values )
        vfile.selfTest()
        
        self.assertSequenceEqual( vfile.getValuesByKeys( dep_keys_1 ), dep_values_1 )
        self.assertSequenceEqual( vfile.getValuesByKeys( dep_keys_2 ), dep_values_2 )
        self.assertSequenceEqual( vfile.getValuesByKeys( dep_keys_3 ), dep_values_3 )
        self.assertSequenceEqual( vfile.getValuesByKeys( dep_keys_4 ), dep_values_4 )
        
        value4 = SimpleValue( "http://aql.org/download3/0", name = value4.name )
        
        vfile.addValue( value4 ); vfile.selfTest()
        
        self.assertSequenceEqual( vfile.getValuesByKeys( dep_keys_1 ), dep_values_1 )
        self.assertIsNone( vfile.getValueByKey( dep_keys_2[-1] ) )
        self.assertIsNone( vfile.getValuesByKeys( dep_keys_3 )[ len(dep_keys_2) - 1] )
        self.assertIsNone( vfile.getValuesByKeys( dep_keys_4 )[ len(dep_keys_2) - 1] )
        
      finally:
        vfile.close()
    

  #//===========================================================================//

  def test_values_file_same_name(self):
    with Tempfile() as tmp:
      vfile = ValuesFile( tmp )
      try:
        vfile.selfTest()
        
        values = []
        
        value1 = SimpleValue( "test", name = "test1" )
        value2 = SignatureValue( b"1234354545", name = value1.name )
        
        vfile.addValues( [ value1, value2 ] ); vfile.selfTest()
        
        values = [ SimpleValue( name = value1.name ), SignatureValue( name = value2.name ) ]
        values = vfile.findValues( values )
        self.assertEqual( value1, values[0] )
        self.assertEqual( value2, values[1] )
        
        vfile.close()
        vfile.open( tmp ); vfile.selfTest()
      finally:
        vfile.close()

  #//===========================================================================//

  @skip
  def   test_value_file_speed(self):
    values = []
    for i in range(0, 100000):
      value = SimpleValue( "http://aql.org/download", name = "target_url%s" % i )
      values.append( value )
    
    with Tempfile() as tmp:
      timer = Chrono()
      with timer:
        with ValuesFile( tmp ) as vf:
          vf.addValues( values )
      print("save values time: %s" % timer )
      
      with timer:
        with ValuesFile( tmp ) as vf:
          pass
      print("read values time: %s" % timer )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
