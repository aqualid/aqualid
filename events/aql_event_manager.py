import threading

from aql_task_manager import TaskManager
from aql_event_handler import EventHandler

class EventManager( EventHandler ):
  
  __slots__ = \
  (
    'lock',
    'handlers',
    'tm',
  )
  
  #//-------------------------------------------------------//

  def   __init__(self):
    self.lock = threading.Lock()
    self.handlers = {}
    self.tm = TaskManager( 0 )
  
  #//-------------------------------------------------------//
  
  def   addHandler( self, handler ):
    with self.lock:
      handlers = self.handlers.setdefault( event_id, [] )
      handlers.append( handler )
      
      self.tm.start( len(handlers) )
  
  #//-------------------------------------------------------//
  
  def   outdatedNode( self, node ):
    logInfo("Outdated node: %s" % node )
  
  #//-------------------------------------------------------//
  
  def   dataFileIsNotSync( self, filename ):
    logWarning("Internal error: DataFile is unsynchronized")
  
  #//-------------------------------------------------------//
  
  def   depValueIsCyclic( self, value ):
    logWarning("Internal error: Cyclic dependency value: %s" % value )
  
  #//-------------------------------------------------------//
  
  def   unknownValue( self, value ):
    logWarning("Internal error: Unknown value: %s " % value )
  #//-------------------------------------------------------//
  
  def   release( self ):
    self.tm.stop()
