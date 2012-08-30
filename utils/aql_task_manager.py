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

import threading

from aql_logging import logWarning

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

class _TaskProcessor( threading.Thread ):
  
  def __init__(self, tasks, completed_tasks, exit_event, stop_on_error ):
    
    super(_TaskProcessor,self).__init__()
    
    self.tasks            = tasks
    self.completed_tasks  = completed_tasks
    self.exit_event       = exit_event
    self.stop_on_error    = stop_on_error
    self.daemon           = True  # let that main thread to exit even if task threads are still active
    
    self.start()
  
  #//-------------------------------------------------------//
  
  def run(self):
    
    tasks             = self.tasks
    completed_tasks   = self.completed_tasks
    exit_event        = self.exit_event
    
    while not exit_event.is_set():
      id, func, args, kw = tasks.get()
      try:
        func(*args, **kw)
        if id is not None:
          success = (id, None)
          completed_tasks.put( success )
      
      except _ExitException:
        exit_event.set()
      
      except (Exception, BaseException) as err:
        if id is not None:
          fail = ( id, err )
          completed_tasks.put( fail )
          if self.stop_on_error:
            exit_event.set()
        else:
          logWarning("Task failed with error: %s" % str(err) )
      
      finally:
        tasks.task_done()
    
    tasks.put( _exit_task ) # exit other threads too

#//===========================================================================//

class TaskManager (object):
  __slots__ = (
    
    'tasks',
    'threads',
    'completed_tasks',
    'exit_event',
    'stop_on_error',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__(self, num_threads, stop_on_error = False ):
    self.tasks            = queue.Queue()
    self.completed_tasks  = queue.Queue()
    self.exit_event       = threading.Event()
    self.threads          = []
    self.stop_on_error    = stop_on_error
    
    self.start( num_threads )
  
  #//-------------------------------------------------------//
  
  def   start( self, num_threads ):
    
    self.exit_event.clear()
    threads = self.threads
    
    num_threads -= len(threads)
    
    while num_threads > 0:
      num_threads -= 1
      t = _TaskProcessor( self.tasks, self.completed_tasks, self.exit_event, self.stop_on_error )
      threads.append( t )
  
  #//-------------------------------------------------------//
  
  def   stop(self):
    
    self.exit_event.set()
    self.tasks.put( _exit_task )
    
    for t in self.threads:
      t.join()
    
    self.threads = []
    self.tasks = queue.Queue()
  
  #//-------------------------------------------------------//
  
  def   addTask( self, id, function, *args, **kw ):
    task = ( id, function, args, kw )
    self.tasks.put( task )
  
  #//-------------------------------------------------------//
  
  def   completedTasks( self ):
    completed_tasks = []
    isExit = self.exit_event.is_set
    
    while True:
      try:
        block = (not completed_tasks) and (not isExit())
        task_result = self.completed_tasks.get( block = block )
        
        completed_tasks.append( task_result )
        self.completed_tasks.task_done()
      except queue.Empty:
        break
    
    return completed_tasks
