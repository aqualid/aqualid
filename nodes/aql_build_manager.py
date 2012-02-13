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

class _Nodes (object):
  
  __slots__ = \
  (
    'lock',
    'node_names',
    'node_deps',
    'dep_nodes',
    'tail_nodes',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self ):
    self.lock = threading.Lock()
    self.node_names = set()
    self.node_deps = {}
    self.dep_nodes = {}
    self.tail_nodes = set()
  
  #//-------------------------------------------------------//
  
  def   __len__(self):
    return len(self.node_names)
  
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
  
  def   __addDeps( self, node, deps ):
    
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
          if node.name in self.node_names:
            raise NodeAlreadyExists( node )
          
          self.node_names.add( node.name )
          self.node_deps[ node ] = set()
          self.dep_nodes[ node ] = set()
          self.tail_nodes.add( node )
          
          self.__add( node.source_nodes )   # TODO: recursively add sources and depends
          self.__add( node.dep_nodes )      # It would be better to rewrite this code to aviod the recursion
          
          self.__addDeps( node, node.source_nodes )
          self.__addDeps( node, node.dep_nodes )
    
  #//-------------------------------------------------------//
  
  def   add( self, nodes ):
    with self.lock:
      self.__add( toSequence( nodes ) )
    
  #//-------------------------------------------------------//
  
  def   addDeps( self, node, deps ):
    with self.lock:
      deps = toSequence( deps )
      
      self.__add( deps )
      self.__addDeps( node, deps )
  
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
      
      self.node_names.remove( node.name )
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
      if len(self.node_names) != len(self.node_deps):
        raise AssertionError("len(self.node_names)(%s) != len(self.node_deps)(%s)" % (len(self.node_names), len(self.node_deps)) )
      
      if set(self.node_deps) != set(self.dep_nodes):
        raise AssertionError("Not all deps are added")
      
      all_dep_nodes = set()
      
      for node in self.dep_nodes:
        if node.name not in self.node_names:
          raise AssertionError("Missed node's name: %s" % str(node.long_name) )
        
        if node not in self.node_deps:
          raise AssertionError("Missed node: %s" % str(node.long_name) )
        
        #~ node_deps = node.source_nodes | node.dep_nodes
        node_deps = self.node_deps[node]
        
        if not node_deps:
          if node not in self.tail_nodes:
            raise AssertionError("Missed tail node: %s"  % str(node.long_name) )
        else:
          if node in self.tail_nodes:
            raise AssertionError("Invalid tail node: %s"  % str(node.long_name) )
        
        all_dep_nodes |= node_deps
        
        #~ if (node_deps - (node.source_nodes | node.dep_nodes)):
          #~ raise AssertionError("self.node_deps[node] != node_deps for node: %s"  % str(node.long_name) )
        
        for dep in node_deps:
          if node not in self.dep_nodes[dep]:
            raise AssertionError("node not in self.dep_nodes[dep]: dep: %s, node: %s"  % (dep.long_name, node.long_name) )
      
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
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, vfilename, jobs, stop_on_error ):
    self.vfilename = vfilename
    self.jobs = jobs
    self.stop_on_error = stop_on_error
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    if attr == 'vfile':
      vfile = ValuesFile( self.vfilename )
      self.vfile = vfile
      return vfile
    
    elif attr == 'task_manager':
      tm = TaskManager( self.jobs )
      
      self.task_manager = tm
      return tm
    
    raise AttributeError("Unknown attribute: '%s'" % str(attr) )
    
  #//-------------------------------------------------------//
  
  def   build( self, nodes ):
    completed_nodes = []
    failed_nodes = {}
    rebuild_nodes = []
    
    addTask = self.task_manager.addTask
    
    vfile = self.vfile
    
    for node in nodes:
      if node.actual( vfile ):
        event_manager.eventActualNode( node )
        completed_nodes.append( node )
      else:
        event_manager.eventOutdateNode( node )
        addTask( node, node.build, vfile )
    
    if not completed_nodes:
      for node, exception in self.task_manager.completedTasks():
        if exception is None:
          completed_nodes.append( node )
        else:
          if isinstance( exception, RebuildNode ):
            event_manager.eventRebuildNode( node )
            rebuild_nodes.append( node )
          else:
            if self.stop_on_error:
              self.task_manager.stop()
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
    self.__nodes = _Nodes()
    self.__nodes_builder = _NodesBuilder( vfilename, jobs, stop_on_error )
  
  #//-------------------------------------------------------//
  
  def   addNodes( self, nodes ):
    self.__nodes.add( nodes )
  
  #//-------------------------------------------------------//
  
  def   addDeps( self, node, deps ):
    self.__nodes.addDeps( node, deps )
  
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
        if not other_node.actual( vfile ):
          event_manager.eventTargetIsBuiltTwiceByNodes( value, node, other_node )
  
  #//-------------------------------------------------------//
  
  def   build(self):
    event_manager.eventBuildingNodes( len(self.__nodes) )
    
    target_nodes = {}
    
    getTails = self.__nodes.tails
    
    buildNodes = self.__nodes_builder.build
    removeTailNode = self.__nodes.removeTail
    
    waiting_nodes = set()
    waitingDiff = waiting_nodes.difference_update
    
    failed_nodes = {}
    
    while True:
      
      tails = getTails()
      tails -= waiting_nodes
      tails.difference_update( failed_nodes )
      
      if not tails and not waiting_nodes:
        break
      
      completed_nodes, tmp_failed_nodes, rebuild_nodes = buildNodes( tails )
      
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
  
  def   clear(self):
    vfile = self.__nodes_builder.vfile
    
    for node in self.__nodes.node_deps:
      node.clear( vfile )
  
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
