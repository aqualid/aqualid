from aql_node import Node

class MetaNode (Node):
  
  #//=======================================================//
  
  def   __getattr__( self, attr ):
    if attr == 'long_name':
      return super(MetaNode,self).__getattr__( attr )
    
    raise UnknownAttribute( self, attr )
  
  #//=======================================================//
  
  def   build( self, vfile ):
    self._build()
  
  #//=======================================================//
  
  def   actual( self, vfile ):
    return False
  
  #//=======================================================//
  
  def   sources(self):
    source_values = list(self.source_values)
    
    for node in self.source_nodes:
      source_values += node.target_values
    
    return source_values
  
  #//=======================================================//
  
  def   clear( self, vfile ):
    pass
