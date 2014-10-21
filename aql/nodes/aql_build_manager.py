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

from aql.util_types import toSequence, AqlException
from aql.utils import eventStatus, eventWarning, eventError, logInfo, logError, logWarning, TaskManager
from aql.values import ValuesFile

#//===========================================================================//

@eventStatus
def   eventNodeActual( settings, node, progress ):
  msg = "(%s) ACTUAL: %s" % (progress, node.getBuildStr( settings.brief ))
  logInfo( msg )

#//===========================================================================//

@eventStatus
def   eventNodeOutdated( settings, node, progress ):
  msg = "(%s) OUTDATED: %s" % (progress, node.getBuildStr( settings.brief ))
  logInfo( msg )

#//===========================================================================//

@eventWarning
def   eventBuildTargetTwice( settings, value, node1 ):
  logWarning("Target '%s' is built twice. The last time built by: '%s' " %
             ( value.name, node1.getBuildStr( settings.brief )) )

#//===========================================================================//

@eventError
def   eventFailedNode( settings, node, error ):
  
  msg = node.getBuildStr( settings )
  msg += '\n\n%s\n' % (error,)
  
  logError( msg )

#//===========================================================================//

@eventStatus
def   eventNodeBuilding( settings, node ):
  pass

#//===========================================================================//

@eventStatus
def   eventNodeBuildingFinished( settings, node, builder_output, progress ):
  
  msg = node.getBuildStr( settings.brief )
  if settings.with_output and builder_output:
    msg += '\n'
    if builder_output:
      msg += builder_output
      msg += '\n'
  
  msg = "(%s) %s" % (progress, msg)
  
  logInfo( msg )

#//===========================================================================//

@eventStatus
def   eventNodeBuildingFailed( settings, node, error ):
  pass

#//===========================================================================//

@eventStatus
def   eventNodeRemoved( settings, node, progress ):
  msg = node.getBuildStr( settings.brief )
  if msg:
    logInfo( "(%s) Removed: %s" % (progress, msg) )

#//===========================================================================//

class   ErrorNodeDependencyCyclic( AqlException ):
  def   __init__( self, node, deps ):
    msg = "Node '%s' (%s) has a cyclic dependency: %s" % (node, node.getBuildStr(True), deps )
    super(ErrorNodeDependencyCyclic, self).__init__( msg )

#//===========================================================================//

class   ErrorNodeUnknown(AqlException):
  def   __init__( self, node ):
    msg = "Unknown node '%s'" % (node, )
    super(ErrorNodeUnknown, self).__init__( msg )

#//===========================================================================//

class   ErrorNodeSignatureDifferent(AqlException):
  def   __init__( self, node ):
    msg = "Two similar nodes have different signatures (sources, builder parameters or dependencies): %s" % (node.getBuildStr( brief = False ), )
    super(ErrorNodeSignatureDifferent, self).__init__( msg )

#//===========================================================================//

class   ErrorNodeDependencyUnknown(AqlException):
  def   __init__( self, node, dep_node ):
    msg = "Unable to add dependency to node '%s' from node '%s'" % (node, dep_node)
    super(ErrorNodeDependencyUnknown, self).__init__( msg )

#//===========================================================================//

class   InternalErrorRemoveNonTailNode( AqlException ):
  def   __init__( self, node ):
    msg = "Removing non-tail node: %s" % (node,)
    super(InternalErrorRemoveNonTailNode, self).__init__( msg )

#//===========================================================================//

class   InternalErrorRemoveUnknownTailNode(AqlException):
  def   __init__( self, node ):
    msg = "Remove unknown tail node: : %s" % (node,)
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
    'node2deps',
    'dep2nodes',
    'tail_nodes',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self ):
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
      
      deps = { dep for dep in deps if not dep.isBuilt() }
      new_deps = deps - current_node_deps
      
      if not new_deps:
        return
      
      if self.__hasCycle( node, new_deps ):
        raise ErrorNodeDependencyCyclic( node, new_deps )
      
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
    self.__add( toSequence( nodes ) )
    
  #//-------------------------------------------------------//
  
  def   depends( self, node, deps ):
    deps = toSequence( deps )
    
    self.__add( deps )
    self.__depends( node, deps )
  
  #//-------------------------------------------------------//
  
  def   removeTail( self, node ):
    node2deps = self.node2deps
    
    try:
      deps = node2deps.pop(node)
      if deps:
        raise InternalErrorRemoveNonTailNode( node )
    except KeyError as node:
      raise InternalErrorRemoveUnknownTailNode( node.args[0] )
    
    tail_nodes = self.tail_nodes
    
    # tail_nodes.remove( node )
    
    for dep in self.dep2nodes.pop( node ):
      d = node2deps[ dep ]
      d.remove( node )
      if not d:
        tail_nodes.add( dep )
    
  #//-------------------------------------------------------//
  
  def   popTails( self ):
    tails = self.tail_nodes
    self.tail_nodes = set()
    return tails
  
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
    if set(self.node2deps) != set(self.dep2nodes):
      raise AssertionError("Not all deps are added")
    
    all_dep_nodes = set()
    
    for node in self.dep2nodes:
      if node not in self.node2deps:
        raise AssertionError("Missed node: %s" % (node,) )
      
      node_deps = self.node2deps[node]
      
      if not node_deps:
        if node not in self.tail_nodes:
          raise AssertionError("Missed tail node: %s, tail_nodes: %s"  % (node, self.tail_nodes) )
      else:
        if node in self.tail_nodes:
          raise AssertionError("Invalid tail node: %s"  % (node,) )
      
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

