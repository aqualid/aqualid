import sys
import os.path
import time

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_task_manager import TaskManager

#//===========================================================================//

def   _doAppend( arg, results, delay = 0 ):
  time.sleep( delay )
  results.add( arg )

#//===========================================================================//

def   _doFail( delay = 0 ):
  time.sleep( delay )
  raise Exception()

#//===========================================================================//

@testcase
def test_task_manager(self):
  tm = TaskManager( 4 )
  
  results = set()
  
  for i in range(0,8):
    tm.addTask( i, _doAppend, i, results )
  
  time.sleep(0.5) # wait until all tasks are done
  
  done_tasks = tm.completedTasks()
  expected_tasks = sorted( zip( range(0,8), [None] * 8 ) )
  
  self.assertEqual( sorted(done_tasks), expected_tasks )
  self.assertEqual( results, set(range(0,8)) )

#//===========================================================================//

@testcase
def test_task_manager_fail(self):
  tm = TaskManager( 4 )
  
  for i in range(0,8):
    tm.addTask( i, _doFail, 0.1 )
  
  time.sleep(1) # wait until all tasks are done
  
  done_tasks = tm.completedTasks()
  for t, i in zip( sorted(done_tasks), range(0,8) ):
    self.assertEqual( t[0], i )
    self.assertIsInstance( t[1], Exception )

#//===========================================================================//

@testcase
def test_task_manager_stop(self):
  tm = TaskManager( 4 )
  
  results = set()
  
  for i in range(0,8):
    tm.addTask( i, _doAppend, i, results, 1 )
  
  time.sleep(0.2)
  
  tm.stop()
  tm.stop()
  
  done_tasks = tm.completedTasks()
  expected_tasks = sorted( zip( range(0,4), [None] * 4 ) )
  
  self.assertEqual( sorted(done_tasks), expected_tasks )
  self.assertEqual( results, set(range(0,4)) )

#//===========================================================================//

@testcase
def test_task_manager_one_fail(self):
  tm = TaskManager( 4 )
  
  results = set()
  
  for i in range(0,3):
    tm.addTask( i, _doAppend, i, results, 0.3 )
  
  tm.addTask( 3, _doFail, 0.1 )
  
  for i in range(4,8):
    tm.addTask( i, _doAppend, i, results, 0 )
  
  time.sleep(1)
  
  done_tasks = sorted( tm.completedTasks() )
  self.assertEqual( len(done_tasks), 8 )
  
  expected_tasks = sorted( zip( range(0,8), [None] * 8 ) )
  
  self.assertEqual( done_tasks[:3], expected_tasks[:3] )
  
  self.assertEqual( done_tasks[3][0], 3 )
  self.assertIsInstance( done_tasks[3][1], Exception )
  
  self.assertEqual( done_tasks[4:], expected_tasks[4:] )

#//===========================================================================//

if __name__ == "__main__":
  runTests()
