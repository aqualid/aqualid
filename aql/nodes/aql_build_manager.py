#
# Copyright (c) 2011-2014 The developers of Aqualid project - http://aqualid.googlecode.com
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
)

import os.path
import threading

from aql.util_types import toSequence, AqlException
from aql.utils import eventStatus, eventWarning, logInfo, logError, logWarning, TaskManager
from aql.values import ValuesFile

#//===========================================================================//

@eventStatus
def   eventNodeStatusOutdated( node, progress, brief ):
  msg = "(%s) OUTDATED: %s" % (progress, node.getBuildStr( brief ))
  logInfo( msg )

#//===========================================================================//

@eventStatus
def   eventNodeStatusActual( node, progress, brief ):
  
  msg = "(%s) ACTUAL: %s" % (progress, node.getBuildStr( brief ))
  logInfo( msg )

#//===========================================================================//

@eventWarning
def   eventBuildTargetTwice( value, node1, brief ):
  logWarning("Target '%s' is built twice. The last time built by: '%s' " %
             ( value.name, node1.getBuildStr( brief )) )

#//===========================================================================//

@eventStatus
def   eventInitialNodes( total_nodes ):
  if total_nodes == 1:
    logInfo("Processing 1 node" )
  else:
    logInfo("Processing %s nodes" % total_nodes )

#//===========================================================================//

@eventStatus
def   eventFailedNode( node, error ):
  
  msg = node.getBuildStr( brief = False )
  msg += '\n\n' + str(error)
  
  logError( msg )

#//===========================================================================//

@eventStatus
def   eventNodeBuilding( node, brief ):
  pass

#//===========================================================================//

@eventStatus
def   eventNodeBuildingActual( node, progress, brief ):
  pass

#//===========================================================================//

@eventStatus
def   eventNodeBuildingFinished( node, builder_output, progress, brief ):
  
  msg = node.getBuildStr( brief )
  if not brief and builder_output:
    msg += '\n'
    msg += builder_output
  
  msg = "(%s) %s" % (progress, msg)
  
  # if __debug__:
  #   msg = '%s: %s' % (node.getName(), msg)
  
  logInfo( msg )

#//===========================================================================//

@eventStatus
def   eventNodeBuildingFailed( node, error ):
  pass

#//===========================================================================//

@eventStatus
def   eventNodeRemoved( node, progress, brief ):
  # msg = node.getClearStr( brief )
  msg = node.getBuildStr( brief )
  if msg:
    # if __debug__:
    #   msg = '%s: %s' % (node.getName(), msg)

    logInfo( "(%s) Removed: %s" % (progress, msg) )

#//===========================================================================//

class   ErrorNodeDependencyCyclic( AqlException ):
  def   __init__( self, node ):
    msg = "Node has a cyclic dependency: %s" % str(node)
    super(ErrorNodeDependencyCyclic, self).__init__( msg )

#//===========================================================================//

class   ErrorNodeUnknown(AqlException):
  def   __init__( self, node ):
    msg = "Unknown node '%s'" % (node, )
    super(ErrorNodeUnknown, self).__init__( msg )

#//===========================================================================//

class   ErrorNodeDependencyUnknown(AqlException):
  def   __init__( self, node, dep_node ):
    msg = "Unable to add dependency to node '%s' from node '%s'" % (node, dep_node)
    super(ErrorNodeDependencyUnknown, self).__init__( msg )

#//===========================================================================//

class   InternalErrorRemoveNonTailNode( AqlException ):
  def   __init__( self, node ):
    msg = "Removing non-tail node: %s" % str(node)
    super(InternalErrorRemoveNonTailNode, self).__init__( msg )

#//===========================================================================//

class   InternalErrorRemoveUnknownTailNode(AqlException):
  def   __init__( self, node ):
    msg = "Remove unknown tail node: : %s" % str(node)
    super(InternalErrorRemoveUnknownTailNode, self).__init__( msg )

#//===========================================================================//