def   _buildNode( node ):
  
  eventNodeBuilding( node )
  
  out = node.build()
  
  if out:
    try:
      out = out.strip()
    except Exception:
      pass
  
  return out

#//===========================================================================//

class   _NodeState( object ):
  __slots__ = \
  (
    'initialized',
    'check_depends',
    'check_replace',
    'check_split',
    'check_actual',
    'split_nodes',
  )
  
  def   __init__(self ):
    self.initialized = False
    self.check_depends = True
    self.check_replace = True
    self.check_split = True
    self.check_actual = True
    self.split_nodes = None
  
  def   __str__(self):
    return "initialized: %s, check_depends: %s, check_replace: %s, check_split: %s, check_actual: %s, split_nodes: %s" %\
      (self.initialized, self.check_depends, self.check_replace, self.check_split, self.check_actual, self.split_nodes )
  
#//===========================================================================//

# noinspection PyAttributeOutsideInit
class _NodesBuilder (object):
  
  __slots__ = \
  (
    'vfiles',
    'build_manager',
    'task_manager',
    'node_states',
    'building_nodes',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, build_manager, jobs, keep_going ):
    self.vfiles         = _VFiles()
    self.node_states    = {}
    self.building_nodes = {}
    self.build_manager  = build_manager
    self.task_manager   = TaskManager( num_threads = jobs, stop_on_fail = not keep_going )
  
  #//-------------------------------------------------------//
  
  def   __enter__(self):
    return self
  
  #//-------------------------------------------------------//
  
  def   __exit__(self, exc_type, exc_value, backtrace):
    self.close()
  
  #//-------------------------------------------------------//
  
  def   _getNodeState( self, node ):
    try:
      state = self.node_states[ node ]
    except KeyError:
      state = _NodeState()
      self.node_states[ node ] = state
    
    return state
  
  #//-------------------------------------------------------//
  
  def   _removeNodeState( self, node ):
    try:
      del self.node_states[ node ]
    except KeyError:
      pass
  
  #//-------------------------------------------------------//
  
  def   _addBuildingNode( self, node, state ):
    conflicting_nodes = []
    building_nodes = self.building_nodes
    
    for name, signature in node.getNamesAndSignatures():
      node_signature = (node, signature)
      
      other_node, other_signature = building_nodes.setdefault( name, node_signature )
      if other_node is not node:
        if other_signature != signature:
          raise ErrorNodeSignatureDifferent( node )
        
        conflicting_nodes.append( other_node )
    
    if conflicting_nodes:
      state.check_actual = True
      self.build_manager.depends( node, conflicting_nodes )
      return True
    
    return False
  
  #//-------------------------------------------------------//
  
  def   _removeBuildingNode( self, node ):
    building_nodes = self.building_nodes
    for name in node.getNames():
      del building_nodes[ name ]
  
  #//-------------------------------------------------------//
  
  def   isBuilding(self):
    return bool(self.building_nodes)
  
  #//-------------------------------------------------------//
  
  def   _checkPrebuildDepends( self, node ):
    dep_nodes = node.buildDepends()
    if dep_nodes:
      self.build_manager.depends( node, dep_nodes )
      return True
    
    return False
  
  #//-------------------------------------------------------//
  
  def _checkPrebuildReplace( self, node ):
    
    if node.buildReplace():
      new_node_sources = node.getSourceNodes()
      if new_node_sources:
        self.build_manager.depends( node, new_node_sources )
        return True
    
    return False
  
  #//-------------------------------------------------------//
  
  def   _checkPrebuildSplit( self, node, state ):
    
    build_manager = self.build_manager
    
    if state.check_split:
      state.check_split = False
      
      check_actual = True
      
      if node.isBatch() and state.check_actual:
        # Check for changed sources of BatchNode
        vfile = self.vfiles[ node.builder ]
        actual = build_manager.isActualNode( node, vfile )
        
        if actual:
          self._removeNodeState( node )
          build_manager.actualNode( node )
          return True
        
        check_actual = False
      
      split_nodes = node.buildSplit()
      if split_nodes:
        state.split_nodes = split_nodes
        for split_node in split_nodes:
          split_state = self._getNodeState( split_node )
          split_state.check_split = False
          split_state.check_depends = False
          split_state.check_replace = False
          split_state.check_actual = check_actual
          split_state.initialized = split_node.builder is node.builder
        
        self.build_manager.depends( node, split_nodes )
        return True
  
    elif state.split_nodes is not None:
      if node.isBatch():
        node._populateTargets()
      else:
        targets = []
        for split_node in state.split_nodes:
          targets += split_node.getTargetValues()
        
        node.target_values = targets
        
      self._removeNodeState( node )
      
      self.build_manager.completedSplitNode( node )
      
      return True
    
    return False
  
  #//-------------------------------------------------------//
  
  def   _prebuild( self, node, state ):
    
    # print( "node: %s, state: %s" % (node, state))
    
    if not state.initialized:
      node.initiate()
      state.initialized = True
    
    if state.check_depends:
      state.check_depends = False
      if self._checkPrebuildDepends( node ):
        return True
    
    if state.check_replace:
      state.check_replace = False
      if self._checkPrebuildReplace( node ):
        return True
    
    if self._checkPrebuildSplit( node, state ):
      return True
    
    return False
    
  #//-------------------------------------------------------//
  
  def   build( self, nodes ):
    
    build_manager = self.build_manager
    
    vfiles = self.vfiles
    addTask = self.task_manager.addTask
    
    tasks_check_period = 10
    added_tasks = 0
    changed = False
    
    for node in nodes:
      
      node_state = self._getNodeState( node )
      
      if self._prebuild( node, node_state ):
        changed = True
        continue
      
      if self._addBuildingNode( node, node_state ):
        continue
      
      if node_state.check_actual:
        vfile = vfiles[ node.builder ]
        actual = build_manager.isActualNode( node, vfile )
        
        if actual:
          self._removeNodeState( node )
          self._removeBuildingNode( node )
          build_manager.actualNode( node )
          changed = True
          continue
          
      addTask( node, _buildNode, node )
      
      added_tasks += 1
      
      if added_tasks == tasks_check_period:
        changed = self._getFinishedNodes( block = False ) or changed
        added_tasks = 0
    
    self._getFinishedNodes( block = not changed )
  
  #//-------------------------------------------------------//
  
  def   _getFinishedNodes( self, block = True ):
    # print("tasks: %s, finished_tasks: %s" % (self.task_manager.unfinished_tasks, self.task_manager.finished_tasks.qsize()))
    finished_tasks = self.task_manager.finishedTasks( block = block )
    
    vfiles = self.vfiles
    
    build_manager = self.build_manager
    
    for task in finished_tasks:
      node = task.task_id
      error = task.error
      
      self._removeNodeState( node )
      self._removeBuildingNode( node )
      
      vfile = vfiles[ node.builder ]
      
      if error is None:
        node.save( vfile )
        build_manager.completedNode( node, task.result )
      else:
        if node.isBatch():
          node.save( vfile )
        
        build_manager.failedNode( node, error )

    return bool(finished_tasks)
  
  #//-------------------------------------------------------//
  
  def   clear( self, nodes ):
    
    vfiles = self.vfiles
    build_manager = self.build_manager
    
    for node in nodes:
      
      node_state = self._getNodeState( node )
      
      node_state.check_actual = False
      
      if self._prebuild( node, node_state ):
        continue
      
      vfile = vfiles[ node.builder ]
      node.clear( vfile )
      build_manager.removedNode( node )
  
  #//-------------------------------------------------------//
  
  def   status( self, nodes ):
    
    vfiles = self.vfiles
    build_manager = self.build_manager
    
    for node in nodes:
      
      node_state = self._getNodeState( node )
      node_state.check_actual = False
      
      if self._prebuild( node, node_state ):
        continue
      
      vfile = vfiles[ node.builder ]
      if build_manager.isActualNode( node, vfile ):
        build_manager.actualNodeStatus( node )
      else:
        build_manager.outdatedNodeStatus( node )
  
  #//-------------------------------------------------------//
  
  def   close( self ):
    try:
      self.task_manager.stop()
      self._getFinishedNodes( block = False )
    finally:
      self.vfiles.close()

