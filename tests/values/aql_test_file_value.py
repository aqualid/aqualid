import sys
import time
import os.path

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_temp_file import Tempfile
from aql_file_value import FileValue, FileName, FileContentChecksum, FileContentTimeStamp

@testcase
def test_file_value(self):
  
  with Tempfile() as temp_file:
    test_string = '1234567890'
    
    temp_file.write( test_string.encode() )
    temp_file.flush()

    temp_file_value1 = FileValue( temp_file.name )
    temp_file_value2 = FileValue( temp_file.name )
    
    self.assertEqual( temp_file_value1, temp_file_value2 )
    self.assertEqual( temp_file_value1.content, temp_file_value2.content )
    
    reversed_test_string = str(reversed(test_string))
    temp_file.seek( 0 )
    temp_file.write( reversed_test_string.encode() )
    temp_file.flush()
    
    temp_file_value2 = FileValue( temp_file_value1 )
    self.assertEqual( temp_file_value1, temp_file_value2 )
    self.assertNotEqual( temp_file_value1.content, temp_file_value2.content )

  #//=======================================================//

@testcase
def test_file_value_save_load(self):
  
  temp_file_name = None
  
  with Tempfile() as temp_file:
    test_string = '1234567890'
    
    temp_file.write( test_string.encode() )
    temp_file.flush()
    
    temp_file_name = temp_file.name
    
    temp_file_value = FileValue( temp_file_name )
  
  self.testSaveLoad( temp_file_value )
  
  file_value = FileValue( temp_file_name )
  self.assertEqual( temp_file_value, file_value )
  self.assertNotEqual( temp_file_value.content, file_value.content )
  self.assertFalse( file_value.exists() )

#//=======================================================//

@testcase
def test_file_value_time(self):
  with Tempfile() as temp_file:
    test_string = '1234567890'
    
    temp_file.write( test_string.encode() )
    temp_file.flush()

    temp_file_value1 = FileValue( temp_file.name, FileContentTimeStamp )
    temp_file_value2 = FileValue( temp_file.name, FileContentTimeStamp )
    
    self.assertEqual( temp_file_value1, temp_file_value2 )
    self.assertEqual( temp_file_value1.content, temp_file_value2.content )
    
    time.sleep(1)
    temp_file.seek( 0 )
    temp_file.write( test_string.encode() )
    temp_file.flush()
    
    temp_file_value2 = FileValue( temp_file_value1, FileContentTimeStamp )
    self.assertEqual( temp_file_value1, temp_file_value2 )
    self.assertNotEqual( temp_file_value1.content, temp_file_value2.content )

#//=======================================================//

@testcase
def test_file_value_time_save_load(self):
  
  temp_file_name = None
  
  with Tempfile() as temp_file:
    test_string = '1234567890'
    
    temp_file.write( test_string.encode() )
    temp_file.flush()
    
    temp_file_name = temp_file.name
    
    temp_file_value = FileValue( temp_file_name, FileContentTimeStamp )
    
  self.testSaveLoad( temp_file_value )
  
  file_value = FileValue( temp_file_name, FileContentTimeStamp )
  self.assertEqual( temp_file_value, file_value )
  self.assertNotEqual( temp_file_value.content, file_value.content )
  self.assertFalse( file_value.exists() )

#//=======================================================//

@testcase
def test_file_empty_value_save_load(self):
  
  value1 = FileValue('__non_exist_file__')
  value2 = FileValue( value1, FileContentTimeStamp )
  
  self.testSaveLoad( value1 )
  self.testSaveLoad( value2 )

#//=======================================================//

if __name__ == "__main__":
  runTests()

