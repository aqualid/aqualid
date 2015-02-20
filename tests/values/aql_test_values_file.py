import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))
from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempfile, Chrono
from aql.entity import SimpleEntity, SignatureEntity, EntitiesFile

#//===========================================================================//

class TestValuesFile( AqlTestCase ):
  
  def test_values_file(self):
    with Tempfile() as tmp:
      with EntitiesFile( tmp ) as vfile:
        vfile.selfTest()
        
        value1 = SimpleEntity( "http://aql.org/download" )
        value2 = SimpleEntity( "http://aql.org/download2" )
        value3 = SimpleEntity( "http://aql.org/download3" )
        
        values = [ value1, value2, value3 ]
        
        vfile.addEntities( values ); vfile.selfTest()
        
        s_values = vfile.findEntities( values ); vfile.selfTest()
        
        self.assertSequenceEqual( values, s_values )
        
        vfile.clear(); vfile.selfTest()
        
        #//-------------------------------------------------------//
        
        value_keys = vfile.addEntities( values ); vfile.selfTest()
        s_values = vfile.findEntities( values ); vfile.selfTest()
        dep_values = vfile.getEntitiesByKeys( value_keys ); vfile.selfTest()
        
        self.assertSequenceEqual( s_values, dep_values )
        
        #//-------------------------------------------------------//
        
        value1_key = vfile.addEntity( value1, cache = False ); vfile.selfTest()
        vfile.dropEntityCache( value1 )
        
        s_dep_value = vfile.getEntityByKey( value1_key ); vfile.selfTest()
        self.assertEqual( value1, s_dep_value )
        
        value1 = SimpleEntity( "abc", name = value1.name )
        
        vfile.addEntity( value1 ); vfile.selfTest()
        
        s_dep_value = vfile.getEntitiesByKeys( value_keys ); vfile.selfTest()
        self.assertIsNone( s_dep_value[0] )

  #//===========================================================================//

  def test_values_file_2(self):
    with Tempfile() as tmp:
      vfile = EntitiesFile( tmp )
      try:
        vfile.selfTest()
        
        self.assertSequenceEqual( vfile.findEntities( [] ), [] )
        
        value1 = SimpleEntity( "http://aql.org/download",  name = "target_url1" )
        value2 = SimpleEntity( "http://aql.org/download2", name = "target_url2" )
        value3 = SimpleEntity( "http://aql.org/download3", name = "target_url3" )
        value4 = SimpleEntity( "http://aql.org/download4", name = "target_url4" )
        value5 = SimpleEntity( "http://aql.org/download5", name = "target_url5" )
        value6 = SimpleEntity( "http://aql.org/download6", name = "target_url6" )
        
        values = [ value1, value2, value3 ]
        
        dep_values_1 = values
        dep_values_2 = dep_values_1 + [ value4 ]
        dep_values_3 = dep_values_2 + [ value5 ]
        dep_values_4 = dep_values_3 + [ value6 ]
        
        all_values = dep_values_4
        
        all_keys = vfile.addEntities( all_values ); vfile.selfTest()
        self.assertSequenceEqual( vfile.findEntities( all_values ), all_values )
        
        dep_keys_1 = vfile.addEntities( dep_values_1 ); vfile.selfTest()
        dep_keys_2 = vfile.addEntities( dep_values_2 ); vfile.selfTest()
        dep_keys_3 = vfile.addEntities( dep_values_3 ); vfile.selfTest()
        dep_keys_4 = vfile.addEntities( dep_values_4 ); vfile.selfTest()
        
        self.assertSequenceEqual( dep_keys_1, dep_keys_2[:-1] )
        self.assertSequenceEqual( dep_keys_2, dep_keys_3[:-1] )
        self.assertSequenceEqual( dep_keys_3, dep_keys_4[:-1] )
        
        self.assertSequenceEqual( all_keys, dep_keys_4 )
        
        vfile.close()
        vfile.open( tmp ); vfile.selfTest()
        
        self.assertSequenceEqual( vfile.findEntities( all_values ), all_values )
        vfile.selfTest()
        
        self.assertSequenceEqual( vfile.getEntitiesByKeys( dep_keys_1 ), dep_values_1 )
        self.assertSequenceEqual( vfile.getEntitiesByKeys( dep_keys_2 ), dep_values_2 )
        self.assertSequenceEqual( vfile.getEntitiesByKeys( dep_keys_3 ), dep_values_3 )
        self.assertSequenceEqual( vfile.getEntitiesByKeys( dep_keys_4 ), dep_values_4 )
        
        value4 = SimpleEntity( "http://aql.org/download3/0", name = value4.name )
        
        vfile.addEntity( value4, cache = False ); vfile.selfTest()
        
        self.assertSequenceEqual( vfile.getEntitiesByKeys( dep_keys_1 ), dep_values_1 )
        self.assertIsNone( vfile.getEntityByKey( dep_keys_2[-1] ) )
        self.assertIsNone( vfile.getEntitiesByKeys( dep_keys_3 )[ len(dep_keys_2) - 1] )
        self.assertIsNone( vfile.getEntitiesByKeys( dep_keys_4 )[ len(dep_keys_2) - 1] )
        
      finally:
        vfile.close()
    

  #//===========================================================================//

  def test_values_file_same_name(self):
    with Tempfile() as tmp:
      vfile = EntitiesFile( tmp )
      try:
        vfile.selfTest()
        
        values = []
        
        value1 = SimpleEntity( "test", name = "test1" )
        value2 = SignatureEntity( b"1234354545", name = value1.name )
        
        vfile.addEntities( [ value1, value2 ] ); vfile.selfTest()
        
        values = [ SimpleEntity( name = value1.name ), SignatureEntity( name = value2.name ) ]
        values = vfile.findEntities( values )
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
      value = SimpleEntity( "http://aql.org/download", name = "target_url%s" % i )
      values.append( value )
    
    with Tempfile() as tmp:
      timer = Chrono()
      with timer:
        with EntitiesFile( tmp ) as vf:
          vf.addEntities( values )
      print("save values time: %s" % timer )
      
      with timer:
        with EntitiesFile( tmp ) as vf:
          pass
      print("read values time: %s" % timer )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