#//===========================================================================//

class BuildManager (object):
  
  __slots__ = \
  (
    '_nodes',
    '_built_targets',
    '_failed_nodes',
    '_built_node_names',
    'completed',
    'actual',
    'explain',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__(self):
    self._nodes = _NodesTree()
    self.__reset()
  
  #//-------------------------------------------------------//
  
  def   __reset(self, build_always = False, explain = False ):
    
    self._built_targets = {}
    self._failed_nodes = {}
    self._built_node_names = set() if build_always else None
    
    self.completed = 0
    self.actual = 0
    self.explain = explain
  
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
    return self._nodes.popTails()
  
  #//-------------------------------------------------------//
  
  def   actualNodeStatus( self, node ):
    eventNodeActual( node, self.getProgressStr() )
    self.actualNode( node )
  
  #//-------------------------------------------------------//
  
  def   outdatedNodeStatus( self, node ):
    self._failed_nodes[ node ] = None
    
    eventNodeOutdated( node, self.getProgressStr() )
    node.shrink()
  
  #//-------------------------------------------------------//
  
  def   isActualNode( self, node, vfile ):
    return node.checkActual( vfile, self._built_node_names, self.explain )
  
  #//-------------------------------------------------------//
  
  def   _addToBuiltNodeNames(self, node ):
    built_names = self._built_node_names
    if built_names is not None:
      built_names.update( node.getNames() )
  
  #//-------------------------------------------------------//
  
  def   completedSplitNode(self, node ):
    self._nodes.removeTail( node )
    node.shrink()
  
  #//-------------------------------------------------------//
  
  def   actualNode( self, node ):
    self._nodes.removeTail( node )
    self.actual += 1
    
    node.shrink()
  
  #//-------------------------------------------------------//
  
  def   completedNode( self, node, builder_output ):
    self._checkAlreadyBuilt( node )
    self._nodes.removeTail( node )
    self._addToBuiltNodeNames( node )
    
    self.completed += 1
    
    eventNodeBuildingFinished( node, builder_output, self.getProgressStr() )
    
    node.shrink()
  
  #//-------------------------------------------------------//
  
  def   failedNode( self, node, error ):
    self._failed_nodes[ node ] = error
    
    eventNodeBuildingFailed( node, error )
  
  #//-------------------------------------------------------//
  
  def   removedNode( self, node ):
    self._nodes.removeTail( node )
    self.completed += 1
    
    eventNodeRemoved( node, self.getProgressStr() )
    
    node.shrink()
  
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
    values = node.getTargetValues()
    
    built_targets = self._built_targets
    
    for value in values:
      value_sign = value.signature
      other_value_sign = built_targets.setdefault( value.valueId(), value_sign )
      
      if other_value_sign != value_sign:
        eventBuildTargetTwice( value, node )
  
  #//-------------------------------------------------------//
  
  def   build( self, jobs, keep_going, nodes = None, build_always = False, explain = False ):
    
    self.__reset( build_always = build_always, explain = explain )
    
    nodes_tree = self._nodes
    if nodes is not None:
      nodes_tree.shrinkTo( nodes )
    
    with _NodesBuilder( self, jobs, keep_going ) as nodes_builder:
      while True:
        tails = self.getTailNodes()
        
        if not tails and not nodes_builder.isBuilding():
          break
        
        nodes_builder.build( tails )
    
    return self.isOk()
  
  #//-------------------------------------------------------//
  
  def   isOk(self):
    return not bool( self._failed_nodes )
  
  #//-------------------------------------------------------//
  
  def   failsCount(self):
    return len( self._failed_nodes )
  
  #//-------------------------------------------------------//
  
  def   printFails(self ):
    for node, error in self._failed_nodes.items():
      eventFailedNode( node, error )
  
  #//-------------------------------------------------------//
  
  def   printBuildState(self):
    logInfo("Failed nodes: %s" % len(self._failed_nodes) )
    logInfo("Completed nodes: %s" % self.completed )
    logInfo("Actual nodes: %s" % self.actual )
  
  #//-------------------------------------------------------//
  
  def   printStatusState(self):
    logInfo("Outdated nodes: %s" % len(self._failed_nodes) )
    logInfo("Actual nodes: %s" % self.actual )
  
  #//-------------------------------------------------------//
  
  def   clear( self, nodes = None ):
    
    self.__reset()
    
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
  
  def   status( self, nodes = None, explain = False ):
    
    self.__reset( explain = explain )
    
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
