#
# Copyright (c) 2011,2012 The developers of Aqualid project - http://aqualid.googlecode.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#


import hashlib

from aql_event_manager import event_manager
from aql_errors import UnknownNodeSourceType, UnknownAttribute, UnknownNodeDependencyType, InvalidBuilderResults
from aql_value import Value, NoContent
from aql_depends_value import DependsValue
from aql_utils import toSequence, isSequence

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
    'name_key',
    'targets_key',
    'itargets_key',
    'deps_key',
    'ideps_key',
    'builder_key',
    
    'sources_value',
    'deps_value',
    'builder_value',
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
  
  def   __getName( self ):
    names = list( toSequence( self.builder.name ) )
    names_append = names.append
    
    for source in self.source_nodes:
      names += source.name
    
    for source in self.source_values:
      names_append( source.name )
    
    names.sort()
    
    return names

  #//=======================================================//
  
  def   __getNameKeys( self ):
     chcksum = hashlib.md5()
     
     for name in self.name:
       chcksum.update( name.encode() )
     
     name_key = chcksum.digest()
     chcksum.update( b'target_values' )
     targets_key = chcksum.digest()
     
     chcksum.update( b'itarget_values' )
     itargets_key = chcksum.digest()
     
     chcksum.update( b'dep_values' )
     deps_key = chcksum.digest()
     
     chcksum.update( b'idep_values' )
     ideps_key = chcksum.digest()
     
     chcksum.update( b'builder_key' )
     builder_key = chcksum.digest()
     
     return name_key, targets_key, itargets_key, deps_key, ideps_key, builder_key
  
  #//=======================================================//
  
  def   __sourcesValue( self ):
    source_values = list(self.source_values)
    
    for node in self.source_nodes:
      source_values += node.target_values
    
    return DependsValue( self.name_key, source_values )
  
  #//=======================================================//
  
  def   __depsValue( self ):
    dep_values = list(self.dep_values)
    
    for node in self.dep_nodes:
      dep_values += node.target_values
    
    dep_values.append( self.builder_value )
    
    return DependsValue( self.deps_key, dep_values )
  
  #//=======================================================//
  
  def   __getattr__( self, attr ):
    if attr in ('name_key', 'targets_key', 'itargets_key', 'deps_key', 'ideps_key', 'builder_key'):
      self.name_key, self.targets_key, self.itargets_key, self.deps_key, self.ideps_key, self.builder_key = self.__getNameKeys()
      return getattr(self, attr)
    
    elif attr == 'name':
      name = self.__getName()
      self.name = name
      return name
    
    elif attr == 'sources_value':
      self.sources_value = self.__sourcesValue()
      return self.sources_value
    
    elif attr == 'deps_value':
      self.deps_value = self.__depsValue()
      return self.deps_value
    
    elif attr == 'builder_value':
      self.builder_value = Value( self.builder_key, self.builder.signature() )
      return self.builder_value
    
    raise UnknownAttribute( self, attr )
  
  #//=======================================================//
  
  def   __save( self, vfile ):
    
    values = [ self.builder_value ]
    values += self.source_values
    values += self.dep_values
    values += self.idep_values
    values += self.target_values
    values += self.itarget_values
    
    values.append( self.sources_value )
    values.append( self.deps_value )
    values.append( DependsValue( self.ideps_key,     self.idep_values )    )
    values.append( DependsValue( self.targets_key,   self.target_values )  )
    values.append( DependsValue( self.itargets_key,  self.itarget_values ) )
    
    vfile.addValues( values )
  
  #//=======================================================//
  
  def   __checkValues( self, values ):
    if not isSequence( values ):
      raise InvalidBuilderResults( self, values )
    
    for value in values:
      if not isinstance( value, Value ):
        raise InvalidBuilderResults( self, values )
  
  #//=======================================================//
  
  def   save( self, vfile, target_values, itarget_values, idep_values ):
    
    self.__checkValues( target_values )
    self.__checkValues( itarget_values )
    self.__checkValues( idep_values )
    
    self.target_values = target_values
    self.itarget_values = itarget_values
    self.idep_values = idep_values
    
    self.__save( vfile )
  
  #//=======================================================//
  
  def   _build( self, build_manager, vfile ):
    
    target_values, itarget_values, idep_values = self.builder.build( build_manager, vfile, self )
    
    self.__checkValues( target_values )
    self.__checkValues( itarget_values )
    self.__checkValues( idep_values )
    
    self.target_values = target_values
    self.itarget_values = itarget_values
    self.idep_values = idep_values
  
  #//=======================================================//
  
  def   build( self, build_manager, vfile ):
    
    event_manager.eventBuildingNode( self )
    
    self._build( build_manager )
    
    self.__save( vfile )
    
    event_manager.eventBuildingNodeFinished( self )
  
  #//=======================================================//
  
  def   actual( self, vfile ):
    sources_value = self.sources_value
    deps_value    = self.deps_value
    
    targets_value   = DependsValue( self.targets_key   )
    itargets_value  = DependsValue( self.itargets_key  )
    ideps_value     = DependsValue( self.ideps_key     )
    
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
  
  def   clear( self, vfile ):
    
    values = [ DependsValue( self.targets_key  ), DependsValue( self.itargets_key  ) ]
    
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
      
      if not source_values:
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
        first_source = ''
      
    except AttributeError:
      return None
    
    name = str( self.builder ) + ': '
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
    name = []
    
    node = self
    
    while True:
      node = next(iter(node.source_nodes))
      
      name.append( str( node.builder ) + ': ['  )
      depth += 1
      
      first_source = node.__friendlyName()
      if first_source is not None:
        name.append( first_source )
        break
    
    name += [']'] * depth
    
    # g++: [ moc: [ m4: src1.m4 ... ] ]
    
    return ' '.join( name )
  
  #//-------------------------------------------------------//
  
  def   __repr__(self):
    return str( self.name )
