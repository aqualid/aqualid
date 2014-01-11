import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))
from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempfile, DataFile
from aql.values import Value, ValuesFile

#//===========================================================================//

class TestValuesFile( AqlTestCase ):
  def test_value_file(self):
    with Tempfile() as tmp:
      vfile = ValuesFile( tmp.name )
      try:
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
        
        vfile2 = ValuesFile( tmp.name )
        try:
          
          vfile2.selfTest()
          
          vfile2.addValues( values ); vfile2.selfTest()
          s_values2 = vfile2.findValues( values ); vfile.selfTest()
          self.assertEqual( values, s_values2 )
          
          #//-------------------------------------------------------//
          
          value1 = Value( name = value1.name, content = "http://aql.org/download1" )
          
          vfile2.addValues( [ value1 ] ); vfile2.selfTest()
          s_value1 = vfile.findValues( [ value1 ] )[0]; vfile.selfTest()
          
          self.assertEqual( value1, s_value1 )
          
          #//-------------------------------------------------------//
          
          df = DataFile( tmp.name )
          try:
            value1_key, value1 = vfile.xash.find( value1 )
            del df[value1_key]
            
            s_value1 = vfile.findValues( [value1] )[0]; vfile.selfTest()
            self.assertNotEqual( s_value1.content, value1.content )
            
            s_value1 = vfile2.findValues( [value1] )[0]; vfile.selfTest()
            self.assertNotEqual( s_value1.content, value1.content )
          finally:
            df.close()
        finally:
          vfile2.close()
      finally:
        vfile.close()

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
        
        all_values = values
        
        vfile.addValues( all_values ); vfile.selfTest()
        self.assertEqual( vfile.findValues( all_values ), all_values )
        
        vfile.close()
        vfile.open( tmp.name ); vfile.selfTest()
        
        s_all_values = vfile.findValues( all_values ); vfile.selfTest()
        for value, s_value in zip( all_values, s_all_values ):
          self.assertEqual( value, s_value )
        
        value3 = Value( name = "target_url3", content = "http://aql.org/download3/0" )
        
        vfile.addValues( [value3] ); vfile.selfTest()
        
      finally:
        vfile.close()
    
  #//===========================================================================//

  def test_value_file_3(self):
    with Tempfile() as tmp:
      vfile = ValuesFile( tmp.name )
      try:
        vfile.selfTest()
        
        values = []
        
        value1 = Value( name = "target_url1", content = "http://aql.org/download" )
        value2 = Value( name = "target_url2", content = "http://aql.org/download2" )
        
        values += [value1, value2 ]
        
        vfile.addValues( values ); vfile.selfTest()
        
        value1 = Value( name = "target_url3", content = "http://aql.org/download3" )
        value2 = Value( name = "target_url4", content = "http://aql.org/download4" )
        
        vfile.addValues( [ value1, value2 ] ); vfile.selfTest()
      
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
      vf = ValuesFile( tmp.name )
      try:
        t = lambda addValues = vf.addValues, values = values: addValues( values )
        t = timeit.timeit( t, number = 1 )
        print("value picker: %s" % t)
      finally:
        vf.close()

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
