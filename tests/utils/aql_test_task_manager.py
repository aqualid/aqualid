import sys
import os.path
import time

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests
from aql.utils import TaskManager, TaskResult

#//===========================================================================//

def   _doAppend( arg, results, delay = 0 ):
  time.sleep( delay )
  results.add( arg )

#//===========================================================================//

def   _doFail( delay = 0 ):
  time.sleep( delay )
  raise Exception()

#//===========================================================================//

class TestTaskManager( AqlTestCase ):
  def test_task_manager(self):
    tm = TaskManager( 4 )
    
    results = set()
    
    for i in range(0,8):
      tm.addTask( i, _doAppend, i, results )
    
    time.sleep(0.5) # wait until all tasks are done
    
    done_tasks = tm.finishedTasks()
    expected_tasks = sorted( zip( range(0,8), [None] * 8, [None] * 8 ) )
    
    self.assertEqual( sorted(done_tasks), expected_tasks )
    self.assertEqual( results, set(range(0,8)) )

  #//===========================================================================//

  def test_task_manager_fail(self):
    tm = TaskManager( num_threads = 4 )
    
    for i in range(100):
      tm.addTask( i, _doFail, 0.0 )
    
    time.sleep(1) # wait until all tasks are done
    
    done_tasks = tm.finishedTasks()
    
    self.assertEqual( len(done_tasks), 100 )
    
    for i, t in enumerate( sorted(done_tasks) ):
      self.assertEqual( t[0], i )
      self.assertIsInstance( t[1], Exception )

  #//===========================================================================//

  def test_task_manager_stop(self):
    
    jobs = 4
    num_tasks = 8
    
    tm = TaskManager( num_threads = jobs )
    
    results = set()
    
    for i in range(num_tasks):
      tm.addTask( i, _doAppend, i, results, 1 )
    
    time.sleep(0.2)
    
    tm.stop()
    tm.stop()
    
    done_tasks = sorted( tm.finishedTasks(), key = lambda result: result.task_id )
    
    expected_tasks = [ TaskResult( task_id, error, result ) \
                       for task_id, error, result in zip(range(jobs), [None] * jobs, [None] * jobs ) ] 
    
    self.assertEqual( done_tasks, expected_tasks )
    self.assertEqual( results, set(range(jobs)) )

  #//===========================================================================//
  
  def test_task_manager_finish(self):
    tm = TaskManager( 1 )
    
    results = set()
    
    num_tasks = 8
    
    for i in range(num_tasks):
      tm.addTask( i, _doAppend, i, results, 0.2 )
    
    tm.finish()
    
    for i in range(num_tasks, num_tasks * 2):
      tm.addTask( i, _doAppend, i, results, 0.2 )
    
    self.assertEqual( results, set(range(num_tasks)) )
    
    done_tasks = tm.finishedTasks()
    expected_tasks = [ TaskResult( task_id, error, result ) \
                       for task_id, error, result in zip(range(num_tasks), [None] * num_tasks, [None] * num_tasks ) ] 
    
    self.assertEqual( sorted(done_tasks), expected_tasks )

  #//===========================================================================//

  def test_task_manager_one_fail(self):
    tm = TaskManager( 4 )
    
    results = set()
    
    num_tasks = 3
    
    tm.addTask( 0, _doAppend, 0, results, 0.3 )
    
    tm.addTask( 1, _doFail, 0.1 )
    
    tm.addTask( 2, _doAppend, 2, results, 0 )
    
    time.sleep(1)
    
    done_tasks = sorted( tm.finishedTasks(), key= lambda v: v.task_id )
    self.assertEqual( len(done_tasks), num_tasks )
    
    expected_tasks = [ TaskResult( task_id, error, result ) \
                       for task_id, error, result in zip(range(num_tasks), [None] * num_tasks, [None] * num_tasks ) ] 
    
    self.assertEqual( done_tasks[0], expected_tasks[0] )
    
    self.assertEqual( done_tasks[1].task_id, 1 )
    self.assertIsInstance( done_tasks[1].error, Exception )
    
    self.assertEqual( done_tasks[2], expected_tasks[2] )
  
  #//===========================================================================//

  def test_task_manager_stop_on_fail(self):
    tm = TaskManager( 4, stop_on_fail = True )
    
    results = set()
    
    num_tasks = 8
    
    for i in range(3):
      tm.addTask( i, _doAppend, i, results, 0.3 )
    
    tm.addTask( i + 1, _doFail, 0.1 )
    
    for i in range(i + 2,num_tasks):
      tm.addTask( i, _doAppend, i, results, 0 )
    
    time.sleep(1)
    
    done_tasks = sorted( tm.finishedTasks(), key=lambda t: t.task_id )
    self.assertEqual( len(done_tasks), 4 )
    
    expected_tasks = [ TaskResult( task_id, error, result ) \
                       for task_id, error, result in zip(range(4), [None] * num_tasks, [None] * num_tasks ) ] 

    self.assertEqual( done_tasks[:3], expected_tasks[:3] )
    
    self.assertEqual( done_tasks[3].task_id, 3 )
    self.assertIsInstance( done_tasks[3].error, Exception )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
