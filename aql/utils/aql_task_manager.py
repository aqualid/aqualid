#
# Copyright (c) 2011,2012 The developers of Aqualid project
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__all__ = (
  'TaskManager', 'TaskResult'
)

import threading
import traceback

from .aql_logging import logWarning

try:
  import queue
except ImportError:
  import Queue as queue # python 2

#//===========================================================================//

class _ExitException( Exception ):
  pass

def   _exitEventFunction():
  raise _ExitException()

_exit_task = ( None, _exitEventFunction, [], {} )

#//===========================================================================//

class TaskResult (object):
  __slots__ = ('task_id', 'error', 'result')
  
  def   __init__(self, task_id = None, result = None, error = None ):
    self.task_id = task_id
    self.result = result
    self.error = error
  
  def   __lt__(self, other):
    return (self.task_id, self.result, self.error) < (other.task_id, other.result, other.error)
  
  def   __eq__(self, other):
    return (self.task_id, self.result, self.error) == (other.task_id, other.result, other.error)
  
  def   __ne__(self, other):
    return not self.__eq__(other)
  
  def   __str__(self):
    return "task_id: %s, result: %s, error: %s" % (self.task_id, self.result, self.error)

#//===========================================================================//

class _TaskExecutor( threading.Thread ):
  
  def __init__(self, tasks, finished_tasks, fail_handler, exit_event, with_backtrace ):
    
    super(_TaskExecutor,self).__init__()
    
    self.tasks            = tasks
    self.finished_tasks   = finished_tasks
    self.fail_handler     = fail_handler
    self.exit_event       = exit_event
    self.daemon           = True  # let that main thread to exit even if task threads are still active
    self.with_backtrace   = with_backtrace
    
    self.start()
  
  #//-------------------------------------------------------//
  
  def run(self):
    
    tasks             = self.tasks
    finished_tasks    = self.finished_tasks
    is_exiting        = self.exit_event.is_set
    
    while not is_exiting():
      
      task_id, func, args, kw = tasks.get()
      
      task_result = TaskResult( task_id = task_id ) if task_id is not None else None
      
      try:
        result = func(*args, **kw)
        
        if task_result is not None:
          task_result.result = result
      
      except _ExitException:
        task_result = None
        break
      
      except (Exception, BaseException) as ex:
        task_result.error = "Internal error"
        
        if self.with_backtrace:
          err = traceback.format_exc()
        else:
          err = str(ex)
                      
        if task_id is not None:
          task_result.error = err
        else:
          logWarning( "Task failed with error: %s" % (err,) )
        
        self.fail_handler( err )
      
      finally:
        if task_result is not None:
          finished_tasks.put( task_result )
        
        tasks.task_done()


#//===========================================================================//

class TaskManager (object):
  __slots__ = (
    
    'lock',
    'threads',
    'exit_event',
    'tasks',
    'finished_tasks',
    'unfinished_tasks',
    'stop_on_fail',
    'with_backtrace',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__(self, num_threads, stop_on_fail = False, with_backtrace = True ):
    self.tasks            = queue.Queue()
    self.finished_tasks   = queue.Queue()
    self.exit_event       = threading.Event()
    self.lock             = threading.Lock()
    self.unfinished_tasks = 0
    self.threads          = []
    self.stop_on_fail     = stop_on_fail
    self.with_backtrace   = with_backtrace
    
    self.start( num_threads )
  
  #//-------------------------------------------------------//
  
  def   start( self, num_threads ):
    with self.lock:
      if self.exit_event.is_set():
        self.__stop()
      
      threads = self.threads
      
      num_threads -= len(threads)
      
      fail_handler = self.failHandler if self.stop_on_fail else lambda err: None
      
      while num_threads > 0:
        num_threads -= 1
        t = _TaskExecutor( self.tasks, self.finished_tasks, fail_handler, self.exit_event, self.with_backtrace )
        threads.append( t )
  
  #//-------------------------------------------------------//
  
  def   __stop( self ):
    threads = self.threads
    if not threads:
      return
    
    for t in threads:
      self.tasks.put( _exit_task )
    
    for t in threads:
      t.join()
    
    self.threads = []
    self.tasks = queue.Queue()
    self.exit_event.clear()
  
  #//-------------------------------------------------------//
  
  def   stop( self ):
    self.exit_event.set()
    with self.lock:
      self.__stop()
  
  #//-------------------------------------------------------//
  
  def   finish( self ):
    with self.lock:
      self.__stop()
  
  #//-------------------------------------------------------//

  #noinspection PyUnusedLocal
  def   failHandler( self, err ):
    self.exit_event.set()
  
  #//-------------------------------------------------------//
  
  def   addTask( self, task_id, function, *args, **kw ):
    with self.lock:
      if not self.exit_event.is_set():
        task = ( task_id, function, args, kw )
        self.tasks.put( task )
        if task_id is not None:
          self.unfinished_tasks += 1
  
  #//-------------------------------------------------------//
  
  def   finishedTasks( self, block = True ):
    finished_tasks = []
    is_exit = self.exit_event.is_set
    
    with self.lock:
      
      if is_exit():
        self.__stop()
      
      if block:
        block = (self.unfinished_tasks > 0) and self.threads
      
      while True:
        try:
          task_result = self.finished_tasks.get( block = block )
          block = False
          
          finished_tasks.append( task_result )
          self.finished_tasks.task_done()
        except queue.Empty:
          break
      
      self.unfinished_tasks -= len( finished_tasks )
      assert self.unfinished_tasks >= 0
    
    return finished_tasks
