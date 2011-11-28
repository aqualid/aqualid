import io
import sys
import pickle
import os.path

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_str_value import StringValue, StringContent, StringContentIgnoreCase

#//===========================================================================//

@testcase
def test_str_value(self):
  
  value1 = StringValue('results_link', 'http://buildsrv.com/results.out')
  value2 = StringValue('results_link', 'http://buildsrv.com/results.out')
  
  self.assertEqual( value1, value1 )
  self.assertEqual( value1, value2 )
  
  value2 = StringValue( value1 )
  self.assertEqual( value1, value2 )
  
  value2.content = StringContent( value2.content.upper() )
  self.assertNotEqual( value1.content, value2.content )
  
  value2.content = StringContentIgnoreCase( value2.content )
  self.assertNotEqual( value1.content, value2.content )
  
  value1.content = StringContentIgnoreCase( value1.content )
  self.assertEqual( value1.content, value2.content )

#//===========================================================================//

@testcase
def test_str_value_save_load(self):
  
  value1 = StringValue('results_link', 'http://buildsrv.com/results.out')
  value2 = StringValue('results_link', StringContentIgnoreCase(value1.content))
  
  self.testSaveLoad( value1 )
  self.testSaveLoad( value2 )

#//===========================================================================//

@testcase
def test_str_empty_value_save_load(self):
  
  value1 = StringValue('results_link')
  value2 = StringValue( value1 )
  
  self.testSaveLoad( value1 )
  self.testSaveLoad( value2 )

#//=======================================================//

if __name__ == "__main__":
  runTests()
