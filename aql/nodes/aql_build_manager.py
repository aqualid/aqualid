#
# Copyright (c) 2011-2014 The developers of Aqualid project
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
import itertools

from aql.utils import eventStatus, eventWarning, eventError, logInfo, logError, logWarning, TaskManager
from aql.entity import EntitiesFile

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
def   eventBuildTargetTwice( settings, entity, node1 ):
  logWarning("Target '%s' is built twice. The last time built by: '%s' " %
             ( entity.name, node1.getBuildStr( settings.brief )) )

#//===========================================================================//

@eventError
def   eventFailedNode( settings, node, error ):
  
  msg = node.getBuildStr( settings.brief )
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

class   ErrorNodeDependencyCyclic( Exception ):
  def   __init__( self, node, deps ):
    msg = "Node '%s' (%s) has a cyclic dependency: %s" % (node, node.getBuildStr(True), deps )
    super(ErrorNodeDependencyCyclic, self).__init__( msg )

#//===========================================================================//

class   ErrorNodeUnknown(Exception):
  def   __init__( self, node ):
    msg = "Unknown node '%s'" % (node, )
    super(ErrorNodeUnknown, self).__init__( msg )

#//===========================================================================//

class   ErrorNodeSignatureDifferent(Exception):
  def   __init__( self, node ):
    msg = "Two similar nodes have different signatures (sources, builder parameters or dependencies): %s" % (node.getBuildStr( brief = False ), )
    super(ErrorNodeSignatureDifferent, self).__init__( msg )

#//===========================================================================//

class   ErrorNodeDependencyUnknown(Exception):
  def   __init__( self, node, dep_node ):
    msg = "Unable to add dependency to node '%s' from node '%s'" % (node, dep_node)
    super(ErrorNodeDependencyUnknown, self).__init__( msg )

#//===========================================================================//

class   InternalErrorRemoveNonTailNode( Exception ):
  def   __init__( self, node ):
    msg = "Removing non-tail node: %s" % (node,)
    super(InternalErrorRemoveNonTailNode, self).__init__( msg )

#//===========================================================================//

class   InternalErrorRemoveUnknownTailNode(Exception):
  def   __init__( self, node ):
    msg = "Remove unknown tail node: : %s" % (node,)
    super(InternalErrorRemoveUnknownTailNode, self).__init__( msg )

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
  
  def   getNodes(self):
    return frozenset( self.node2deps )
  
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
  
  def   _depends( self, node, deps ):
    
    node2deps = self.node2deps
    dep2nodes = self.dep2nodes
    
    try:
      current_node_deps = node2deps[ node ]
      
      deps = set( dep for dep in deps if not dep.isBuilt() )
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
  
  def   add( self, nodes ):
      for node in nodes:
        if node not in self.node2deps:
          self.node2deps[ node ] = set()
          self.dep2nodes[ node ] = set()
          self.tail_nodes.add( node )

          node_srcnodes = node.getSourceNodes()
          node_depnodes = node.getDepNodes()

          self.add( node_srcnodes )       # recursively add sources and depends
          self.add( node_depnodes )       # TODO: It would be better to rewrite this code to avoid the recursion
          
          self._depends( node, node_srcnodes )
          self._depends( node, node_depnodes )
            
  #//-------------------------------------------------------//
  
  def   depends( self, node, deps ):
    self.add( deps )
    self._depends( node, deps )
  
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
    
    for dep in self.dep2nodes.pop( node ):
      d = node2deps[ dep ]
      d.remove( node )
      if not d:
        tail_nodes.add( dep )
    
  #//-------------------------------------------------------//
  
  def   filterUnknownDeps(self, deps ):
    return [ dep for dep in deps if dep in self.node2deps ]
  
  #//-------------------------------------------------------//
  
  def   popTails( self ):
    tails = self.tail_nodes
    self.tail_nodes = set()
    return tails
  
  #//-------------------------------------------------------//
  
  def   __getAllNodes(self, nodes ):
    nodes = set(nodes)
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
      
      if node_deps:
        if node in self.tail_nodes:
          raise AssertionError("Invalid tail node: %s"  % (node,) )
      # if not node_deps:
      #   if node not in self.tail_nodes:
      #     raise AssertionError("Missed tail node: %s, tail_nodes: %s"  % (node, self.tail_nodes) )
      # else:
      #   if node in self.tail_nodes:
      #     raise AssertionError("Invalid tail node: %s"  % (node,) )
      
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
    'force_lock'
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, force_lock = False ):
    self.handles = {}
    self.names = {}
    self.force_lock = force_lock
  
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
      vfile = EntitiesFile( vfilename, force = self.force_lock )
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

