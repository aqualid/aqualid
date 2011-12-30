import hashlib

from aql_node import Node
from aql_logging import logError
from aql_utils import toSequence

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
  
  def __flatDeps( self, deps ):
    flatten_deps = set(deps)
    flatten_deps_update = flatten_deps.update
    get_node = self.node_deps.__getitem__
    
    for dep in source_nodes:
      flatten_deps_update( get_node( dep.name )[1] )
    
    return flatten_deps
  
  #//-------------------------------------------------------//
  
  def   __addDeps( self, node, deps ):
    
    nodes = self.node_deps
    dep_nodes = self.dep_nodes
    
    flatten_deps = set(deps)
    flatten_deps_update = flatten_deps.update
    get_deps = nodes.get
    
    for dep in deps:
      d = get_deps( dep )
      if d:
        flatten_deps_update( d )
    
    if node in flatten_deps:
      raise Exception( "Node has a cyclic dependency: %s" % str(node.long_name) )
    
    #//-------------------------------------------------------//
    
    nodes.setdefault( node, set() ).update( flatten_deps )
    
    #//-------------------------------------------------------//
    
    deps_from_node = dep_nodes.get( node, set() )
    
    for dep in deps_from_node:
      nodes[ dep ].update( flatten_deps )
    
    #//-------------------------------------------------------//
    
    deps_from_node.add( node )
    deps_add = dep_nodes.setdefault
    for dep in flatten_deps:
      deps_add( dep, set() ).update( deps_from_node )
    
  #//-------------------------------------------------------//
  
  def   add( self, node ):
    
    if node.name in self.node_names:
      raise Exception("Multiple instances of node: %s" % str(node.long_name) )
    
    self.node_names.add( node.name )
    
    self.__addDeps( node, node.source_nodes )
    
  #//-------------------------------------------------------//
  
  def   addDeps( self, node, deps ):
    self.__addDeps( node, toSequence( deps ) )

  #//-------------------------------------------------------//
  
  def   __nodeDeps( self, node, flatten_deps = None ):
    
    if flatten_deps is None:
      flatten_deps = set()
    
    deps = node.source_nodes - flatten_deps
    
    flatten_deps.update( deps )
    
    for dep in deps:
      self.__nodeDeps( dep, flatten_deps )
    
    #//-------------------------------------------------------//
    
    deps = node.dep_nodes - flatten_deps
    
    flatten_deps.update( deps )
    
    for dep in deps:
      self.__nodeDeps( dep, flatten_deps )
    
    return flatten_deps
  
  #//-------------------------------------------------------//
  
  def   selfTest( self ):
    if len(self.node_names) != len(self.node_deps):
      raise AssertionError("len(self.node_names)(%s) != len(self.node_deps)(%s)" % (len(self.node_names), len(self.node_deps)) )
    
    all_dep_nodes = set()
    
    for node in self.node_deps:
      if node.name not in self.node_names:
        raise AssertionError("Missed node's name: %s" % str(node.long_name) )
      
      node_deps = self.__nodeDeps( node )
      
      all_dep_nodes |= node_deps
      
      if self.node_deps[node] != node_deps:
        raise AssertionError("self.node_deps[node] != node_deps for node: %s"  % str(node.long_name) )
      
      for dep in node_deps:
        if node not in self.dep_nodes[dep]:
          raise AssertionError("node not in self.dep_nodes[dep]: dep: %s, node: %s"  % (dep.long_name, node.long_name) )
      
    if all_dep_nodes != set(self.dep_nodes):
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
  

