import hashlib

from aql_node import Node
from aql_task_manager import TaskManager
from aql_values_file import ValuesFile
from aql_logging import logError,logInfo,logWarning
from aql_utils import toSequence

#//===========================================================================//

class _Nodes (object):
  
  __slots__ = \
  (
    'node_names',
    'node_deps',
    'dep_nodes',
    'tail_nodes',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self ):
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
        raise Exception( "Node has a cyclic dependency: %s" % str(node.long_name) )
      
      self.tail_nodes.discard( node )
      
      #//-------------------------------------------------------//
      
      current_node_deps |= new_deps
      
      #//-------------------------------------------------------//
      
      for dep in new_deps:
        dep_nodes[ dep ].add( node )
    
    except KeyError as node:
      raise Exception( "Unknown node: %s" % str(node.args[0].long_name) )
    
  #//-------------------------------------------------------//
  
  def   add( self, node ):
    
    if node.name in self.node_names:
      raise Exception("Multiple instances of node: %s" % str(node.long_name) )
    
    self.node_names.add( node.name )
    self.node_deps[ node ] = set()
    self.dep_nodes[ node ] = set()
    self.tail_nodes.add( node )
    
    self.__addDeps( node, node.source_nodes )
    
  #//-------------------------------------------------------//
  
  def   addDeps( self, node, deps ):
    self.__addDeps( node, toSequence( deps ) )
  
  #//-------------------------------------------------------//
  
  def   removeTail( self, node ):
    node_deps = self.node_deps
    
    try:
      if node_deps[node]:
        raise Exception("Removing non-tail node: %s" % str(node.long_name) )
    except KeyError as node:
      raise Exception( "Unknown node: %s" % str(node.args[0].long_name) )
    
    tail_nodes = self.tail_nodes
    
    self.node_names.remove( node.name )
    del node_deps[node]
    tail_nodes.remove( node )
    
    tails = []
    for dep in self.dep_nodes.pop( node ):
      d = node_deps[ dep ]
      d.remove( node )
      if not d:
        tails.append( dep )
        tail_nodes.add( dep )
    
    return tails
    
  #//-------------------------------------------------------//
  
  def   tails( self ):
    return tuple( self.tail_nodes )
  
  #//-------------------------------------------------------//
  
  def   selfTest( self ):
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
      
      if (node_deps - (node.source_nodes | node.dep_nodes)):
        raise AssertionError("self.node_deps[node] != node_deps for node: %s"  % str(node.long_name) )
      
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
    'active_tasks',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, vfilename, jobs, stop_on_error ):
    self.vfilename = vfilename
    self.jobs = jobs
    self.stop_on_error = stop_on_error
    self.active_tasks = 0
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    if attr in ('vfile'):
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
    #~ print("building nodes: %s" % str(nodes))
    completed_nodes = []
    failed_nodes = []
    
    addTask = self.task_manager.addTask
    vfile = self.vfile
    
    for node in nodes:
      if node.actual( vfile ):
        #~ print("actual node: %s" % str(node))
        completed_nodes.append( node )
      else:
        #~ print("add node to tm: %s" % str(node))
        addTask( node, node.build, vfile )
        self.active_tasks += 1
    
    if self.active_tasks:
      for node, exception in self.task_manager.completedTasks():
        self.active_tasks -= 1
        if exception is None:
          completed_nodes.append( node )
        else:
          if self.stop_on_error:
            self.task_manager.stop()
          
          failed_nodes.append( (node, exception) )
    
    return completed_nodes, failed_nodes

#//===========================================================================//

class BuildManager (object):
  
  __slots__ = \
  (
    '__nodes',
    '__nodes_builder',
    '__vfile',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__(self, vfilename, jobs, stop_on_error ):
    self.__nodes = _Nodes()
    self.__nodes_builder = _NodesBuilder( vfilename, jobs, stop_on_error )
  
  #//-------------------------------------------------------//
  
  def   addNode( self, node ):
    self.__nodes.add( node )
  
  #//-------------------------------------------------------//
  
  def   addDeps( self, node, deps ):
    self.__nodes.addDeps( node, deps )
  
  #//-------------------------------------------------------//
  
  def   tailNodes( self ):
    return self.__nodes.tails()
  
  #//-------------------------------------------------------//
  
  def   __len__(self):
    return len(self.__nodes)
  
  #//-------------------------------------------------------//
  def   selfTest( self ):
    self.__nodes.selfTest()
  
  #//-------------------------------------------------------//
  
  def   build(self):
    target_nodes = {}
    
    tails = self.__nodes.tails()
    
    buildNodes = self.__nodes_builder.build
    removeTailNodes = self.__nodes.removeTail
    
    failed_nodes = []
    
    while tails:
      completed_nodes, tmp_failed_nodes = buildNodes( tails )
      
      failed_nodes += tmp_failed_nodes
      
      tails = []
      
      for node in completed_nodes:
        
        values = []
        values += node.target_values
        values += node.itarget_values
        
        for value in values:
          other_node = target_nodes.setdefault( value.name, node )
          
          if other_node is not node:
            logWarning("Target '%s' is built by different nodes: %s, %s " % ( value.name, node, other_node ) )
        
        tails += removeTailNodes( node )
    
    return failed_nodes
    
  #//-------------------------------------------------------//
  
  def   clear(self):
    vfile = self.__nodes_builder.vfile
    
    for node in self.__nodes.node_deps:
      node.clear( vfile )
  
  #//-------------------------------------------------------//
  
  def   status(self):
    
    target_nodes = {}
    vfile = self.__nodes_builder.vfile
    tails = self.__nodes.tails()
    
    removeTailNodes = self.__nodes.removeTail
    
    while tails:
      new_tails = []
      
      for node in tails:
        if not node.actual( vfile ):
          logInfo("Outdated node: %s" % node )
        else:
          new_tails += removeTailNodes( node )
      
      tails = new_tails
