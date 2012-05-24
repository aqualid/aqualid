import sys
import os.path
import time

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_errors import *

#//-------------------------------------------------------//


class TestErrors( AqlTestCase ):
  def test_errors(self):
    def   _testError( error_type, *args ):
      try:
        raise error_type( *args )
        
      except error_type as err:
        pass
      
    _testError( UnknownNodeSourceType, 1, 2 )
    _testError( UnknownNodeDependencyType, 1, 2 )
    _testError( UnknownNode, 1 )
    _testError( UnknownAttribute, 1, 2 )
    _testError( NodeHasCyclicDependency, 1 )
    _testError( NodeAlreadyExists, 1 )
    _testError( RemovingNonTailNode, 1 )
    _testError( UnpickleableValue, 1 )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