class   BuildStat (object):
  __slots__ = \
    (
      'total',
      'completed',
      'failed',
    )
  
  def   __init__(self, total):
    self.total = total
    self.completed = 0
    self.failed = 0
  
  def   addTotal(self, count ):
    self.total += count
    
  def   incCompleted(self):
    self.completed += 1
    
  def   incFailed(self):
    self.failed += 1
  
  def   getProgressStr(self):
    progress = "%s/%s" % (self.completed + self.failed, self.total )
    return progress

#//===========================================================================//

class _NodesTree (object):
  
  __slots__ = \
  (
    'lock',
    'node2deps',
    'dep2nodes',
    'tail_nodes',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self ):
    self.lock = threading.Lock()
    self.node2deps = {}
    self.dep2nodes = {}
    self.tail_nodes = set()
  
  #//-------------------------------------------------------//
  
  def   __len__(self):
    return len(self.node2deps)
  
  #//-------------------------------------------------------//
  
  def   __hasCycle( self, node, new_deps ):
    
    if node in new_deps:
      return True
    
    deps = set(new_deps)
    node2deps = self.node2deps
    
    while deps:
      dep = deps.pop()
      
      dep_deps = node2deps[dep]
      
      if node in dep_deps:
        return True
      
      deps |= dep_deps
    
    return False
  
  #//-------------------------------------------------------//
  
  def   __depends( self, node, deps ):
    
    node2deps = self.node2deps
    dep2nodes = self.dep2nodes
    
    try:
      current_node_deps = node2deps[ node ]
      
      new_deps = set(deps) - current_node_deps
      
      if not new_deps:
        return
      
      if self.__hasCycle( node, new_deps ):
        raise ErrorNodeDependencyCyclic( node )
      
      self.tail_nodes.discard( node )
      
      #//-------------------------------------------------------//
      
      current_node_deps.update( new_deps )
      
      #//-------------------------------------------------------//
      
      for dep in new_deps:
        dep2nodes[ dep ].add( node )
    
    except KeyError as dep_node:
      raise ErrorNodeDependencyUnknown( node, dep_node.args[0] )
    
  #//-------------------------------------------------------//
  
  def   __add( self, nodes ):
      for node in nodes:
        
        if node not in self.node2deps:
          self.node2deps[ node ] = set()
          self.dep2nodes[ node ] = set()
          self.tail_nodes.add( node )

          node_srcnodes = node.getSourceNodes()
          node_depnodes = node.getDepNodes()

          self.__add( node_srcnodes )       # TODO: recursively add sources and depends
          self.__add( node_depnodes )       # It would be better to rewrite this code to avoid the recursion
          
          self.__depends( node, node_srcnodes )
          self.__depends( node, node_depnodes )
    
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
      node2deps = self.node2deps
      
      try:
        if node2deps[node]:
          raise InternalErrorRemoveNonTailNode( node )
      except KeyError as node:
        raise InternalErrorRemoveUnknownTailNode( node.args[0] )
      
      tail_nodes = self.tail_nodes
      
      del node2deps[node]
      tail_nodes.remove( node )
      
      for dep in self.dep2nodes.pop( node ):
        d = node2deps[ dep ]
        d.remove( node )
        if not d:
          tail_nodes.add( dep )
    
  #//-------------------------------------------------------//
  
  def   tails( self ):
    with self.lock:
      return set( self.tail_nodes )
  
  #//-------------------------------------------------------//
  
  def   __getAllNodes(self, nodes ):
    nodes = set(toSequence(nodes))
    all_nodes = set( nodes )
    
    node2deps = self.node2deps
    while nodes:
      node = nodes.pop()
      
      try:
        deps = node2deps[ node ] - all_nodes
      except KeyError as node:
        raise ErrorNodeUnknown( node.args[0] )
      
      all_nodes.update( deps )
      nodes.update( deps )
    
    return all_nodes
  
  #//-------------------------------------------------------//
  
  def   shrinkTo(self, nodes ):
    
    node2deps = self.node2deps
    dep2nodes = self.dep2nodes
    
    ignore_nodes = set(node2deps) - self.__getAllNodes( nodes )
    
    self.tail_nodes -= ignore_nodes
    
    for node in ignore_nodes:
      del node2deps[ node ]
      del dep2nodes[ node ]
    
    for dep_nodes in dep2nodes.values():
      dep_nodes.difference_update( ignore_nodes ) 
  
  #//-------------------------------------------------------//
  
  def   selfTest( self ):
    with self.lock:
      if set(self.node2deps) != set(self.dep2nodes):
        raise AssertionError("Not all deps are added")
      
      all_dep_nodes = set()
      
      for node in self.dep2nodes:
        if node not in self.node2deps:
          raise AssertionError("Missed node: %s" % str(node) )
        
        node_deps = self.node2deps[node]
        
        if not node_deps:
          if node not in self.tail_nodes:
            raise AssertionError("Missed tail node: %s"  % str(node) )
        else:
          if node in self.tail_nodes:
            raise AssertionError("Invalid tail node: %s"  % str(node) )
        
        all_dep_nodes |= node_deps
        
        for dep in node_deps:
          if node not in self.dep2nodes[dep]:
            raise AssertionError("node not in self.dep2nodes[dep]: dep: %s, node: %s"  % (dep, node) )
      
      if all_dep_nodes - set(self.dep2nodes):
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
  
  def   __iter__(self):
    raise TypeError()
  
  #//-------------------------------------------------------//
  
  def   __getitem__( self, builder ):
    
    builder_name = builder.name
    
    try:
      vfilename = self.names[ builder_name ]
    except KeyError:
      vfilename = os.path.join( builder.getBuildDir(), '.aql.db' )
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

