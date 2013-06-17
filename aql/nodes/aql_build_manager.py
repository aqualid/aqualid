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
  'BuildManager',
  'ErrorNodeDependencyCyclic', 'ErrorNodeDependencyUnknown',
  'eventBuildNodeFailed', 'eventBuildStatusActualNode', 'eventBuildStatusOutdatedNode', 'eventBuildTargetTwiceByNodes',
  'eventBuildingNodes', 'eventRebuildNode', 'eventNodeBuilding', 'eventNodeBuildingFinished',
)

import threading
import traceback

from aql.types import toSequence
from aql.utils import eventInfo, eventStatus, eventWarning, logInfo, logError, logWarning, TaskManager
from aql.values import ValuesFile

from .aql_builder import RebuildNode

#//===========================================================================//

@eventStatus
def   eventBuildStatusOutdatedNode( node ):
  logInfo("Outdated node: %s" % node )

#//===========================================================================//

@eventStatus
def   eventBuildStatusActualNode( node ):
  logInfo("Actual node: %s" % node )

#//===========================================================================//

@eventWarning
def   eventBuildTargetTwiceByNodes( value, node1, node2 ):
  logWarning("Target '%s' is built twice by different nodes: '%s', '%s' " % ( value.name, node1, node2 ) )

#//===========================================================================//

@eventStatus
def   eventBuildingNodes( total_nodes ):
  logInfo("Building %s nodes" % total_nodes )

#//===========================================================================//

@eventInfo
def   eventRebuildNode( node ):
  logInfo("Rebuild node: %s" % node.builder.buildStr( node ) )

#//===========================================================================//

@eventStatus
def   eventBuildNodeFailed( node, error ):
  logError("Failed node: %s" % node.buildStr() )
  logError("Error: %s" % str(error) )
  try:
    traceback.print_tb( error.__traceback__ )
  except AttributeError:
    pass

#//===========================================================================//

@eventStatus
def   eventNodeBuilding( node ):
  logInfo("Building node: %s" % node.buildStr() )

#//===========================================================================//

@eventStatus
def   eventNodeBuildingFinished( node ):
  logInfo("Finished node: %s" % node.buildStr() )

#//===========================================================================//

class   ErrorNodeDependencyCyclic( Exception ):
  def   __init__( self, node ):
    msg = "Node has a cyclic dependency: %s" % str(node)
    super(ErrorNodeDependencyCyclic, self).__init__( msg )

#//===========================================================================//

class   ErrorNodeDependencyUnknown(Exception):
  def   __init__( self, node, dep_node ):
    msg = "Unable to add dependency to node '%s' from node '%s'" % (node, dep_node)
    super(ErrorNodeDependencyUnknown, self).__init__( msg )

#//===========================================================================//

class   InternalErrorRemoveNonTailNode( Exception ):
  def   __init__( self, node ):
    msg = "Removing non-tail node: %s" % str(node)
    super(InternalErrorRemoveNonTailNode, self).__init__( msg )

#//===========================================================================//

class   InternalErrorRemoveUnknownTailNode(Exception):
  def   __init__( self, node, dep_node ):
    msg = "Remove unknown tail node: : %s" % str(node)
    super(InternalErrorRemoveUnknownTailNode, self).__init__( msg )

#//===========================================================================//

