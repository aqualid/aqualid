import sys
import os.path

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.values import Value, IStringContent

#//===========================================================================//

class TestStrValue( AqlTestCase ):
  def test_str_value(self):
    
    value1 = Value('results_link', 'http://buildsrv.com/results.out')
    value2 = Value('results_link', 'http://buildsrv.com/results.out')
    
    self.assertEqual( value1, value1 )
    self.assertEqual( value1, value2 )
    
    value2 = Value( value1 )
    self.assertEqual( value1, value2 )
    
    value2.content = value2.content.data.upper()
    self.assertNotEqual( value1.content, value2.content )
    
    value2.content = IStringContent( value2.content )
    self.assertNotEqual( value1.content, value2.content )
    
    value1.content = IStringContent( value1.content )
    self.assertEqual( value1.content, value2.content )

  #//===========================================================================//

  def test_str_value_save_load(self):
    
    value1 = Value('results_link', 'http://buildsrv.com/results.out')
    value2 = Value('results_link', IStringContent(value1.content))
    
    self._testSaveLoad( value1 )
    self._testSaveLoad( value2 )

  #//===========================================================================//

  def test_str_empty_value_save_load(self):
    
    value1 = Value('results_link')
    value2 = Value( value1 )
    
    self._testSaveLoad( value1 )
    self._testSaveLoad( value2 )

#//=======================================================//

if __name__ == "__main__":
  runLocalTests()
