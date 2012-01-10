import threading

try:
  import queue
except ImportError:
  import Queue as queue # python 2

from aql_node import Node
from aql_logging import logError
from aql_utils import toSequence

#//===========================================================================//

class _ExitExecption( Exception ):
  pass

def   _exitEventFunction():
  raise _ExitException()

_exit_task = ( None, _exitEventFunction, [], {} )

#//===========================================================================//

class _TaskProcessor( threading.Thread ):
  
  def __init__(self, tasks, completed_tasks, stop_on_error, exit_event ):
    
    super(_TaskJob,self).__init__(self)
    
    self.tasks            = tasks
    self.completed_tasks  = completed_tasks
    self.stop_on_error    = stop_on_error
    self.exit_event       = exit_event
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
        success = (id, None)
        completed_tasks.put( success )
      
      except _ExitException:
        exit_event.set()
      
      except Exception as err:
        fail = ( id, err )
        completed_tasks.put( fail )
        
        if self.stop_on_error:
          exit_event.set()
      
      finally:
        tasks.task_done()
    
    tasks.put( _exit_task ) # exit other threads too

#//===========================================================================//

class TaskManager (object):
  __slots__ = (
    
    'tasks',
    'threads',
    'completed_tasks',
    'stop_on_error',
    'exit_event',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__(self, num_threads = 1, stop_on_error = True ):
    self.start( num_threads, stop_on_error )
  
  #//-------------------------------------------------------//
  
  def   start( num_threads = 1, stop_on_error = True )
    self.tasks            = queue.Queue()
    self.completed_tasks  = queue.Queue()
    self.stop_on_error    = stop_on_error
    self.exit_event       = threading.Event()
    
    threads = []
    
    while num_threads > 0:
      num_threads -= 1
      t = _TaskProcessor( self.tasks, self.completed_tasks, stop_on_error )
      threads.append( t )
    
    self.threads = threads
  
  #//-------------------------------------------------------//
  
  def   stop(self):
    
    self.exit_event.set()
    self.tasks.put( _exit_task )
    
    for t in self.threads:
      t.join()
    
    self.threads          = []
    self.tasks            = None
    self.completed_tasks  = None
    self.stop_on_error    = stop_on_error
    self.exit_event       = None
  
  #//-------------------------------------------------------//
  
  def   addTask( self, id, function, *args, **kw ):
    if not self.threads:
      raise Exception("TaskManager is not started.")
      
    task = ( id, function, args, kw )
    self.tasks.put( task )
  
  #//-------------------------------------------------------//
  
  def   completedTasks( self ):
    if not self.threads:
      raise Exception("TaskManager is not started.")
    
    completed_tasks = []
    
    while True:
      try:
        block = not completed_tasks
        id, err = self.completed_tasks.get( block = block )
        
        completed_tasks.append( id )
        self.completed_tasks.task_done()
      except queue.Empty:
        break
    
    return completed_tasks