class _NodesTree (object):
  
  __slots__ = \
  (
    'lock',
    'node_deps',
    'dep_nodes',
    'tail_nodes',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self ):
    self.lock = threading.Lock()
    self.node_deps = {}
    self.dep_nodes = {}
    self.tail_nodes = set()
  
  #//-------------------------------------------------------//
  
  def   __len__(self):
    return len(self.node_deps)
  
  #//-------------------------------------------------------//
  
  def   __hasCycle( self, node, new_deps ):
    
    if node in new_deps:
      return True
    
    deps = set(new_deps)
    node_deps = self.node_deps
    
    while deps:
      dep = deps.pop()
      
      dep_deps = node_deps[dep]
      
      if node in dep_deps:
        return True
      
      deps |= dep_deps
    
    return False
  
  #//-------------------------------------------------------//
  
  def   __depends( self, node, deps ):
    
    node_deps = self.node_deps
    dep_nodes = self.dep_nodes
    
    try:
      current_node_deps = node_deps[ node ]
      
      new_deps = set(deps) - current_node_deps
      
      if not new_deps:
        return
      
      if self.__hasCycle( node, new_deps ):
        raise ErrorNodeDependencyCyclic( node )
      
      self.tail_nodes.discard( node )
      
      #//-------------------------------------------------------//
      
      current_node_deps |= new_deps
      
      #//-------------------------------------------------------//
      
      for dep in new_deps:
        dep_nodes[ dep ].add( node )
    
    except KeyError as dep_node:
      raise ErrorNodeDependencyUnknown( node, dep_node.args[0] )
    
  #//-------------------------------------------------------//
  
  def   __add( self, nodes ):
      node_deps = self.node_deps
      
      for node in nodes:
        
        if node not in node_deps:
          self.node_deps[ node ] = set()
          self.dep_nodes[ node ] = set()
          self.tail_nodes.add( node )
          
          self.__add( node.source_nodes )   # TODO: recursively add sources and depends
          self.__add( node.dep_nodes )      # It would be better to rewrite this code to aviod the recursion
          
          self.__depends( node, node.source_nodes )
          self.__depends( node, node.dep_nodes )
    
  #//-------------------------------------------------------//
  
  def   add( self, nodes ):
    with self.lock:
      self.__add( toSequence( nodes ) )
    
  #//-------------------------------------------------------//
  
  def   depends( self, node, deps ):
    with self.lock:
      deps = toSequence( deps )
      
      self.__add( deps )
      self.__depends( node, deps )
  
  #//-------------------------------------------------------//
  
  def   removeTail( self, node ):
    with self.lock:
      node_deps = self.node_deps
      
      try:
        if node_deps[node]:
          raise InternalErrorRemoveNonTailNode( node )
      except KeyError as node:
        raise InternalErrorRemoveUnknownTailNode( node.args[0] )
      
      tail_nodes = self.tail_nodes
      
      del node_deps[node]
      tail_nodes.remove( node )
      
      for dep in self.dep_nodes.pop( node ):
        d = node_deps[ dep ]
        d.remove( node )
        if not d:
          tail_nodes.add( dep )
    
  #//-------------------------------------------------------//
  
  def   tails( self ):
    with self.lock:
      return set( self.tail_nodes )
  
  #//-------------------------------------------------------//
  
  def   selfTest( self ):
    with self.lock:
      if set(self.node_deps) != set(self.dep_nodes):
        raise AssertionError("Not all deps are added")
      
      all_dep_nodes = set()
      
      for node in self.dep_nodes:
        if node not in self.node_deps:
          raise AssertionError("Missed node: %s" % str(node) )
        
        #~ node_deps = node.source_nodes | node.dep_nodes
        node_deps = self.node_deps[node]
        
        if not node_deps:
          if node not in self.tail_nodes:
            raise AssertionError("Missed tail node: %s"  % str(node) )
        else:
          if node in self.tail_nodes:
            raise AssertionError("Invalid tail node: %s"  % str(node) )
        
        all_dep_nodes |= node_deps
        
        #~ if (node_deps - (node.source_nodes | node.dep_nodes)):
          #~ raise AssertionError("self.node_deps[node] != node_deps for node: %s"  % str(node) )
        
        for dep in node_deps:
          if node not in self.dep_nodes[dep]:
            raise AssertionError("node not in self.dep_nodes[dep]: dep: %s, node: %s"  % (dep, node) )
      
      if (all_dep_nodes - set(self.dep_nodes)):
        raise AssertionError("Not all deps are added")

#//===========================================================================//

class  _VFiles( object ):
  __slots__ = \
  (
    'names',
    'handles',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self ):
    self.handles = {}
    self.names = {}
  
  #//-------------------------------------------------------//
  
  def   __getitem__( self, node ):
    
    builder = node.builder
    builder_name = builder.name
    
    try:
      vfilename = self.names[ builder_name ]
    except KeyError:
      build_path = builder.buildPath()
      vfilename = build_path.join('.aql.db').abs()
      self.names[ builder_name ] = vfilename
    
    try:
      return self.handles[ vfilename ]
    
    except KeyError:
      vfile = ValuesFile( vfilename )
      self.handles[ vfilename ] = vfile
      
      return vfile

  #//-------------------------------------------------------//
  
  def   close(self):
    for vfile in self.handles.values():
      vfile.close()
    
    self.handles.clear()
    self.names.clear()
  
  #//-------------------------------------------------------//
  
  def   __enter__(self):
    return self
  
  #//-------------------------------------------------------//
  
  def   __exit__(self, exc_type, exc_value, backtrace):
    self.close()

#//===========================================================================//

def   _buildNode( build_manager, vfile, builder, node ):
  
  eventNodeBuilding( node )
  
  builder.build( build_manager, vfile, node )
  
  eventNodeBuildingFinished( node )


#//===========================================================================//

class _NodesBuilder (object):
  
  __slots__ = \
  (
    'vfiles',
    'jobs',
    'keep_going',
    'task_manager',
    'prebuild_nodes',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, jobs, keep_going ):
    self.vfiles = _VFiles()
    self.jobs = jobs
    self.keep_going = keep_going
    self.prebuild_nodes = {}
  
  #//-------------------------------------------------------//
  
  def   __enter__(self):
    return self
  
  #//-------------------------------------------------------//
  
  def   __exit__(self, exc_type, exc_value, backtrace):
    self.close()
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    if attr == 'task_manager':
      self.task_manager = tm = TaskManager( num_threads = self.jobs )
      return tm
    
    raise AttributeError( "%s instance has no attribute '%s'" % (type(self), attr) )
    
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, nodes ):
    completed_nodes = []
    failed_nodes = {}
    rebuild_nodes = []
    
    add_task = self.task_manager.addTask
    
    for node in nodes:
      vfile = self.vfiles[ node ]
      
      builder = node.builder
      
      pre_nodes = self.prebuild_nodes.pop( node, None )
      
      if pre_nodes:
        builder.prebuildFinished( build_manager, vfile, node, pre_nodes )
      else:
        pre_nodes = builder.prebuild( build_manager, vfile, node )
        if pre_nodes:
          self.prebuild_nodes[ node ] = pre_nodes
          build_manager.depends( node, pre_nodes )
          rebuild_nodes.append( node )
          continue
      
      if builder.actual( vfile, node ):
        completed_nodes.append( node )
      else:
        add_task( node, builder.build, build_manager, vfile )
    
    if not completed_nodes and not rebuild_nodes:
      finished_tasks = self.task_manager.completedTasks()
      
      for node, exception in finished_tasks:
        if exception is None:
          completed_nodes.append( node )
        else:
          if isinstance( exception, RebuildNode ):
            eventRebuildNode( node )
            rebuild_nodes.append( node )
          else:
            if not self.keep_going:
              self.task_manager.stop()
              
            eventBuildNodeFailed( node, exception )
            failed_nodes[ node ] = exception
    
    return completed_nodes, failed_nodes, rebuild_nodes
  
  #//-------------------------------------------------------//
  
  def   close( self ):
    self.task_manager.finish()
    self.vfiles.close()

