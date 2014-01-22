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
)

import threading
import traceback

from aql.util_types import toSequence
from aql.utils import eventStatus, eventWarning, logInfo, logError, logWarning, TaskManager
from aql.values import ValuesFile

#//===========================================================================//

@eventStatus
def   eventBuildStatusOutdatedNode( node, detailed ):
  logInfo("Outdated node: %s" % node.getBuildStr( detailed ) )

#//===========================================================================//

@eventStatus
def   eventBuildStatusActualNode( node, detailed ):
  logInfo("Actual node: %s" % node.getBuildStr( detailed ) )

#//===========================================================================//

@eventWarning
def   eventBuildTargetTwiceByNodes( value, node1, node2, detailed ):
  logWarning("Target '%s' is built twice by different nodes: '%s', '%s' " %
             ( value.name, node1.getBuildStr( detailed ), node2.getBuildStr( detailed ) ) )

#//===========================================================================//

@eventStatus
def   eventBuildingNodes( total_nodes ):
  logInfo("Building %s nodes" % total_nodes )

#//===========================================================================//

@eventStatus
def   eventBuildNodeFailed( node, error ):
  
  msg = node.getBuildStr( detailed = True )
  msg += '\n' + str(error)
  logError( msg )
  
  if __debug__:
    try:
      traceback.print_tb( error.__traceback__ )
    except AttributeError:
      pass

#//===========================================================================//

@eventStatus
def   eventNodeBuilding( node, detailed ):
  pass

#//===========================================================================//

@eventStatus
def   eventNodeBuildingFinished( node, out, detailed ):
  
  msg = node.getBuildStr( detailed )
  if detailed and out:
    msg += out
  
  logInfo( msg )

#//===========================================================================//

class   ErrorNodeDependencyCyclic( Exception ):
  def   __init__( self, node ):
    msg = "Node has a cyclic dependency: %s" % str(node)
    super(ErrorNodeDependencyCyclic, self).__init__( msg )

#//===========================================================================//

class   ErrorNodeUnknown(Exception):
  def   __init__( self, node ):
    msg = "Unknown node '%s'" % (node, )
    super(ErrorNodeUnknown, self).__init__( msg )

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
  def   __init__( self, node ):
    msg = "Remove unknown tail node: : %s" % str(node)
    super(InternalErrorRemoveUnknownTailNode, self).__init__( msg )

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

          self.__add( node_srcnodes )       # TODO: recursively add sources and depends
          self.__add( node.dep_nodes )      # It would be better to rewrite this code to avoid the recursion
          
          self.__depends( node, node_srcnodes )
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
  
  def   __getitem__( self, builder ):
    
    builder_name = builder.name
    
    try:
      vfilename = self.names[ builder_name ]
    except KeyError:
      build_path = builder.getBuildPath()
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

def   _buildNode( builder, node, detailed ):
  
  eventNodeBuilding( node, detailed )
  
  out = builder.build( node )
  
  eventNodeBuildingFinished( node, out, detailed )


#//===========================================================================//

