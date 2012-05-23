import sys
import os.path
import io
import pickle
import unittest

_search_paths = [ '.', 'tests_utils', 'utils', 'events', 'values', 'nodes', 'options' ]
sys.path[0:0] = map( lambda p: os.path.normpath( os.path.join( os.path.dirname( __file__ ), '..', p) ), _search_paths )

from tests_utils import TestCaseBase, skip, runTests, runLocalTests
from aql_value import NoContent

#//===========================================================================//

class AqlTestCase( TestCaseBase ):
  
  @skip
  def testSaveLoad( self, value ):
    data = pickle.dumps( ( value, ), protocol = pickle.HIGHEST_PROTOCOL )
    
    loaded_values = pickle.loads( data )
    loaded_value = loaded_values[0]
    
    self.assertEqual( value.name, loaded_value.name )
    if type(value.content) is not NoContent:
      self.assertEqual( value.content, loaded_value.content )
    else:
      self.assertEqual( type(value.content), type(loaded_value.content) )

#//===========================================================================//

if __name__ == '__main__':
  runTests()
