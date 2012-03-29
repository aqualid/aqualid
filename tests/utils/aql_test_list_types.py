import sys
import os.path
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_list_types import UniqueList, SplitListType, List, ValueListType

#//===========================================================================//

@testcase
def test_unique_list(self):
  
  ul = UniqueList( [1,2,3,2,1,3] ); ul.selfTest()
  
  self.assertEqual( ul, [2,3,1])
  self.assertEqual( list(ul), [1,2,3])
  
  ul = UniqueList()
  
  ul.append( 1 ); ul.selfTest()
  ul.append( 3 ); ul.selfTest()
  ul.append( 1 ); ul.selfTest()
  ul.append( 2 ); ul.selfTest()
  ul.append( 3 ); ul.selfTest()
  ul.append( 1 ); ul.selfTest()
  
  self.assertEqual( list(ul), [1,3,2])
  
  ul.append_front( 2 ); ul.selfTest()
  self.assertEqual( list(ul), [2,1,3])
  
  ul.extend( [4,1,2,2,5] ); ul.selfTest()
  self.assertEqual( list(ul), [2,1,3,4,5])
  
  ul.extend_front( [1,2,2,3,1,1,5,5] ); ul.selfTest()
  self.assertEqual( list(ul), [1,2,3,5,4])
  
  self.assertEqual( list(ul), [1,2,3,5,4])
  
  ul.remove( 1 ); ul.selfTest()
  self.assertEqual( list(ul), [2,3,5,4])
  
  ul.remove( 5 ); ul.selfTest()
  self.assertEqual( list(ul), [2,3,4])
  
  ul.remove( 55 ); ul.selfTest()
  self.assertEqual( list(ul), [2,3,4])
  
  self.assertEqual( ul.pop(), 4 ); ul.selfTest()
  self.assertEqual( ul.pop_front(), 2 ); ul.selfTest()
  
  self.assertEqual( ul.pop_front(), 3 ); ul.selfTest()
  
  ul += [1,2,2,2,3,1,2,4,3,3,5,4,5,5]; ul.selfTest()
  self.assertEqual( list(ul), [1,2,3,4,5])
  
  ul -= [2,2,2,4,33]; ul.selfTest()
  self.assertEqual( list(ul), [1,3,5])
  
  self.assertEqual( ul[0], 1)
  self.assertEqual( ul[2], 5)
  self.assertEqual( ul[1], 3)
  
  self.assertIn( 1, ul)
  
  self.assertEqual( list(reversed(ul)), [5,3,1])
  
  ul.reverse(); ul.selfTest()
  self.assertEqual( ul, [5,3,1] )
  
  ul.reverse(); ul.selfTest()
  self.assertEqual( str(ul), "[1, 3, 5]" )
  
  
  self.assertEqual( ul, UniqueList([1, 3, 5]) )
  self.assertEqual( ul, UniqueList(ul) )
  self.assertLess( UniqueList([1,2,2,2,3]), UniqueList([1,2,1,1,1,4]) )
  self.assertLess( UniqueList([1,2,2,2,3]), [1,2,1,1,1,4] )

#//===========================================================================//

@testcase
def test_splitlist(self):
  
  l = SplitListType( List, ", \t\n\r" )("1,2, 3,,, \n\r\t4")
  self.assertEqual( l, ['1','2','3','4'] )
  self.assertEqual( l, "1,2,3,4" )
  self.assertEqual( l, "1 2 3 4" )
  self.assertEqual( str(l), "1,2,3,4" )
  
  l += "7, 8"
  self.assertEqual( l, ['1','2','3','4','7','8'] )
  
  l -= "2, 3"
  self.assertEqual( l, ['1','4','7','8'] )
  
  l -= "5"
  self.assertEqual( l, ['1','4','7','8'] )
  
  l.extend_front( "10,12" )
  self.assertEqual( l, ['10','12','1','4','7','8'] )
  
  l.extend( "0,-1" )
  self.assertEqual( l, ['10','12','1','4','7','8', '0', '-1'] )

#//===========================================================================//

@testcase
def test_valuelist(self):
  
  l = SplitListType( ValueListType( List, int ), ", \t\n\r" )("1,2, 3,,, \n\r\t4")
  self.assertEqual( l, [1,2,3,4] )
  self.assertEqual( l, "1,2,3,4" )
  self.assertEqual( l, "1 2 3 4" )
  self.assertEqual( str(l), "1,2,3,4" )
  
  l += [7, 8]
  self.assertEqual( l, ['1','2','3','4','7','8'] )
  
  l -= "2, 3"
  self.assertEqual( l, ['1','4','7','8'] )
  
  l -= "5"
  self.assertEqual( l, ['1','4','7','8'] )
  
  l.extend_front( "10,12" )
  self.assertEqual( l, ['10','12','1','4','7','8'] )
  
  l.extend( "0,-1" )
  self.assertEqual( l, ['10','12','1','4','7','8', '0', '-1'] )

#//===========================================================================//

if __name__ == "__main__":
  runTests()
