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
    'nodes',
    'node_deps',
    'dep_nodes',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self ):
    self.nodes = set()
    self.node_names = set()
    self.node_deps = {}
    self.dep_nodes = {}
  
  #//-------------------------------------------------------//
  
  def   __len__(self):
    return len(self.node_names)
  
  #//-------------------------------------------------------//
  
  def __flatDeps( self, deps ):
    flatten_deps = set(deps)
    flatten_deps_update = flatten_deps.update
    get_node = self.node_deps.__getitem__
    
    for dep in source_nodes:
      flatten_deps_update( get_node( dep.name )[1] )
    
    return flatten_deps
  
  #//-------------------------------------------------------//
  
  def   __addDeps( self, node, deps ):
    
    node_deps = self.node_deps
    dep_nodes = self.dep_nodes
    
    current_node_deps = node_deps[ node ]
    
    new_deps = set(deps) - current_node_deps
    
    if not new_deps:
      return
    
    unknown_deps = new_deps - self.nodes
    if unknown_deps:
      raise Exception("Unknown node: %s" % str(unknown_deps.pop().long_name) )
    
    for dep in deps:
      new_deps |= node_deps[dep]
    
    new_deps -= current_node_deps
    
    if node in new_deps:
      raise Exception( "Node has a cyclic dependency: %s" % str(node.long_name) )
    
    #//-------------------------------------------------------//
    
    current_node_deps |= new_deps
    
    #//-------------------------------------------------------//
    
    deps_from_node = set(dep_nodes[ node ])
    
    for dep in deps_from_node:
      node_deps[ dep ] |= new_deps
    
    #//-------------------------------------------------------//
    
    deps_from_node.add( node )
    
    for dep in new_deps:
      dep_nodes[ dep ] |= deps_from_node
    
  #//-------------------------------------------------------//
  
  def   add( self, node ):
    
    if node.name in self.node_names:
      raise Exception("Multiple instances of node: %s" % str(node.long_name) )
    
    self.node_names.add( node.name )
    self.nodes.add( node )
    self.node_deps[ node ] = set()
    self.dep_nodes[ node ] = set()
    
    self.__addDeps( node, node.source_nodes )
    
  #//-------------------------------------------------------//
  
  def   addDeps( self, node, deps ):
    if node.name not in self.node_names:
      raise Exception("Unknown node: %s" % str(node.long_name) )
    
    self.__addDeps( node, toSequence( deps ) )

  #//-------------------------------------------------------//
  
  def   __nodeDeps( self, node ):
    
    all_deps = set()
    
    new_deps = set([node])
    
    while new_deps:
      node = new_deps.pop()
      
      deps = node.source_nodes | node.dep_nodes
      deps -= all_deps
      all_deps |= deps
      new_deps |= deps
    
    return all_deps
  
  #//-------------------------------------------------------//
  
  def   selfTest( self ):
    if len(self.node_names) != len(self.node_deps):
      raise AssertionError("len(self.node_names)(%s) != len(self.node_deps)(%s)" % (len(self.node_names), len(self.node_deps)) )
    
    if self.nodes != set(self.dep_nodes):
      raise AssertionError("Not all deps are added")
    
    if self.nodes != set(self.node_deps):
      raise AssertionError("Not all nodes are added")
    
    all_dep_nodes = set()
    
    for node in self.node_deps:
      if node.name not in self.node_names:
        raise AssertionError("Missed node's name: %s" % str(node.long_name) )
      
      if node not in self.nodes:
        raise AssertionError("Missed node: %s" % str(node.long_name) )
      
      node_deps = self.__nodeDeps( node )
      
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
  

