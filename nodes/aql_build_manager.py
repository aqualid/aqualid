import hashlib

from aql_node import Node
from aql_logging import logError
from aql_utils import toSequence

class BuildManager (object):
  
  __slots__ = \
  (
    '__nodes',
    '__node_deps',
    '__dep_nodes',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__(self):
    self.__nodes = []
    self.__node_deps = {}
  
  #//-------------------------------------------------------//
  
  def   addNodes( nodes ):
    add = self.__nodes.append
    addDeps = self.addDeps
    for node in toSequence( nodes ):
      add( node )
      addDeps( node, node.source_nodes )
  
  #//-------------------------------------------------------//
  
  def   checkDeps( self, node, deps ):
    all_deps = set( deps )
    
    while True:
      sub_deps = set()
      for dep in deps:
        dep_deps = set( dep.source_nodes + dep.dep_nodes )
        
        if node in
        
        sub_deps.update( dep.source_nodes + dep.dep_nodes )
      
      
    
    nodeAdd = self.__node_deps.setdefault( node, set() ).add
    dep_nodes = self.__dep_nodes.setdefault
    
    for dep in toSequence( deps ):
      nodeAdd( dep )
      dep_nodes( dep, set() ).add( node )
  
  #//-------------------------------------------------------//
  
  def   __nodeDeps( self, node )
    node_deps = {}
    
    for node in self.__nodes:
      node_deps[ id(node) ] = [set(map(id, node.source_nodes + node.dep_nodes))]

