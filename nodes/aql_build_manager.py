import hashlib

from aql_node import Node
from aql_logging import logError
from aql_utils import toSequence

def  _nodesToStr( nodes ):
  return str( list( map( lambda n : n.long_name, nodes ) ) )

#//===========================================================================//

class _Nodes (object):
  
  __slots__ = \
  (
    'node_names',
    'node_deps',
    'dep_nodes',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self ):
    self.node_names = set()
    self.node_deps = {}
    self.dep_nodes = {}
  
  #//-------------------------------------------------------//
  
  def   __len__(self):
    return len(self.node_names)
  
  #//-------------------------------------------------------//
  
  def   __hasCycle( self, node, new_deps ):
    
    if node in new_deps:
      return True
    
    deps = set(new_deps)
    node_deps = self.node_deps
    
    try:
      while deps:
        dep = deps.pop()
        
        dep_deps = node_deps[dep]
        
        if node in dep_deps:
          return True
        
        deps |= dep_deps
    except KeyError as dep:
      raise Exception("Unknown node: %s" % str(dep.args[0].long_name) )
    
    return False
  
  #//-------------------------------------------------------//
  
  def   __addDeps( self, node, deps ):
    
    node_deps = self.node_deps
    dep_nodes = self.dep_nodes
    
    current_node_deps = node_deps[ node ]
    
    new_deps = set(deps) - current_node_deps
    
    if not new_deps:
      return
    
    if self.__hasCycle( node, new_deps ):
      raise Exception( "Node has a cyclic dependency: %s" % str(node.long_name) )
    
    #//-------------------------------------------------------//
    
    current_node_deps |= new_deps
    
    #//-------------------------------------------------------//
    
    for dep in new_deps:
      dep_nodes[ dep ].add( node )
    
  #//-------------------------------------------------------//
  
  def   add( self, node ):
    
    if node.name in self.node_names:
      raise Exception("Multiple instances of node: %s" % str(node.long_name) )
    
    self.node_names.add( node.name )
    self.node_deps[ node ] = set()
    self.dep_nodes[ node ] = set()
    
    self.__addDeps( node, node.source_nodes )
    
  #//-------------------------------------------------------//
  
  def   addDeps( self, node, deps ):
    if node.name not in self.node_names:
      raise Exception("Unknown node: %s" % str(node.long_name) )
    
    self.__addDeps( node, toSequence( deps ) )
  
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
      
      all_dep_nodes |= node_deps
      
      if self.node_deps[node] != node_deps:
        raise AssertionError("self.node_deps[node] != node_deps for node: %s"  % str(node.long_name) )
      
      for dep in node_deps:
        if node not in self.dep_nodes[dep]:
          raise AssertionError("node not in self.dep_nodes[dep]: dep: %s, node: %s"  % (dep.long_name, node.long_name) )
    
    if (all_dep_nodes - set(self.dep_nodes)):
      raise AssertionError("Not all deps are added")

#//===========================================================================//

class BuildManager (object):
  
  __slots__ = \
  (
    '__nodes',
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
  
  def   __len__(self):
    return len(self.__nodes)
  
  #//-------------------------------------------------------//
  def   selfTest( self ):
    self.__nodes.selfTest()
  
  #//-------------------------------------------------------//
  
  def   build(self):
    pass
  
  #//-------------------------------------------------------//
  

