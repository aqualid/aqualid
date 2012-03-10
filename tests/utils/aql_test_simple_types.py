import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_simple_types import IgnoreCaseString, LowerCaseString, UpperCaseString, Version

#//===========================================================================//

@testcase
def test_istr(self):
  event_manager.setHandlers( EventHandler() )
  
  s1 = IgnoreCaseString('ABC')
  s2 = IgnoreCaseString('abc')
  
  self.assertEqual( s1, s2 )
  self.assertNotEqual( str(s1), str(s2) )
  
  a = {}
  a[s1] = 1
  a[s2] = 2
  
  self.assertEqual( len(a), 1 )
  
  b = set()
  b.add(s1)
  b.add(s2)
  
  self.assertEqual( len(b), 1 )
  
  self.assertIs( s1, IgnoreCaseString( s1 ) )

#//===========================================================================//

@testcase
def test_lowerstr(self):
  event_manager.setHandlers( EventHandler() )
  
  s1 = LowerCaseString('ABC')
  s2 = LowerCaseString('abc')
  
  self.assertEqual( s1, s2 )
  self.assertEqual( str(s1), str(s2) )
  
  a = {}
  a[s1] = 1
  a[s2] = 2
  
  self.assertEqual( len(a), 1 )
  
  b = set()
  b.add(s1)
  b.add(s2)
  
  self.assertEqual( len(b), 1 )
  
  self.assertIs( s1, LowerCaseString( s1 ) )

#//===========================================================================//

@testcase
def test_upperstr(self):
  event_manager.setHandlers( EventHandler() )
  
  s1 = UpperCaseString('ABC')
  s2 = UpperCaseString('abc')
  
  self.assertEqual( s1, s2 )
  self.assertEqual( str(s1), str(s2) )
  
  a = {}
  a[s1] = 1
  a[s2] = 2
  
  self.assertEqual( len(a), 1 )
  
  b = set()
  b.add(s1)
  b.add(s2)
  
  self.assertEqual( len(b), 1 )
  
  self.assertIs( s1, UpperCaseString( s1 ) )

#//===========================================================================//

@testcase
def test_version(self):
  event_manager.setHandlers( EventHandler() )
  
  v1 = Version('1.2.100')
  v2 = Version('1.2.99')
  
  self.assertLess( v2, v1 )
  
  a = {}
  a[v1] = 1
  a[v2] = 2
  
  v3 = Version('1.2.100')
  a[v3] = 3
  
  self.assertEqual( len(a), 2 )
  
  b = set()
  b.add(v1)
  b.add(v2)
  b.add(v3)
  
  self.assertEqual( len(b), 2 )
  
  self.assertIs( v1, Version( v1 ) )

#//===========================================================================//

if __name__ == "__main__":
  runTests()
