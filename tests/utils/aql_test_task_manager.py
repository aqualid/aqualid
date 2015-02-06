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
    
    jobs = 1
    tm = TaskManager( 0 )
    
    results = set()
    
    num_of_tasks = 8
    
    for i in range(num_of_tasks):
      tm.addTask( num_of_tasks - i, i, _doAppend, i, results )
    
    tm.start( jobs )
    
    time.sleep(0.5) # wait until all tasks are done
    
    done_tasks = [result.task_id for result in tm.finishedTasks()]
    expected_tasks = sorted(range(num_of_tasks), reverse = True)
    
    self.assertEqual( done_tasks, expected_tasks )
    self.assertEqual( results, set(range(num_of_tasks)) )

  #//===========================================================================//

  def test_task_manager_fail(self):
    
    jobs = 4
    
    tm = TaskManager( jobs )
    
    num_of_tasks = 100
    
    for i in range(num_of_tasks):
      tm.addTask( 0, i, _doFail, 0.0 )
    
    tm.start( jobs )
    
    time.sleep(0.5) # wait until all tasks are done
    
    done_tasks = tm.finishedTasks()
    
    self.assertEqual( len(done_tasks), num_of_tasks )
    
    for i, t in enumerate( sorted(done_tasks) ):
      self.assertEqual( t.task_id, i )
      self.assertIsNotNone( t.error )

  #//===========================================================================//

  def test_task_manager_stop(self):
    
    jobs = 4
    num_tasks = 8
    
    tm = TaskManager( num_threads = jobs )
    
    results = set()
    
    for i in range(num_tasks):
      tm.addTask( 0, i, _doAppend, i, results, 1 )
    
    time.sleep(0.2)
    
    tm.stop()
    tm.stop()
    
    done_tasks = sorted( result.task_id for result in tm.finishedTasks() )
    
    self.assertEqual( len(done_tasks), jobs )
    self.assertEqual( results, set(done_tasks) )

  #//===========================================================================//

  def test_task_manager_one_fail(self):
    tm = TaskManager( 4 )
    
    results = set()
    
    num_tasks = 3
    
    tm.addTask( 0, 0, _doAppend, 0, results, 0.3 )
    
    tm.addTask( 0, 1, _doFail, 0.1 )
    
    tm.addTask( 0, 2, _doAppend, 2, results, 0 )
    
    time.sleep(1)
    
    done_tasks = sorted( tm.finishedTasks(), key= lambda v: v.task_id )
    self.assertEqual( len(done_tasks), num_tasks )
    
    expected_tasks = [ TaskResult( task_id, error, result ) \
                       for task_id, error, result in zip(range(num_tasks), [None] * num_tasks, [None] * num_tasks ) ] 
    
    self.assertEqual( done_tasks[0], expected_tasks[0] )
    
    self.assertEqual( done_tasks[1].task_id, 1 )
    self.assertIsNotNone( done_tasks[1].error )
    
    self.assertEqual( done_tasks[2], expected_tasks[2] )
  
  #//===========================================================================//

  def test_task_manager_stop_on_fail(self):
    num_tasks = 8
    jobs = 4
    
    tm = TaskManager( 0, stop_on_fail = True )
    
    results = set()
    
    for i in range( jobs - 1 ):
      tm.addTask( 0, i, _doAppend, i, results, 0.5 )
    
    tm.addTask( 1, jobs - 1, _doFail, 0.1 )
    
    for i in range(jobs, num_tasks):
      tm.addTask( 2, i, _doAppend, i, results, 0 )
    
    tm.start( jobs )
    
    time.sleep(1)
    
    done_tasks = sorted( tm.finishedTasks(), key=lambda t: t.task_id )
    print()
    self.assertEqual( len(done_tasks), jobs )
    
    expected_tasks = [ TaskResult( task_id, error, result ) \
                       for task_id, error, result in zip(range(jobs), [None] * num_tasks, [None] * num_tasks ) ] 

    self.assertEqual( done_tasks[:3], expected_tasks[:3] )
    
    self.assertEqual( done_tasks[3].task_id, 3 )
    self.assertIsNotNone( done_tasks[3].error )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
