import hashlib

from aql_node import Node
from aql_logging import logError
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
    
    del self.node_names[ node.name ]
    del node_deps[node]
    tail_nodes.remove( node )
    
    tails = []
    for dep in self.dep_nodes.pop( node ):
      d = node_deps[ dep ]
      d.remove( dep )
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
      
      node_deps = node.source_nodes | node.dep_nodes
      
      if not node_deps:
        if node not in self.tail_nodes:
          raise AssertionError("Missed tail node: %s"  % str(node.long_name) )
      else:
        if node in self.tail_nodes:
          raise AssertionError("Invalid tail node: %s"  % str(node.long_name) )
      
      all_dep_nodes |= node_deps
      
      if self.node_deps[node] != node_deps:
        raise AssertionError("self.node_deps[node] != node_deps for node: %s"  % str(node.long_name) )
      
      for dep in node_deps:
        if node not in self.dep_nodes[dep]:
          raise AssertionError("node not in self.dep_nodes[dep]: dep: %s, node: %s"  % (dep.long_name, node.long_name) )
    
    if (all_dep_nodes - set(self.dep_nodes)):
      raise AssertionError("Not all deps are added")

#//===========================================================================//

class _BuildingNodes (object):
  
  __slots__ = \
  (
    '__nodes',
    '__failed',
  )
  
  def   __init__( self ):
    self.

#//===========================================================================//

class BuildManager (object):
  
  __slots__ = \
  (
    '__nodes',
    '__building_nodes',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__(self):
    self.__nodes = _Nodes()
  
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
    tails = self.__nodes.tails()
    
    while tails:
      for node in tails:
        self.__building_nodes.add( node )
      
      built_nodes = self.__building_nodes.builtNodes()
      
      tails = []
      for node in built_nodes:
        tails += self.__nodes.removeTail( node )
  
  #//-------------------------------------------------------//
  

