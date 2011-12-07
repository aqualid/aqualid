import hashlib

from aql_value import Value
from aql_logging import logError
from aql_utils import toSequence

class Node (object):
  
  __slots__ = \
  (
    'builder',
    'source_nodes',
    'source_values',
    'dep_nodes',
    'dep_values',
    'implicit_dep_values',
    'target_values',
    'side_effect_values',
    
    'name',
    'long_name',
    'target_name',
    'side_name',
    'implicit_deps_name',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, builder, sources ):
    
    self.builder = builder
    self.source_nodes, self.source_values = self.__getSourceNodes( sources )
    self.dep_values = []
    self.dep_nodes = []
  
  #//=======================================================//
  
  def   __getSourceNodes( self, sources )
    
    source_nodes = []
    source_values = []
    
    source_nodes_append = source_nodes.append
    source_values_append = source_values.append
    
    for source in toSequence( sources ):
      if isintance(source, Node):
        source_nodes_append( source )
      elif isintance(source, Value):
        source_values_append( source )
      else:
        raise Exception( "Unknown source type: %s" % type(source) )
    
    return source_nodes, source_values
    
  #//=======================================================//
  
  def   __getLongName( self ):
    names = []
    names_append = names.append
    names_append( self.builder.long_name )
    
    for source in self.source_nodes:
      names += source.long_name
    
    for source in self.source_values:
      names_append( source.name )
    
    names.sort()
    
    return names

  #//=======================================================//
  
  def   __getNames( self ):
     chcksum = hashlib.md5()
     
     for name in self.long_name:
       chcksum.update( name )
     
     name = chcksum.digest()
     chcksum.update( 'targets' )
     target_name = chcksum.digest()
     
     chcksum.update( 'side_effect_values' )
     side_name = chcksum.digest()
     
     chcksum.update( 'implicit_dep_values' )
     implicit_deps_name = chcksum.digest()
     
     return name, target_name, side_name, implicit_deps_name
  
  #//=======================================================//
  
  def   __getattr__( self, attr )
    if attr in ('name', 'target_name', 'side_name', 'implicit_deps_name'):
      self.name, self.target_name, self.side_name = self.__getNames()
      return getattr(self, attr)
    
    elif attr == 'long_name':
      long_name = self.__getLongName()
      self.long_name = long_name
      return long_name
    
    elif attr == 'implicit_dep_values':
      implicit_deps = self.builder.scan( self )
      self.implicit_dep_values = implicit_deps
      return implicit_deps
   
   raise AttributeError("Unknown attribute: '%s'" % str(attr) )
  
  #//=======================================================//
  
  def   sourcesValue( self ):
    source_values = list(self.source_values)
    
    for node in self.source_nodes:
      source_values += node.target_values
    
    for node in self.dep_nodes:
      source_values += node.target_values
    
    source_values += self.builder.values()
    
    return DependsValue( self.name source_values )
  
  #//=======================================================//
  
  def   save( self, vfile ):
    
    values = []
    values += self.source_values
    values += self.dep_values
    values += self.builder.values()
    values += self.implicit_dep_values
    values += self.target_values
    values += self.side_effect_values
    
    values.append( self.sourcesValue() )
    values.append( DependsValue( self.implicit_deps_name, self.implicit_dep_values ) )
    values.append( DependsValue( self.target_name,        self.target_values ) )
    values.append( DependsValue( self.side_name,          self.side_effect_values ) )
    
    vfile.addValues( values )
  
  #//=======================================================//
  
  def   build( self ):
    self.builder( self )
  
  #//=======================================================//
  
  def   actual( self, vfile ):
    sources_value = self.sourcesValue()
    targets_value = DependsValue( self.target_name )
    side_effects_value = DependsValue( self.side_name )
    deps_value = DependsValue( self.deps_name )
    ideps_value = DependsValue( self.implicit_deps_name )
    
    values = [sources_value, targets_value, side_effects_value, deps_value, ideps_value ]
    values = vfile.findValues( values )
    old_sources_value = values[0]
    
    if sources_value != old_sources_value:
      return False
    
    for value in values[1:]:
      if not value.actual():
        return False
    
    return True
  
  #//=======================================================//
  
  def   sources( self ):
    return self.source_nodes
  