def   _buildNode( node, brief ):
  
  eventNodeBuilding( node, brief )
  
  out = node.build()
  
  if out and isinstance(out, str):
    try:
      out = out.strip()
    except Exception:
      pass
  
  return out

#//===========================================================================//

# noinspection PyAttributeOutsideInit
class _NodesBuilder (object):
  
  __slots__ = \
  (
    'vfiles',
    'build_manager',
    'task_manager',
    'prebuild_nodes',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, build_manager, jobs, keep_going ):
    self.vfiles         = _VFiles()
    self.prebuild_nodes = {}
    self.build_manager  = build_manager
    self.task_manager   = TaskManager( num_threads = jobs, stop_on_fail = not keep_going )
  
  #//-------------------------------------------------------//
  
  def   __enter__(self):
    return self
  
  #//-------------------------------------------------------//
  
  def   __exit__(self, exc_type, exc_value, backtrace):
    self.close()
  
  #//-------------------------------------------------------//
  
  def   build( self, nodes, brief, build_always = False ):
    
    build_manager = self.build_manager
    
    vfiles = self.vfiles
    addTask = self.task_manager.addTask
    
    tasks_check_period = 10
    added_tasks = 0
    changed = False
    
    for node in nodes:
      
      pre_nodes = self.prebuild_nodes.pop( node, None )
      
      if pre_nodes:
        actual = node.prebuildFinished( pre_nodes )
        if actual:
          build_manager.actualNode( node )
          changed = True
          continue
      
      else:
        pre_nodes = node.prebuild()
        if pre_nodes:
          self.prebuild_nodes[ node ] = pre_nodes
          
          build_manager.rebuildNode( node, pre_nodes )
          changed = True
          continue
      
      vfile = vfiles[ node.builder ]
      
      if (not build_always) and node.isActual( vfile ):
        build_manager.actualNode( node )
        changed = True
      else:
        addTask( node, _buildNode, node, brief )
        added_tasks += 1
        
        if added_tasks == tasks_check_period:
          changed = self._getFinishedNodes( block = False ) or changed
          added_tasks = 0
    
    return self._getFinishedNodes( block = not changed ) or changed
  
  #//-------------------------------------------------------//
  
  def   _getFinishedNodes( self, block = True ):
    finished_tasks = self.task_manager.finishedTasks( block = block )
    
    vfiles = self.vfiles
    
    build_manager = self.build_manager
    
    for task in finished_tasks:
      node = task.task_id
      error = task.error
      
      if error is None:
        vfile = vfiles[ node.builder ]
        node.save( vfile )
        build_manager.completedNode( node, task.result )
      else:
        build_manager.failedNode( node, error )
    
    return bool(finished_tasks)
  
  #//-------------------------------------------------------//
  
  def   clear( self, nodes ):
    
    vfiles = self.vfiles
    build_manager = self.build_manager
    
    for node in nodes:
      
      pre_nodes = self.prebuild_nodes.pop( node, None )
      if pre_nodes:
        actual = node.prebuildFinished( pre_nodes )
        if actual:
          build_manager.removedNode( node, silent = True )
          continue
        
      else:
        pre_nodes = node.prebuild()
        if pre_nodes:
          self.prebuild_nodes[ node ] = pre_nodes
          
          build_manager.rebuildNode( node, pre_nodes )
          continue
      
      vfile = vfiles[ node.builder ]
      node.clear( vfile )
      build_manager.removedNode( node )
  
  #//-------------------------------------------------------//
  
  def   status( self, nodes ):
    
    vfiles = self.vfiles
    build_manager = self.build_manager
    
    for node in nodes:
      pre_nodes = self.prebuild_nodes.pop( node, None )
      if pre_nodes:
        actual = node.prebuildFinished( pre_nodes )
        if actual:
          build_manager.actualNodeStatus( node )
          continue
      
      else:
        pre_nodes = node.prebuild()
        if pre_nodes:
          self.prebuild_nodes[ node ] = pre_nodes
          
          build_manager.rebuildNode( node, pre_nodes )
          continue
      
      vfile = vfiles[ node.builder ]
      if node.isActual( vfile ):
        build_manager.actualNodeStatus( node )
      else:
        build_manager.outdatedNodeStatus( node )
  
  #//-------------------------------------------------------//
  
  def   close( self ):
    self.task_manager.stop()
    self._getFinishedNodes( block = False )
    self.vfiles.close()

