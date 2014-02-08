import sys
import time
import os.path

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempfile
from aql.values.aql_file_value import FileValue, FileContentTimeStamp

class TestFileValue( AqlTestCase ):
  def test_file_value(self):
    
    with Tempfile() as temp_file:
      test_string = '1234567890'
      
      temp_file.write( test_string.encode() )
      temp_file.flush()

      temp_file_value1 = FileValue( temp_file.name )
      temp_file_value2 = FileValue( temp_file.name )
      
      self.assertEqual( temp_file_value1, temp_file_value2 )
      
      reversed_test_string = str(reversed(test_string))
      temp_file.seek( 0 )
      temp_file.write( reversed_test_string.encode() )
      temp_file.flush()
      
      temp_file_value2 = FileValue( temp_file_value1 )
      self.assertEqual( temp_file_value1.name, temp_file_value2.name )
      self.assertNotEqual( temp_file_value1.content, temp_file_value2.content )

  #//=======================================================//

  def test_file_value_save_load(self):
    
    temp_file_name = None
    
    with Tempfile() as temp_file:
      test_string = '1234567890'
      
      temp_file.write( test_string.encode() )
      temp_file.flush()
      
      temp_file_name = temp_file.name
      
      temp_file_value = FileValue( temp_file_name )
    
    self._testSaveLoad( temp_file_value )
    
    file_value = FileValue( temp_file_name )
    self.assertEqual( temp_file_value.name, file_value.name )
    self.assertNotEqual( temp_file_value.content, file_value.content )
    self.assertFalse( file_value )

  #//=======================================================//

  def test_file_value_time(self):
    with Tempfile() as temp_file:
      test_string = '1234567890'
      
      temp_file.write( test_string.encode() )
      temp_file.flush()
      
      temp_file_value1 = FileValue( temp_file.name, FileContentTimeStamp )
      temp_file_value2 = FileValue( temp_file.name, FileContentTimeStamp )
      
      self.assertEqual( temp_file_value1, temp_file_value2 )
      
      time.sleep(2)
      temp_file.seek( 0 )
      temp_file.write( test_string.encode() )
      temp_file.close()
      
      temp_file_value2 = FileValue( temp_file_value1, FileContentTimeStamp )
      self.assertEqual( temp_file_value1.name, temp_file_value2.name )
      self.assertNotEqual( temp_file_value1.content, temp_file_value2.content )

  #//=======================================================//

  def test_file_value_time_save_load(self):
    
    temp_file_name = None
    
    with Tempfile() as temp_file:
      test_string = '1234567890'
      
      temp_file.write( test_string.encode() )
      temp_file.flush()
      
      temp_file_name = temp_file.name
      
      temp_file_value = FileValue( temp_file_name, FileContentTimeStamp )
      
    self._testSaveLoad( temp_file_value )
    
    file_value = FileValue( temp_file_name, FileContentTimeStamp )
    self.assertEqual( temp_file_value.name, file_value.name )
    self.assertNotEqual( temp_file_value.content, file_value.content )
    self.assertFalse( file_value )

  #//=======================================================//

  def test_file_empty_value_save_load(self):
    
    value1 = FileValue('__non_exist_file__')
    #~ print( id(value1.content) )
    #~ print( value1.content.signature )
    
    value2 = FileValue( value1, FileContentTimeStamp )
    
    self._testSaveLoad( value1 )
    self._testSaveLoad( value2 )

#//=======================================================//

if __name__ == "__main__":
  runLocalTests()