#//===========================================================================//

class BuildManager (object):
  
  __slots__ = \
  (
    '_nodes',
    '_jobs'
  )
  
  #//-------------------------------------------------------//
  
  def   __init__(self):
    self._nodes = _NodesTree()
    self._jobs = 1
  
  #//-------------------------------------------------------//
  
  def   add( self, nodes ):
    self._nodes.add( nodes )
  
  #//-------------------------------------------------------//
  
  def   depends( self, node, deps ):
    self._nodes.depends( node, deps )
  
  #//-------------------------------------------------------//
  
  def   jobs( self ):
    return self._jobs
  
  #//-------------------------------------------------------//
  
  def   __len__(self):
    return len(self._nodes)
  
  #//-------------------------------------------------------//
  
  def   selfTest( self ):
    self._nodes.selfTest()
  
  #//-------------------------------------------------------//
  
  def   __checkAlreadyBuilt( self, target_nodes, node ):
    values = []
    values += node.targets()
    values += node.sideEffects()
    
    for value in values:
      other_node, other_value = target_nodes.setdefault( value.name, (node, value) )
      
      if other_value != value:
        eventBuildTargetTwiceByNodes( value, node, other_node )
  
  #//-------------------------------------------------------//
  
  def   build( self, jobs, keep_going ):
    
    with _NodesBuilder( jobs, keep_going ) as nodes_builder:
      
      self._jobs = nodes_builder.jobs
      
      eventBuildingNodes( len(self._nodes) )
      
      target_nodes = {}
      
      get_tails = self._nodes.tails
      
      build_nodes = nodes_builder.build
      removeTailNode = self._nodes.removeTail
      
      waiting_nodes = set()
      waitingDiff = waiting_nodes.difference_update
      
      failed_nodes = {}
      
      while True:
        
        tails = get_tails()
        tails -= waiting_nodes
        tails.difference_update( failed_nodes )
        
        if not tails and not waiting_nodes:
          break
        
        completed_nodes, tmp_failed_nodes, rebuild_nodes = build_nodes( self, tails )
        if not (completed_nodes or tmp_failed_nodes or rebuild_nodes):
          break
        
        failed_nodes.update( tmp_failed_nodes )
        
        waiting_nodes |= tails
        
        waitingDiff( completed_nodes )
        waitingDiff( tmp_failed_nodes )
        waitingDiff( rebuild_nodes )
        
        for node in completed_nodes:
          self.__checkAlreadyBuilt( target_nodes, node )
          removeTailNode( node )
      
      return tuple( failed_nodes.items() )
    
  #//-------------------------------------------------------//
  
  def   close( self ):
    self._nodes = _NodesTree()
    self._jobs = 1
  
  #//-------------------------------------------------------//
  
  def   clear( self ):
    clear_nodes = []
    
    get_tails = self._nodes.tails
    
    remove_tail = self._nodes.removeTail
    
    outdated_nodes = set()
    
    with _VFiles() as vfiles:
      while True:
        tails = get_tails()
        tails -= outdated_nodes
        
        if not tails:
          break
        
        for node in tails:
          vfile = vfiles[ node ]
          if node.actual( vfile ):
            remove_tail( node )
            clear_nodes.insert( 0, node )  # add nodes in LIFO order to clear nodes from root to leaf nodes
          else:
            outdated_nodes.add( node )
      
      for node in clear_nodes:
        vfile = vfiles[ node ]
        node.clear( vfile )
  
  #//-------------------------------------------------------//
  
  def   status( self ):
    
    with _VFiles() as vfiles:
      getTails = self._nodes.tails
      
      removeTailNode = self._nodes.removeTail
      
      outdated_nodes = set()
      
      while True:
        tails = getTails() - outdated_nodes
        if not tails:
          break
        
        for node in tails:
          vfile = vfiles[ node ]
          if not node.actual( vfile ):
            eventBuildStatusOutdatedNode( node )
            outdated_nodes.add( node )
          else:
            eventBuildStatusActualNode( node )
            removeTailNode( node )
