import sys
import os.path

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.values import SimpleValue, SignatureValue, NullValue

#//===========================================================================//

class TestValues( AqlTestCase ):
  def test_str_value(self):
    
    value1 = SimpleValue( 'http://buildsrv.com/results.out' )
    value2 = SimpleValue( 'http://buildsrv.com/results.out' )
    
    self._testSaveLoad( value1 )
    
    self.assertEqual( value1, value1 )
    self.assertEqual( value1, value2 )
    
    self.assertTrue( value1.isActual() )
    
    value2 = value1.copy()
    self.assertEqual( value1, value2 )
    
    self._testSaveLoad( value2 )
    
    value2 = SimpleValue( 'http://buildsrv.com/results2.out')
    self.assertNotEqual( value1, value2 )
    

  #//===========================================================================//

  def test_str_empty_value_save_load(self):
    
    value1 = SimpleValue( name = 'results_link' )
    value2 = value1.copy()
    self.assertEqual( value1, value2 )
    
    self.assertFalse( value1.isActual() )
    self.assertFalse( value2.isActual() )
    
    self._testSaveLoad( value1 )
    self._testSaveLoad( value2 )

  #//=======================================================//
  
  def test_sign_value(self):
    
    value1 = SignatureValue( b'http://buildsrv.com/results.out' )
    value2 = SignatureValue( b'http://buildsrv.com/results.out' )
    
    self._testSaveLoad( value1 )
    
    self.assertEqual( value1, value1 )
    self.assertEqual( value1, value2 )
    self.assertTrue( value1.isActual() )
    
    value2 = value1.copy()
    self.assertEqual( value1, value2 )
    
    self._testSaveLoad( value2 )
    
    value2 = SignatureValue( b'http://buildsrv.com/results2.out')
    self.assertNotEqual( value1, value2 )
    

  #//===========================================================================//
  
  def test_sign_empty_value_save_load(self):
    
    value1 = SignatureValue( name = 'results_link' )
    value2 = value1.copy()
    self.assertEqual( value1, value2 )
    
    self.assertFalse( value1.isActual() )
    self.assertFalse( value2.isActual() )
    
    self._testSaveLoad( value1 )
    self._testSaveLoad( value2 )
  
  #//===========================================================================//
  
  def test_null_value(self):
    
    value1 = NullValue()
    value2 = NullValue()
    self.assertEqual( value1, value2 )
    
    self.assertFalse( value1.isActual() )
    
    self._testSaveLoad( value1 )

#//=======================================================//

if __name__ == "__main__":
  runLocalTests()
