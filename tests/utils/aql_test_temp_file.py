import os.path

from aql_tests import testcase
from aql_temp_file import Tempfile

#//===========================================================================//

@testcase
def test_temp_file(self):
  temp_file_name = None
  
  with Tempfile() as temp_file:
    
    temp_file.write( '1234567890\n1234567890'.encode() )
    temp_file.flush()
    
    temp_file_name = temp_file.name
  
  self.assertFalse( os.path.isfile(temp_file_name) )
  
#//===========================================================================//

@testcase
def test_temp_file_rw(self):
  temp_file_name = None
  
  with Tempfile() as temp_file:
    
    test_string = '1234567890'
    
    temp_file.write( test_string.encode() )
    temp_file.flush()
    
    temp_file_name = temp_file.name
    
    with open(temp_file_name, "r") as temp_file_rh:
      test_string_read = temp_file_rh.read()
      self.assertEqual( test_string,test_string_read )
    
  #//=======================================================//