# noinspection PyAttributeOutsideInit
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
      self.task_manager = tm = TaskManager( num_threads = self.jobs, stop_on_fail = not self.keep_going )
      return tm
    
    raise AttributeError( "%s instance has no attribute '%s'" % (type(self), attr) )
    
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, nodes, detailed ):
    completed_nodes = []
    failed_nodes = {}
    rebuild_nodes = []
    
    vfiles = self.vfiles
    addTask = self.task_manager.addTask
    
    for node in nodes:
      
      node.initiate()
      
      builder = node.builder
      
      vfile = vfiles[ builder ]
      
      pre_nodes = self.prebuild_nodes.pop( node, None )
      
      if pre_nodes:
        builder.prebuildFinished( vfile, node, pre_nodes )
      else:
        pre_nodes = builder.prebuild( vfile, node )
        if pre_nodes:
          self.prebuild_nodes[ node ] = pre_nodes
          build_manager.depends( node, pre_nodes )
          rebuild_nodes.append( node )
          continue
      
      if builder.actual( vfile, node ):
        # eventBuildStatusActualNode( node )
        completed_nodes.append( node )
      else:
        addTask( node, _buildNode, builder, node, detailed )
    
    if not completed_nodes and not rebuild_nodes:
      completed_nodes, failed_nodes = self.__getFinishedNodes()
      # print("completed_nodes: %s" % (completed_nodes,))
    
    return completed_nodes, failed_nodes, rebuild_nodes
  
  #//-------------------------------------------------------//
  
  def   __getFinishedNodes( self ):
    completed_nodes = []
    failed_nodes = {}
    
    finished_tasks = self.task_manager.finishedTasks()
    # print("finished_tasks: %s" % (len(finished_tasks), ))
    
    vfiles = self.vfiles
    
    for node, exception in finished_tasks:
      
      builder = node.builder
      
      if exception is None:
        builder.save( vfiles[ builder ], node )
        completed_nodes.append( node )
      else:
        eventBuildNodeFailed( node, exception )
        failed_nodes[ node ] = exception
    
    return completed_nodes, failed_nodes
  
  #//-------------------------------------------------------//
  
  def   close( self ):
    self.task_manager.finish()
    self.__getFinishedNodes()
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
  
  def   __len__(self):
    return len(self._nodes)
  
  #//-------------------------------------------------------//
  
  def   selfTest( self ):
    self._nodes.selfTest()
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __checkAlreadyBuilt( target_nodes, node ):
    values = []
    values += node.getTargetValues()
    values += node.getSideEffectValues()
    
    for value in values:
      other_node, other_value = target_nodes.setdefault( value.name, (node, value) )
      
      if other_value != value:
        eventBuildTargetTwiceByNodes( value, node, other_node )
  
  #//-------------------------------------------------------//
  
  def   build( self, jobs, keep_going, nodes = None, detailed = False ):
    
    nodes_tree = self._nodes
    if nodes is not None:
      nodes_tree.shrinkTo( nodes )
    
    with _NodesBuilder( jobs, keep_going ) as nodes_builder:
      
      eventBuildingNodes( len(nodes_tree) )
      
      target_nodes = {}
      
      waiting_nodes = set()
      failed_nodes = {}
      
      while True:
        
        tails = nodes_tree.tails()
        tails -= waiting_nodes
        tails.difference_update( failed_nodes )
        
        if not tails and not waiting_nodes:
          break
        
        completed_nodes, tmp_failed_nodes, rebuild_nodes = nodes_builder.build( self, tails, detailed )
        
        if not (completed_nodes or tmp_failed_nodes or rebuild_nodes):
          break
        
        failed_nodes.update( tmp_failed_nodes )
        
        waiting_nodes |= tails
        
        waiting_nodes.difference_update( completed_nodes )
        waiting_nodes.difference_update( tmp_failed_nodes )
        waiting_nodes.difference_update( rebuild_nodes )
        
        for node in completed_nodes:
          self.__checkAlreadyBuilt( target_nodes, node )
          nodes_tree.removeTail( node )
      
      return tuple( failed_nodes.items() )
    
  #//-------------------------------------------------------//
  
  def   close( self ):
    self._nodes = _NodesTree()
    self._jobs = 1
  
  #//-------------------------------------------------------//
  
  def   clear( self, nodes = None ):
    
    nodes_tree = self._nodes
    if nodes is not None:
      nodes_tree.shrinkTo( nodes )
    
    with _VFiles() as vfiles:
      
      while True:
        tails = nodes_tree.tails()
        
        if not tails:
          break
        
        for node in tails:
          
          node.initiate()
          
          vfile = vfiles[ node.builder ]
          
          node.clear( vfile )
          
          nodes_tree.removeTail( node )
  
  #//-------------------------------------------------------//
  
  def   status( self, detailed ):
    
    with _VFiles() as vfiles:
      getTails = self._nodes.tails
      
      removeTailNode = self._nodes.removeTail
      
      outdated_nodes = set()
      
      while True:
        tails = getTails() - outdated_nodes
        if not tails:
          break
        
        for node in tails:
          
          node.initiate()
          
          builder = node.builder
          
          vfile = vfiles[ builder ]
          
          # TODO: add support for prebuild
          if not builder.actual( vfile, node ):
            eventBuildStatusOutdatedNode( node, detailed )
            outdated_nodes.add( node )
          else:
            eventBuildStatusActualNode( node, detailed )
            removeTailNode( node )
