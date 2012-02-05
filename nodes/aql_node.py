import hashlib

from aql_errors import UnknownNodeSourceType, UnknownAttribute, UnknownNodeDependencyType
from aql_value import Value, NoContent
from aql_depends_value import DependsValue
from aql_utils import toSequence

class Node (object):
  
  __slots__ = \
  (
    'builder',
    'source_nodes',
    'source_values',
    'dep_nodes',
    'dep_values',
    
    'idep_values',
    'target_values',
    'itarget_values',
    
    'name',
    'long_name',
    'targets_name',
    'itargets_name',
    'deps_name',
    'ideps_name',
    
    'sources_value',
    'deps_value',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, builder, sources ):
    
    self.builder = builder
    self.source_nodes, self.source_values = self.__getSourceNodes( sources )
    self.dep_values = []
    self.dep_nodes = set()
  
  #//=======================================================//
  
  def   __getSourceNodes( self, sources ):
    
    source_nodes = set()
    source_values = []
    
    source_nodes_append = source_nodes.add
    source_values_append = source_values.append
    
    for source in toSequence( sources ):
      if isinstance(source, Node):
        source_nodes_append( source )
      elif isinstance(source, Value):
        source_values_append( source )
      else:
        raise UnknownNodeSourceType( self, source )
    
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
       chcksum.update( name.encode() )
     
     name = chcksum.digest()
     chcksum.update( b'target_values' )
     targets_name = chcksum.digest()
     
     chcksum.update( b'itarget_values' )
     itargets_name = chcksum.digest()
     
     chcksum.update( b'dep_values' )
     deps_name = chcksum.digest()
     
     chcksum.update( b'idep_values' )
     ideps_name = chcksum.digest()
     
     return name, targets_name, itargets_name, deps_name, ideps_name
  
  #//=======================================================//
  
  def   __sourcesValue( self ):
    source_values = list(self.source_values)
    
    for node in self.source_nodes:
      source_values += node.target_values
    
    return DependsValue( self.name, source_values )
  
  #//=======================================================//
  
  def   __depsValue( self ):
    dep_values = list(self.dep_values)
    
    for node in self.dep_nodes:
      dep_values += node.target_values
    
    dep_values += self.builder.values()
    
    return DependsValue( self.deps_name, dep_values )
  
  #//=======================================================//
  
  def   __getattr__( self, attr ):
    if attr in ('name', 'targets_name', 'itargets_name', 'deps_name', 'ideps_name'):
      self.name, self.targets_name, self.itargets_name, self.deps_name, self.ideps_name = self.__getNames()
      return getattr(self, attr)
    
    elif attr == 'long_name':
      long_name = self.__getLongName()
      self.long_name = long_name
      return long_name
    
    elif attr == 'sources_value':
      self.sources_value = self.__sourcesValue()
      return self.sources_value
    
    elif attr == 'deps_value':
      self.deps_value = self.__depsValue()
      return self.deps_value
    
    raise UnknownAttribute( self, attr )
  
  #//=======================================================//
  
  def   __save( self, vfile ):
    
    values = []
    values += self.source_values
    values += self.dep_values
    values += self.builder.values()
    values += self.idep_values
    values += self.target_values
    values += self.itarget_values
    
    values.append( self.sources_value )
    values.append( self.deps_value )
    values.append( DependsValue( self.ideps_name,     self.idep_values )    )
    values.append( DependsValue( self.targets_name,   self.target_values )  )
    values.append( DependsValue( self.itargets_name,  self.itarget_values ) )
    
    vfile.addValues( values )
  
  #//=======================================================//
  
  def   build( self, vfile ):
    
    self.target_values, self.itarget_values, self.idep_values = self.builder.build( self )
    
    self.__save( vfile )
  
  #//=======================================================//
  
  def   actual( self, vfile ):
    sources_value = self.sources_value
    deps_value    = self.deps_value
    
    targets_value   = DependsValue( self.targets_name   )
    itargets_value  = DependsValue( self.itargets_name  )
    ideps_value     = DependsValue( self.ideps_name     )
    
    values = [ sources_value, deps_value, targets_value, itargets_value, ideps_value ]
    values = vfile.findValues( values )
    
    if sources_value != values.pop(0):
      return False
    
    if deps_value != values.pop(0):
      return False
    
    for value in values:
      if not value.actual():
        return False
    
    targets_value, itargets_value, ideps_value = values
    
    self.target_values  = targets_value.content
    self.itarget_values = itargets_value.content
    self.idep_values    = ideps_value.content
    
    return True
  
  #//=======================================================//
  
  def   sources(self):
    return self.sources_value.content
  
  #//=======================================================//
  
  @staticmethod
  def   __removeContent( values, no_content = NoContent() ):
    for value in values:
      value.content = no_content
  
  #//=======================================================//
  
  def   clear( self, vfile ):
    
    values = [ DependsValue( self.targets_name  ), DependsValue( self.itargets_name  ) ]
    
    targets_value, itargets_value = vfile.findValues( values )
    target_values = targets_value.content
    itarget_values = itargets_value.content
    
    if itarget_values or target_values:
      if isinstance( target_values, NoContent ):
        target_values = tuple()
      
      if isinstance( itarget_values, NoContent ):
        itarget_values = tuple()
      
      self.builder.clear( self, target_values, itarget_values )
      
      values = []
      values += target_values
      values += itarget_values
      
      no_content = NoContent()
      for value in values:
        value.content = no_content
      
      vfile.addValues( values )
  
  #//=======================================================//
  
  def   targets( self ):
    return self.target_values
  
  #//=======================================================//
  
  def   sideEffects( self ):
    return self.itarget_values
  
  #//=======================================================//
  
  def   addDeps( self, deps ):
    
    append_node = self.dep_nodes.add
    append_value = self.dep_values.append
    
    for dep in toSequence( deps ):
      if isinstance(dep, Node):
        append_node( dep )
      elif isinstance(dep, Value):
        append_value( dep )
      else:
        raise UnknownNodeDependencyType( self, dep )
  
  #//-------------------------------------------------------//
  
  def   __friendlyName( self ):
    
    many_sources = False
    
    try:
      source_values = self.source_values
      
      if not self.source_values:
        source_values = self.sources()
        many_sources = (len(source_values) > 1)
      else:
        many_sources = (len(source_values) > 1)
        if not many_sources:
          if self.source_nodes:
            many_sources = True
      
      if source_values:
        first_source = min( source_values, key = lambda v: v.name ).name
      else:
        first_source = []
      
    except AttributeError:
      return None
    
    name = str( self.builder.long_name ) + ': '
    if many_sources:
      name += '[' + str(first_source) + ' ...]'
    else:
      name += str(first_source)
    
    return name
  
  #//-------------------------------------------------------//
  
  def   __str__(self):
    
    name = self.__friendlyName()
    if name is not None:
      return name
    
    depth = 0
    long_name = []
    
    node = self
    
    while True:
      node = next(iter(node.source_nodes))
      
      long_name.append( str( node.builder.long_name ) + ': ['  )
      depth += 1
      
      first_source = node.__friendlyName()
      if first_source is not None:
        long_name.append( first_source )
        break
    
    long_name += [']'] * depth
    
    # g++: [ moc: [ m4: src1.m4 ... ] ]
    
    return ' '.join( long_name )
  
  #//-------------------------------------------------------//
  
  def   __repr__(self):
    return str( self.long_name )