#//===========================================================================//

class BuildManager (object):
  
  __slots__ = \
  (
    '_nodes',
    '_built_targets',
    '_waiting_nodes',
    '_failed_nodes',
    'brief',
    'completed',
    'actual',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__(self):
    self._nodes = _NodesTree()
    self.__reset()
  
  #//-------------------------------------------------------//
  
  def   __reset(self, brief =  True ):
    
    self._built_targets = {}
    self._waiting_nodes = set()
    self._failed_nodes = {}
    
    self.brief = brief
    self.completed = 0
    self.actual = 0
  
  #//-------------------------------------------------------//
  
  def   add( self, nodes ):
    self._nodes.add( nodes )
  
  #//-------------------------------------------------------//
  
  def   depends( self, node, deps ):
    self._nodes.depends( node, deps )
  
  #//-------------------------------------------------------//
  
  def   __len__(self):
    return len(self._nodes)
  
  #//-------------------------------------------------------//
  
  def   selfTest( self ):
    self._nodes.selfTest()
  
  #//-------------------------------------------------------//
  
  def   getTailNodes(self):
    
    wait_nodes = self._waiting_nodes
    
    tails = self._nodes.tails()
    tails -= wait_nodes
    tails.difference_update( self._failed_nodes )
    
    wait_nodes.update( tails )
    
    return tails
  
  #//-------------------------------------------------------//
  
  def   isWaiting(self):
    return bool(self._waiting_nodes)
  
  #//-------------------------------------------------------//
  
  def   completedNode( self, node, builder_output ):
    self._checkAlreadyBuilt( node )
    self._nodes.removeTail( node )
    self._waiting_nodes.remove( node )
    self.completed += 1
    
    eventNodeBuildingFinished( node, builder_output, self.getProgressStr(), self.brief )
    
    node.shrink()
  
  #//-------------------------------------------------------//
  
  def   removedNode( self, node, silent = False ):
    self._nodes.removeTail( node )
    self._waiting_nodes.remove( node )
    self.completed += 1
    
    if not silent:
      eventNodeRemoved( node, self.getProgressStr(), self.brief )
    
    node.shrink()
  
  #//-------------------------------------------------------//
  
  def   actualNode( self, node ):
    self._checkAlreadyBuilt( node )
    self._nodes.removeTail( node )
    self._waiting_nodes.remove( node )
    self.actual += 1
    
    eventNodeBuildingActual( node, self.getProgressStr(), self.brief )
    
    node.shrink()
  
  #//-------------------------------------------------------//
  
  def   actualNodeStatus( self, node ):
    self._nodes.removeTail( node )
    self.actual += 1
    self._waiting_nodes.remove( node )
    
    eventNodeStatusActual( node, self.getProgressStr(), self.brief )
    
    node.shrink()
  
  #//-------------------------------------------------------//
  
  def   outdatedNodeStatus( self, node ):
    self._waiting_nodes.remove( node )
    self._failed_nodes[ node ] = None
    
    eventNodeStatusOutdated( node, self.getProgressStr(), self.brief )
    node.shrink()
  
  #//-------------------------------------------------------//
  
  def   failedNode( self, node, error ):
    self._waiting_nodes.remove( node )
    self._failed_nodes[ node ] = error
    
    eventNodeBuildingFailed( node, self.brief )
  
  #//-------------------------------------------------------//
  
  def   rebuildNode( self, node, pre_nodes ):
    self.depends( node, pre_nodes )
    self._waiting_nodes.remove( node )
  
  #//-------------------------------------------------------//
  
  def   getProgressStr(self):
    done = self.completed + self.actual
    total = len(self._nodes) + done
    
    processed = done + len(self._failed_nodes)
    
    progress = "%s/%s" % (processed, total)
    return progress
    
  #//-------------------------------------------------------//
  
  def   close( self ):
    self._nodes = _NodesTree()
  
  #//-------------------------------------------------------//
  
  def   _checkAlreadyBuilt( self, node ):
    values = []
    values += node.getTargetValues()
    values += node.getSideEffectValues()
    
    built_targets = self._built_targets
    
    for value in values:
      value_sign = value.signature
      other_value_sign = built_targets.setdefault( value.valueId(), value_sign )
      
      if other_value_sign != value_sign:
        eventBuildTargetTwice( value, node, brief = self.brief )
  
  #//-------------------------------------------------------//
  
  def   build( self, jobs, keep_going, nodes = None, brief = True, build_always = False ):
    
    self.__reset( brief )
    
    nodes_tree = self._nodes
    if nodes is not None:
      nodes_tree.shrinkTo( nodes )
    
    with _NodesBuilder( self, jobs, keep_going ) as nodes_builder:
      
      eventInitialNodes( len(nodes_tree) )
      
      while True:
        tails = self.getTailNodes()
        
        if not (tails or self.isWaiting()):
          break
        
        changed = nodes_builder.build( tails, brief, build_always )
        
        if not changed:
          break
    
    return self.isOk()
  
  #//-------------------------------------------------------//
  
  def   isOk(self):
    return not bool( self._failed_nodes )
  
  #//-------------------------------------------------------//
  
  def   printFails(self ):
    for node, error in self._failed_nodes.items():
      eventFailedNode( node, error )
  
  #//-------------------------------------------------------//
  
  def   printBuildState(self):
    logInfo("Wating nodes: %s" % len(self._waiting_nodes) )
    logInfo("Failed nodes: %s" % len(self._failed_nodes) )
    logInfo("Completed nodes: %s" % self.completed )
    logInfo("Actual nodes: %s" % self.actual )
  
  #//-------------------------------------------------------//
  
  def   printStatusState(self):
    logInfo("Outdated nodes: %s" % len(self._failed_nodes) )
    logInfo("Actual nodes: %s" % self.actual )
  
  #//-------------------------------------------------------//
  
  def   clear( self, nodes = None, brief = True ):
    
    self.__reset( brief )
    
    nodes_tree = self._nodes
    if nodes is not None:
      nodes_tree.shrinkTo( nodes )
    
    with _NodesBuilder( self, jobs = 1, keep_going = False ) as nodes_builder:
      while True:
        
        tails = self.getTailNodes()
        
        if not tails:
          break
        
        nodes_builder.clear( tails )
  
  #//-------------------------------------------------------//
  
  def   status( self, nodes = None, brief = True ):
    
    self.__reset( brief )
    
    nodes_tree = self._nodes
    if nodes is not None:
      nodes_tree.shrinkTo( nodes )
    
    with _NodesBuilder( self, jobs = 1, keep_going = False ) as nodes_builder:
      
      while True:
        tails = self.getTailNodes()
        
        if not tails:
          break
        
        nodes_builder.status( tails )
    
    return self.isOk()
