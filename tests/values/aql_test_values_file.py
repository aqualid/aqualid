import sys
import os.path
import operator
import sqlite3

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))
from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempfile, Chrono
from aql.entity import SimpleEntity, SignatureEntity, EntitiesFile, EntityPickler, EntityBase

#//===========================================================================//

class TestValuesFile( AqlTestCase ):
  
  def test_values_file(self):
    with Tempfile() as tmp:
      vfile = EntitiesFile( tmp )
      
      try:
        vfile.selfTest()
        
        value1 = SimpleEntity( "http://aql.org/download" )
        value2 = SimpleEntity( "http://aql.org/download2" )
        value3 = SimpleEntity( "http://aql.org/download3" )
        
        values = [ value1, value2, value3 ]
        
        value_keys = vfile.addEntities( values ); vfile.selfTest()
        other_value_keys = vfile.addEntities( values ); vfile.selfTest()
        
        self.assertItemsEqual( value_keys, other_value_keys )
        
        values = sorted(values, key = operator.attrgetter('id'))
        
        s_values = vfile.findEntities( values )
        s_values = sorted(s_values, key = operator.attrgetter('id'))
        
        self.assertItemsEqual( values, s_values )
        
        vfile.clear(); vfile.selfTest()
        
        #//-------------------------------------------------------//
        
        value_keys = vfile.addEntities( values ); vfile.selfTest()
        
        s_values = vfile.findEntities( values ); vfile.selfTest()
        dep_values = vfile.findEntitiesByKey( value_keys ); vfile.selfTest()
        
        self.assertItemsEqual( s_values, dep_values )
        
        #//-------------------------------------------------------//
        
        value1_key = vfile.addEntities( [value1] )[0]; vfile.selfTest()
        
        s_dep_value = vfile.findEntitiesByKey( [value1_key] )[0]
        self.assertEqual( value1, s_dep_value )
        
        value1 = SimpleEntity( "abc", name = value1.name )
        
        vfile.addEntities( [value1] ); vfile.selfTest()
        
        s_dep_value = vfile.findEntitiesByKey( value_keys ); vfile.selfTest()
        self.assertIsNone( s_dep_value )
      finally:
        vfile.close()

  #//===========================================================================//

  def test_values_file_2(self):
    with Tempfile() as tmp:
      vfile = EntitiesFile( tmp )
      try:
        vfile.selfTest()
        
        self.assertItemsEqual( vfile.findEntities( [] ), [] )
        
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
        self.assertItemsEqual( vfile.findEntities( all_values ), all_values )
        self.assertItemsEqual( vfile.findEntitiesByKey( all_keys ), all_values )
        
        dep_keys_1 = vfile.addEntities( dep_values_1 ); vfile.selfTest()
        dep_keys_2 = vfile.addEntities( dep_values_2 ); vfile.selfTest()
        dep_keys_3 = vfile.addEntities( dep_values_3 ); vfile.selfTest()
        dep_keys_4 = vfile.addEntities( dep_values_4 ); vfile.selfTest()
        
        self.assertTrue( set(dep_keys_1).issubset( dep_keys_2 ) )
        self.assertTrue( set(dep_keys_2).issubset( dep_keys_3 ) )
        self.assertTrue( set(dep_keys_3).issubset( dep_keys_4 ) )
        
        self.assertItemsEqual( all_keys, dep_keys_4 )
        
        vfile.close()
        vfile.open( tmp ); vfile.selfTest()
        
        self.assertItemsEqual( vfile.findEntities( all_values ), all_values )
        vfile.selfTest()
        
        self.assertItemsEqual( vfile.findEntitiesByKey( dep_keys_1 ), dep_values_1 )
        self.assertItemsEqual( vfile.findEntitiesByKey( dep_keys_2 ), dep_values_2 )
        self.assertItemsEqual( vfile.findEntitiesByKey( dep_keys_3 ), dep_values_3 )
        self.assertItemsEqual( vfile.findEntitiesByKey( dep_keys_4 ), dep_values_4 )
        
        value4 = SimpleEntity( "http://aql.org/download3/0", name = value4.name )
        
        vfile.addEntities( [value4] ); vfile.selfTest()
        
        self.assertItemsEqual( vfile.findEntitiesByKey( dep_keys_1 ), dep_values_1 )
        self.assertIsNone( vfile.findEntitiesByKey( dep_keys_2 ) )
        self.assertIsNone( vfile.findEntitiesByKey( dep_keys_3 ) )
        self.assertIsNone( vfile.findEntitiesByKey( dep_keys_4 ) )
        
      finally:
        vfile.close()
    

  #//===========================================================================//

  def test_values_file_same_name(self):
    with Tempfile() as tmp:
      vfile = EntitiesFile( tmp )
      try:
        vfile.selfTest()
        
        value1 = SimpleEntity( "test", name = "test1" )
        value2 = SignatureEntity( b"1234354545", name = value1.name )
        
        vfile.addEntities( [ value1, value2 ] ); vfile.selfTest()
        
        values = [ SimpleEntity( name = value1.name ), SignatureEntity( name = value2.name ) ]
        values = vfile.findEntities( values )
        self.assertItemsEqual( values, [ value1, value2 ] )
        
        vfile.close()
        vfile.open( tmp ); vfile.selfTest()
      finally:
        vfile.close()

  #//===========================================================================//

  def   _test_values_file_speed(self, use_sqlite ):
    values = []
    for i in range(20000):
      value = SimpleEntity( "http://aql.org/download", name = "target_url%s" % i )
      values.append( value )
    
    with Tempfile() as tmp:
      print("Opening a database '%s' ..." % tmp )
      timer = Chrono()
      with EntitiesFile( tmp, use_sqlite = use_sqlite ) as vf:
        with timer:
          keys = vf.addEntities( values )
      print("add values time: %s" % (timer,) )
      
      with EntitiesFile( tmp, use_sqlite = use_sqlite ) as vf:
        with timer:
          keys = vf.addEntities( values )
      print("re-add values time: %s" % (timer,) )
      
      with EntitiesFile( tmp, use_sqlite = use_sqlite ) as vf:
        with timer:
          vf.findEntitiesByKey( keys )
      print("get values time: %s" % timer )
      
      with timer:
        with EntitiesFile( tmp, use_sqlite = use_sqlite ) as vf:
          pass
      print("reopen values file time: %s" % timer )
  
  #//===========================================================================//

  @skip
  def   test_values_file_speed(self):
    self._test_values_file_speed( use_sqlite = False )
  
  #//===========================================================================//

  @skip
  def   test_values_file_speed_sql(self):
    self._test_values_file_speed( use_sqlite = True )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
