import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_temp_file import Tempfile
from aql_value import Value, NoContent
from aql_str_value import StringValue
from aql_depends_value import DependsValue
from aql_value_pickler import ValuePickler, pickleable
from aql_values_file import ValuesFile


#//===========================================================================//

@testcase
def test_deps_1(self):
  
    with Tempfile() as tmp:
      pass
    vfile = ValuesFile( tmp.name )
    vfile.selfTest()
    
    value1 = StringValue( "target_url1", "http://aql.org/download" )
    value2 = StringValue( "target_url2", "http://aql.org/download2" )
    value3 = StringValue( "target_url3", "http://aql.org/download3" )
    
    values = [ value1, value2, value3 ]
    
    vfile.addValues( values ); vfile.selfTest()
    
    s_values = vfile.findValues( values ); vfile.selfTest()
    
    self.assertEqual( values, s_values )
    
    vfile.clear(); vfile.selfTest()
    #//-------------------------------------------------------//
    
    dep_value = DependsValue( "urls", values )
    values.insert( 0, dep_value )
    
    vfile.addValues( values ); vfile.selfTest()
    s_values = vfile.findValues( values ); vfile.selfTest()
    
    self.assertEqual( values, s_values )
    
    #//-------------------------------------------------------//
    
    vfile2 = ValuesFile( tmp.name ); vfile2.selfTest()
    s_values2 = vfile2.findValues( values ); vfile.selfTest()
    self.assertEqual( values, s_values2 )
    
    #//-------------------------------------------------------//
    
    values[0] = DependsValue( "urls", reversed(values[1:]) )
    
    vfile2.addValues( values ); vfile2.selfTest()
    s_values = vfile.findValues( values ); vfile.selfTest()
    self.assertEqual( values, s_values )
    
    #//-------------------------------------------------------//
    
    value1.content = "http://aql.org/download1"
    
    vfile2.addValues( [ value1 ] ); vfile2.selfTest()
    s_value1 = vfile.findValues( [ value1 ] )[0]; vfile.selfTest()
    self.assertEqual( value1, s_value1 )
    
    #//-------------------------------------------------------//
    
    dep_value = DependsValue( "urls", reversed(values) )
    
    vfile2.addValues( [dep_value] ); vfile2.selfTest()
    s_dep_value = vfile.findValues( [dep_value] )[0]; vfile.selfTest()
    self.assertEqual( dep_value, s_dep_value )

#//===========================================================================//

if __name__ == "__main__":
  runTests()
