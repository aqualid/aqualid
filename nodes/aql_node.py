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
from aql_errors import UnknownNodeSourceType, UnknownAttribute, UnknownNodeDependencyType, InvalidNodeTarget
from aql_value import Value, NoContent
from aql_depends_value import DependsValue
from aql_utils import toSequence

#//---------------------------------------------------------------------------//

def   _toValues( values ):
  
  dst_values = []
  
  for value in toSequence( values ):
    if not isinstance( value, Value ):
      raise InvalidNodeTarget( value )
    dst_values.append( value )
  
  return dst_values

#//---------------------------------------------------------------------------//

class NodeTargets (object):
  __slots__ = ( 'targets', 'itargets', 'ideps' )
  
  def   __init__( self, targets = None, itargets = None, ideps = None ):
    self.target_values  = _toValues( targets )
    self.itarget_values = _toValues( itargets )
    self.idep_values    = _toValues( ideps )
  
  def   __iadd__(self, other):
    if not isinstance( other, NodeTargets ):
      raise InvalidNodeTargetsType( other )
    
    self.target_values  += other.target_values
    self.itarget_values += other.itarget_values
    self.idep_values    += other.idep_values
    
    return self

#//---------------------------------------------------------------------------//

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
    
    'name_key',
    'targets_key',
    'itargets_key',
    'ideps_key',
    
    'signature',
    'is_actual',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, builder, sources ):
    
    self.builder = builder
    self.source_nodes, self.source_values = self._getSourceNodes( sources )
    self.dep_values = []
    self.dep_nodes = set()
    self.is_actual = None
  
  #//=======================================================//
  
  def   _getSourceNodes( self, sources ):
    
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
  
  def   depends( self, deps ):
    
    self.is_actual = None
    
    append_node = self.dep_nodes.add
    append_value = self.dep_values.append
    
    for dep in toSequence( deps ):
      if isinstance(dep, Node):
        append_node( dep )
      elif isinstance(dep, Value):
        append_value( dep )
      else:
        raise UnknownNodeDependencyType( self, dep )
  
  #//=======================================================//
  
  def   setTargets( self, node_targets ):
    if not isinstance( other, NodeTargets ):
      raise InvalidNodeTargetsType( other )
    
    self.is_actual = None
    
    self.target_values = tuple( node_targets.target_values )
    self.itarget_values = tuple( node_targets.itarget_values )
    self.idep_values = tuple( node_targets.ideps_values )
  
  #//=======================================================//
  
  def   __getName( self ):
    names = [ self.builder.name.encode('utf-8') ]
    names += sorted( map( lambda value: value.name.encode('utf-8'), self.source_values ) )
    names += sorted( map( lambda node: node.name_key, self.source_nodes ) )
    
    return names
  
  #//=======================================================//
  
  def   __keys( self ):
     chcksum = hashlib.md5()
     
     for name in self.__getName():
       chcksum.update( name )
     
     name_key = chcksum.digest()
     
     chcksum.update( b'target_values' )
     targets_key = chcksum.digest()
     
     chcksum.update( b'itarget_values' )
     itargets_key = chcksum.digest()
     
     chcksum.update( b'idep_values' )
     ideps_key = chcksum.digest()
     
     return name_key, targets_key, itargets_key, ideps_key

  #//=======================================================//
  
  def   __signature( self ):
    
    sign = [ self.builder.signature ]
    
    def _addSign( values, sign = sign ):
      sign += map( lambda value: value.signature, sorted( values, key = lambda value: value.name) )
    
    def _addSignAndName( values, sign_append = sign.append ):
      for value in sorted( values, key = lambda value: value.name ):
        sign_append( value.name.encode('utf-8') )
        sign_append( value.signature )
    
    _addSign( self.source_values )
    
    for node in self.source_nodes:
      _addSignAndName( node.target_values )
    
    _addSignAndName( self.dep_values )
    
    for node in self.dep_nodes:
      _addSignAndName( node.target_values )
    
    hash = hashlib.md5()
    for s in sign:
      hash.update( s )
    
    return hash.digest()
  
  #//=======================================================//
  
  def   __getattr__( self, attr ):
    if attr in ('name_key', 'targets_key', 'itargets_key', 'ideps_key'):
      self.name_key, self.targets_key, self.itargets_key, self.ideps_key, = self.__keys()
      return getattr(self, attr)
    
    if attr == 'signature':
      self.signature = self.__signature()
      return self.signature
    
    raise AttributeError( self, attr )
  
  #//=======================================================//
  
  def   save( self, vfile, node_targets = None ):
    
    if node_targets is not None:
      self.setTargets( node_targets )
    
    values = [ Value( self.name_key, self.signature ) ]
    
    values += idep_values
    values += target_values
    values += itarget_values
    
    values.append( DependsValue( self.targets_key,  self.target_values )  )
    values.append( DependsValue( self.itargets_key, self.itarget_values ) )
    values.append( DependsValue( self.ideps_key,    self.idep_values )    )
    
    vfile.addValues( values )
    
    self.is_actual = True
  
  #//=======================================================//
  
  def   prebuild( self, vfile ):
    return self.builder.prebuild( vfile, self )
  
  #//=======================================================//
  
  def   build( self, build_manager, vfile, prebuild_nodes = None ):
    
    event_manager.eventBuildingNode( self )
    
    args = [ build_manager, vfile, self ]
    if prebuild_nodes:
      args.append( prebuild_nodes )
    
    node_targets = self.builder.build( *args )
    self.save( vfile, node_targets )
    
    event_manager.eventBuildingNodeFinished( self )
  
  #//=======================================================//
  
  def   actual( self, vfile, use_cache = True ):
    
    if self.is_actual is not None:
      return self.is_actual
    
    self.is_actual = None
    
    sources_value = Value( self.name_key, self.signature )
    
    targets_value   = DependsValue( self.targets_key   )
    itargets_value  = DependsValue( self.itargets_key  )
    ideps_value     = DependsValue( self.ideps_key     )
    
    values = [ sources_value, targets_value, itargets_value, ideps_value ]
    values = vfile.findValues( values )
    
    if sources_value != values.pop(0):
      self.is_actual = False
      return False
    
    for value in values:
      if not value.actual( use_cache ):
        self.is_actual = False
        return False
    
    targets_value, itargets_value, ideps_value = values
    
    self.target_values  = targets_value.content
    self.itarget_values = itargets_value.content
    self.idep_values    = ideps_value.content
    
    self.is_actual = True
    return True
  
  #//=======================================================//
  
  def   sources(self):
    values = list(self.source_values)
    for node in self.source_nodes:
      values += node.target_values
    
    return values
  
  #//=======================================================//
  
  def   targets(self):
    return self.target_values
  
  #//=======================================================//
  
  def   sideEffects(self):
    return self.itarget_values
  
  #//=======================================================//
  
  def   nodeTargets(self):
    return NodeTargets( self.target_values, self.itarget_values, self.idep_values )
  
  #//=======================================================//
  
  def   clear( self, vfile ):
    
    self.is_actual = None
    
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
  
  #//-------------------------------------------------------//
  
  def   __friendlyName( self ):
    
    many_sources = False
    
    try:
      source_values = self.source_values
      
      if not source_values:
        return None
      
      many_sources = (len(source_values) > 1)
      if not many_sources:
        if self.source_nodes:
          many_sources = True
      
      first_source = min( source_values, key = lambda v: v.name ).name
    
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
