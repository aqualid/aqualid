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
import hashlib

from aql_event_manager import event_manager
from aql_errors import NodeHasCyclicDependency, UnknownNode, NodeAlreadyExists, RemovingNonTailNode

from aql_node import Node
from aql_builder import RebuildNode
from aql_task_manager import TaskManager
from aql_values_file import ValuesFile
from aql_utils import toSequence

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
        raise NodeHasCyclicDependency( node )
      
      self.tail_nodes.discard( node )
      
      #//-------------------------------------------------------//
      
      current_node_deps |= new_deps
      
      #//-------------------------------------------------------//
      
      for dep in new_deps:
        dep_nodes[ dep ].add( node )
    
    except KeyError as node:
      raise UnknownNode( node.args[0] )
    
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
          raise RemovingNonTailNode( node )
      except KeyError as node:
        raise UnknownNode( node.args[0] )
      
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

class _NodesBuilder (object):
  
  __slots__ = \
  (
    'vfile',
    'vfilename',
    'jobs',
    'stop_on_error',
    'task_manager',
    'prebuild_nodes',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, vfilename, jobs, stop_on_error ):
    self.vfilename = vfilename
    self.jobs = jobs
    self.stop_on_error = stop_on_error
    self.prebuild_nodes = {}
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    if attr == 'vfile':
      vfile = ValuesFile( self.vfilename )
      self.vfile = vfile
      return vfile
    
    elif attr == 'task_manager':
      tm = TaskManager( num_threads = self.jobs, stop_on_error = self.stop_on_error )
      
      self.task_manager = tm
      return tm
    
    raise AttributeError("Unknown attribute: '%s'" % str(attr) )
    
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, nodes ):
    completed_nodes = []
    failed_nodes = {}
    rebuild_nodes = []
    
    add_task = self.task_manager.addTask
    
    vfile = self.vfile
    
    for node in nodes:
      pre_nodes = self.prebuild_nodes.pop( node, None )
      
      if pre_nodes:
        node.prebuildFinished( vfile, pre_nodes )
      else:
        pre_nodes = node.prebuild( vfile )
        if pre_nodes:
          self.prebuild_nodes[ node ] = pre_nodes
          build_manager.depends( node, pre_nodes )
          rebuild_nodes.append( node )
          continue
      
      if node.actual( vfile ):
        completed_nodes.append( node )
      else:
        add_task( node, node.build, build_manager, vfile, pre_nodes )
    
    if not completed_nodes and not rebuild_nodes:
      for node, exception in self.task_manager.completedTasks():
        if exception is None:
          completed_nodes.append( node )
        else:
          if isinstance( exception, RebuildNode ):
            event_manager.eventRebuildNode( node )
            rebuild_nodes.append( node )
          else:
            event_manager.eventFailedNode( node, exception )
            failed_nodes[ node ] = exception
    
    return completed_nodes, failed_nodes, rebuild_nodes

#//===========================================================================//

class BuildManager (object):
  
  __slots__ = \
  (
    '__nodes',
    '__nodes_builder',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__(self, vfilename, jobs, stop_on_error ):
    self.__nodes = _NodesTree()
    self.__nodes_builder = _NodesBuilder( vfilename, jobs, stop_on_error )
  
  #//-------------------------------------------------------//
  
  def   add( self, nodes ):
    self.__nodes.add( nodes )
  
  #//-------------------------------------------------------//
  
  def   depends( self, node, deps ):
    self.__nodes.depends( node, deps )
  
  #//-------------------------------------------------------//
  
  def   valuesFile( self ):
    return self.__nodes_builder.vfile
  
  #//-------------------------------------------------------//
  
  def   __len__(self):
    return len(self.__nodes)
  
  #//-------------------------------------------------------//
  
  def   selfTest( self ):
    self.__nodes.selfTest()
  
  #//-------------------------------------------------------//
  
  def   __checkAlreadyBuilt( self, target_nodes, node ):
    values = []
    values += node.target_values
    values += node.itarget_values
    
    vfile = self.valuesFile()
    
    for value in values:
      other_node = target_nodes.setdefault( value.name, node )
      
      if other_node is not node:
        if (other_node.name_key == node.name_key) or not other_node.actual( vfile ):
          event_manager.eventTargetIsBuiltTwiceByNodes( value, node, other_node )
  
  #//-------------------------------------------------------//
  
  def   build(self):
    event_manager.eventBuildingNodes( len(self.__nodes) )
    
    target_nodes = {}
    
    get_tails = self.__nodes.tails
    
    build_nodes = self.__nodes_builder.build
    removeTailNode = self.__nodes.removeTail
    
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
    self.__nodes = _NodesTree()
    self.__nodes_builder.task_manager.finish()
    self.__nodes_builder.vfile.close()
  
  #//-------------------------------------------------------//
  
  def   clear(self):
    get_tails = self.__nodes.tails
    
    remove_tail = self.__nodes.removeTail
    
    failed_nodes = set()
    
    vfile = self.valuesFile()
    
    while True:
      
      tails = get_tails()
      tails -= failed_nodes
      
      if not tails:
        break
      
      for node in tails:
        if node.clear( vfile ):
          remove_tail( node )
        else:
          failed_nodes.add( node )
  
  #//-------------------------------------------------------//
  
  def   status(self):
    
    target_nodes = {}
    vfile = self.__nodes_builder.vfile
    getTails = self.__nodes.tails
    
    removeTailNode = self.__nodes.removeTail
    
    outdated_nodes = set()
    
    while True:
      
      tails = getTails() - outdated_nodes
      if not tails:
        break
      
      for node in tails:
        if not node.actual( vfile ):
          event_manager.eventOutdatedNode( node )
          outdated_nodes.add( node )
        else:
          event_manager.eventActualNode( node )
          removeTailNode( node )
