#
# Copyright (c) 2011,2012 The developers of Aqualid project - http://aqualid.googlecode.com
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
  'TaskManager',
)

import threading

from .aql_logging import logWarning

try:
  import queue
except ImportError:
  import Queue as queue # python 2

#//===========================================================================//

class _ExitException( Exception ):
  pass

class _FinishingException( Exception ):
  pass

def   _exitEventFunction():
  raise _ExitException()

def   _finishingEventFunction():
  raise _FinishingException()

_exit_task = ( None, _exitEventFunction, [], {} )
_finishing_task = ( None, _finishingEventFunction, [], {} )

#//===========================================================================//

class _TaskExecutor( threading.Thread ):
  
  def __init__(self, tasks, completed_tasks, exit_event, finish_event ):
    
    super(_TaskExecutor,self).__init__()
    
    self.tasks            = tasks
    self.completed_tasks  = completed_tasks
    self.exit_event       = exit_event
    self.finish_event     = finish_event
    self.daemon           = True  # let that main thread to exit even if task threads are still active
    
    self.start()
  
  #//-------------------------------------------------------//
  
  def run(self):
    
    tasks             = self.tasks
    completed_tasks   = self.completed_tasks
    is_exiting        = self.exit_event.is_set
    is_finishing      = self.finish_event.is_set
    
    while not is_exiting():
      try:
        block = not is_finishing()
        
        task_id, func, args, kw = tasks.get( block )
        tasks.task_done()
      except queue.Empty:
        break
      
      try:
        func(*args, **kw)
        
        if task_id is not None:
          success = (task_id, None)
          completed_tasks.put( success )
      
      except _FinishingException:
        break
      
      except _ExitException:
        break
      
      except (Exception, BaseException) as err:
        if task_id is not None:
          fail = ( task_id, err )
          completed_tasks.put( fail )
        else:
          logWarning("Task failed with error: %s" % str(err) )

#//===========================================================================//

class TaskManager (object):
  __slots__ = (
    
    'tasks',
    'threads',
    'completed_tasks',
    'exit_event',
    'finish_event',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__(self, num_threads ):
    self.tasks            = queue.Queue()
    self.completed_tasks  = queue.Queue()
    self.exit_event       = threading.Event()
    self.finish_event     = threading.Event()
    self.threads          = []
    
    self.start( num_threads )
  
  #//-------------------------------------------------------//
  
  def   start( self, num_threads ):
    
    self.exit_event.clear()
    self.finish_event.clear()
    threads = self.threads
    
    num_threads -= len(threads)
    
    while num_threads > 0:
      num_threads -= 1
      t = _TaskExecutor( self.tasks, self.completed_tasks, self.exit_event, self.finish_event )
      threads.append( t )
  
  #//-------------------------------------------------------//
  
  def   __stop( self, stop_event, stop_task ):
    
    if not self.threads:
      return
    
    stop_event.set()
    for t in self.threads:
      self.tasks.put( stop_task )
    
    for t in self.threads:
      t.join()
    
    self.threads = []
    self.tasks = queue.Queue()
  
  #//-------------------------------------------------------//
  
  def   stop( self ):
    self.__stop( self.exit_event, _exit_task )
  
  #//-------------------------------------------------------//
  
  def   finish( self ):
    self.__stop( self.finish_event, _finishing_task )
  
  #//-------------------------------------------------------//
  
  def   addTask( self, task_id, function, *args, **kw ):
    if not self.exit_event.is_set() and not self.finish_event.is_set():
      task = ( task_id, function, args, kw )
      self.tasks.put( task )
  
  #//-------------------------------------------------------//
  
  def   completedTasks( self ):
    completed_tasks = []
    is_exit = self.exit_event.is_set
    
    if is_exit():
      self.stop()
    
    while True:
      try:
        block = not (completed_tasks or is_exit() or self.tasks.empty())
        task_result = self.completed_tasks.get( block = block )
        
        completed_tasks.append( task_result )
        self.completed_tasks.task_done()
      except queue.Empty:
        break
    
    return completed_tasks