def   _getModuleNodes( node, module_cache, node_cache ):
  try:
    return module_cache[ node ]
  except KeyError:
    pass
  
  result = set( (node,) )
  
  try:
    src_nodes = node_cache[ node ]
  except KeyError:
    node_cache[ node ] = src_nodes = frozenset(node.getSourceNodes())

  for src in src_nodes:
    result.update( _getModuleNodes( src, module_cache, node_cache ) )
  
  module_cache[ node ] = result
  return result

#//===========================================================================//

def   _getLeafNodes( nodes, exclude_nodes, node_cache ):
  leafs = set()
  for node in nodes:
    if node_cache[node].issubset( exclude_nodes ):
      leafs.add( node )
  
  return leafs
  
#//===========================================================================//

class _NodeLocker( object ):
  __slots__ = (
    'node2deps',
    'dep2nodes',
    'locked_nodes',
    'unlocked_nodes',
  )
  
  def   __init__( self ):
    self.node2deps = {}
    self.dep2nodes = {}
    self.locked_nodes = {}
    self.unlocked_nodes = []
  
  #//-------------------------------------------------------//
  
  def   syncModules( self, nodes, module_cache = None, node_cache = None ):
    
    if module_cache is None:
      module_cache = {}
    
    if node_cache is None:
      node_cache = {}
    
    for node1, node2 in itertools.product( nodes, nodes ):
      if node1 is not node2:
        self.__addModules( node1, node2, module_cache, node_cache )
    
  #//-------------------------------------------------------//
  
  def   __addModules( self, node1, node2, module_cache, node_cache ):
    
    node1_sources = _getModuleNodes( node1, module_cache, node_cache )
    node2_sources = _getModuleNodes( node2, module_cache, node_cache )
    
    common = node1_sources & node2_sources
    node1_sources -= common
    node2_sources -= common
    
    leafs1 = _getLeafNodes( node1_sources, common, node_cache )
    leafs2 = _getLeafNodes( node2_sources, common, node_cache )
    
    for leaf in leafs1:
      self.__add( leaf, node2_sources )
    
    for leaf in leafs2:
      self.__add( leaf, node1_sources )
  
  #//-------------------------------------------------------//
  
  def   sync( self, nodes ):
    for node in nodes:
      node_deps = self.__add( node, nodes )
      node_deps.remove( node )
  
  #//-------------------------------------------------------//
  
  def __add( self, node, deps ):
    try:
      node_set = self.node2deps[ node ]
    except KeyError:
      node_set = set()
      self.node2deps[ node ] = node_set
    
    node_set.update( deps )
    
    for dep in deps:
      if dep is not node:
        try:
          dep_set = self.dep2nodes[ dep ]
        except KeyError:
          dep_set = set()
          self.dep2nodes[ dep ] = dep_set
        
        dep_set.add( node )
    
    return node_set
  
  #//-------------------------------------------------------//
  
  def   lock( self, node, building_nodes ):
    
    deps = self.node2deps.get( node, None )
    if not deps:
      # node doesn't have to be synchronized
      return True
    
    for dep in deps:
      if dep in building_nodes:
        try:
          self.locked_nodes[dep].add( node )
        except KeyError:
          self.locked_nodes[dep] = set( (node,) )
        
        return False
    
    return True
  
  #//-------------------------------------------------------//
  
  def   unlock( self, node ):
    
    for dep in self.node2deps.pop( node, tuple() ):
      self.dep2nodes[ dep ].remove( node )
      
    for dep in self.dep2nodes.pop( node, tuple() ):
      self.node2deps[ dep ].remove( node )
    
    unlocked_nodes = self.locked_nodes.pop(node, None)
    if not unlocked_nodes:
      return 
    
    self.unlocked_nodes.extend( unlocked_nodes )
  
  #//-------------------------------------------------------//
  
  def   popUnlocked(self):
    unlocked_nodes = self.unlocked_nodes
    self.unlocked_nodes = []
    
    return unlocked_nodes

  #//-------------------------------------------------------//
  
  def   selfTest( self ):
    for node, deps in self.node2deps.items():
      if node in deps:
        raise AssertionError("Node depends from itself: %s"  % (node,) )
      
      for dep in deps:
        if node not in self.dep2nodes[ dep ]:
          raise AssertionError("Dependency '%s' doesn't have node '%s'"  % (dep, node,) )
    
    for node, deps in self.locked_nodes.items():
      for dep in deps:
        if node not in self.node2deps[dep]:
          raise AssertionError("Locked node %s does't actually depend from node %s"  % (dep, node) )
        
        if dep in self.unlocked_nodes:
          raise AssertionError("Locked node %s is actually locked"  % (dep,) )
    
    for node in self.unlocked_nodes:
      if node not in self.node2deps:
        raise AssertionError("Unknown unlocked node %s"  % (node,) )


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
  
  def   __init__( self, build_manager, jobs = 0, keep_going = False, with_backtrace = True, force_lock = False ):
    self.vfiles         = _VFiles( force_lock = force_lock )
    self.node_states    = {}
    self.building_nodes = {}
    self.build_manager  = build_manager
    self.task_manager   = TaskManager( num_threads = jobs, stop_on_fail = not keep_going, with_backtrace = with_backtrace )
  
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
    
    node_names = {}
    
    for name, signature in node.getNamesAndSignatures():
      other = building_nodes.get( name, None )
      if other is None:
        node_names[ name ] = (node, signature)
        continue
      
      other_node, other_signature = other
      if other_signature != signature:
        raise ErrorNodeSignatureDifferent( node )
        
      conflicting_nodes.append( other_node )
    
    if conflicting_nodes:
      state.check_actual = True
      self.build_manager.depends( node, conflicting_nodes )
      return False
    
    building_nodes.update( node_names )
    return True
  
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
          targets += split_node.getTargetEntities()
        
        node.target_entities = targets
        
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
  
  def   build( self, nodes, node_locker ):
    
    build_manager = self.build_manager
    
    vfiles = self.vfiles
    addTask = self.task_manager.addTask
    
    tasks_check_period = 10
    added_tasks = 0
    changed = False
    
    for node in nodes:
      if (node_locker is not None) and (not node_locker.lock( node, self.node_states )):
        continue
      
      node_state = self._getNodeState( node )
      
      if self._prebuild( node, node_state ):
        changed = True
        continue
      
      if not self._addBuildingNode( node, node_state ):
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
    
    return self._getFinishedNodes( block = not changed )
  
  #//-------------------------------------------------------//
  
  def   _getFinishedNodes( self, block = True ):
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
    
    # return false when there are no more task processing threads
    return finished_tasks or not block
  
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
  
  __slots__ = (
    '_nodes',
    '_built_targets',
    '_failed_nodes',
    '_built_node_names',
    '_node_locker',
    '_module_cache',
    '_node_cache',
    'completed',
    'actual',
    'explain',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__(self):
    self._nodes = _NodesTree()
    self._node_locker = None
    self.__reset()
  
  #//-------------------------------------------------------//
  
  def   __reset(self, build_always = False, explain = False ):
    
    self._built_targets = {}
    self._failed_nodes = {}
    self._module_cache = {}
    self._node_cache = {}
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
  
  def   moduleDepends( self, node, deps ):
    module_cache = self._module_cache
    node_cache = self._node_cache
    
    module_nodes = _getModuleNodes( node, module_cache, node_cache )
    
    for dep in deps:
      dep_nodes = _getModuleNodes( dep, module_cache, node_cache )
      
      common = module_nodes & dep_nodes
      only_module_nodes = module_nodes - common 
      
      leafs = _getLeafNodes( only_module_nodes, common, node_cache )
      
      for leaf in leafs:
        self._nodes.depends( leaf, (dep,) )
  
  #//-------------------------------------------------------//
  
  def   sync( self, nodes, deep = False ):
    node_locker = self._node_locker
    if node_locker is None:
      self._node_locker = node_locker = _NodeLocker()
        
    if deep:
      node_locker.syncModules( nodes, self._module_cache, self._node_cache )
    else:
      node_locker.sync( nodes )
  
  #//-------------------------------------------------------//
  
  def   unlockNode( self, node ):
    node_locker = self._node_locker
    if node_locker is not None:    
      node_locker.unlock( node )
  
  #//-------------------------------------------------------//
  
  def   __len__(self):
    return len(self._nodes)
  
  #//-------------------------------------------------------//
  
  def   selfTest( self ):
    self._nodes.selfTest()
    if self._node_locker is not None:
      self._node_locker.selfTest()
  
  #//-------------------------------------------------------//
  
  def   getNextNodes( self ):
    tails = self._nodes.popTails()
    
    if not tails:
      node_locker = self._node_locker
      if node_locker is not None:
        return node_locker.popUnlocked()
    
    return tails
  
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
    
    self.unlockNode( node )
    self._nodes.removeTail( node )
    node.shrink()
  
  #//-------------------------------------------------------//
  
  def   actualNode( self, node ):
    self.unlockNode( node )
    self._nodes.removeTail( node )
    self.actual += 1
    
    node.shrink()
  
  #//-------------------------------------------------------//
  
  def   completedNode( self, node, builder_output ):
    self._checkAlreadyBuilt( node )
    self.unlockNode( node )
    self._nodes.removeTail( node )
    self._addToBuiltNodeNames( node )
    
    self.completed += 1
    
    eventNodeBuildingFinished( node, builder_output, self.getProgressStr() )
    
    node.shrink()
  
  #//-------------------------------------------------------//
  
  def   failedNode( self, node, error ):
    self.unlockNode( node )
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
    entities = node.getTargetEntities()
    
    built_targets = self._built_targets
    
    for entity in entities:
      entity_sign = entity.signature
      other_entity_sign = built_targets.setdefault( entity.getId(), entity_sign )
      
      if other_entity_sign != entity_sign:
        eventBuildTargetTwice( entity, node )
  
  #//-------------------------------------------------------//
  
  def   shrink( self, nodes ):
    if not nodes:
      return
    
    self._nodes.shrinkTo( nodes )
  
  #//-------------------------------------------------------//
  
  def   getNodes(self):
    return self._nodes.getNodes()
  
  #//-------------------------------------------------------//
  
  def   build( self, jobs, keep_going, nodes = None, build_always = False, explain = False, with_backtrace = True, force_lock = False):
    
    self.__reset( build_always = build_always, explain = explain )
    
    self.shrink( nodes )
    
    node_locker = self._node_locker
    
    with _NodesBuilder( self, jobs, keep_going, with_backtrace, force_lock = force_lock ) as nodes_builder:
      while True:
        tails = self.getNextNodes()
        
        if not tails and not nodes_builder.isBuilding():
          break
        
        if not nodes_builder.build( tails, node_locker ):
          # no more processing threads
          break
    
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
  
  def   clear( self, nodes = None, force_lock = False ):
    
    self.__reset()
    
    self.shrink( nodes )
    
    with _NodesBuilder( self, force_lock = force_lock ) as nodes_builder:
      while True:
        
        tails = self.getNextNodes()
        
        if not tails:
          break
        
        nodes_builder.clear( tails )
  
  #//-------------------------------------------------------//
  
  def   status( self, nodes = None, explain = False, force_lock = False ):
    
    self.__reset( explain = explain )
    
    self.shrink( nodes )
    
    with _NodesBuilder( self, force_lock = force_lock ) as nodes_builder:
      
      while True:
        tails = self.getNextNodes()
        
        if not tails:
          break
        
        nodes_builder.status( tails )
    
    return self.isOk()
