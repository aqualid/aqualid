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
from aql_errors import UnknownSourceValueType, UnknownAttribute, InvalidNodeTarget, InvalidNodeTargetsType
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
  __slots__ = ( 'target_values', 'itarget_values', 'idep_values' )
  
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
    
    'target_values',
    'itarget_values',
    'idep_values',
    
    'name_key',
    'targets_key',
    'itargets_key',
    'ideps_key',
    
    'signature',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, builder, sources ):
    
    self.builder = builder
    self.source_nodes= set()
    self.source_values = []
    self.source_nodes, self.source_values = self._getSourceNodes( sources )
    self.dep_values = []
    self.dep_nodes = set()
  
  #//=======================================================//
  
  def   _getSourceNodes( self, sources ):
    
    source_nodes = set()
    source_values = []
    
    source_nodes_append = source_nodes.add
    source_values_append = source_values.append
    
    to_value = self.builder.sourceValue
    
    for source in toSequence( sources ):
      if isinstance(source, Node):
        source_nodes_append( source )
      else:
        source_values_append( to_value( source ) )
    
    return source_nodes, tuple(source_values)
    
  #//=======================================================//
  
  def   depends( self, deps ):
    
    append_node = self.dep_nodes.add
    append_value = self.dep_values.append
    
    to_value = self.builder.sourceValue
    
    for dep in toSequence( deps ):
      if isinstance(dep, Node):
        append_node( dep )
      else:
        append_value( to_value(dep) )
  
  #//=======================================================//
  
  def   setTargets( self, node_targets ):
    if not isinstance( node_targets, NodeTargets ):
      raise InvalidNodeTargetsType( node_targets )
    
    self.target_values = tuple( node_targets.target_values )
    self.itarget_values = tuple( node_targets.itarget_values )
    self.idep_values = tuple( node_targets.idep_values )
  
  #//=======================================================//
  
  def   __setNameAndSignature( self ):
    
    names = [ self.builder.name.encode('utf-8') ]
    sign = [ self.builder.signature ]
    
    sources = self.sources()
    
    names += map( lambda value: value.name.encode('utf-8'), sources )
    sign += map( lambda value: value.signature, sources )
    
    deps = self.dependencies()
    
    sign += map( lambda value: value.name.encode('utf-8'), deps )
    sign += map( lambda value: value.signature, deps )
    
    #//-------------------------------------------------------//
    #// Signature
    
    sign_hash = hashlib.md5()
    for s in sign:
      sign_hash.update( s )
    
    self.signature = sign_hash.digest()
    
    #//-------------------------------------------------------//
    #// Name key
    name_hash = hashlib.md5()
    for s in names:
      name_hash.update( s )
    
    self.name_key = name_hash.digest()
    
    #//-------------------------------------------------------//
    #// Target keys
    
    name_hash.update( b'target_values' )
    self.targets_key = name_hash.digest()
   
    name_hash.update( b'itarget_values' )
    self.itargets_key = name_hash.digest()
    
    name_hash.update( b'idep_values' )
    self.ideps_key = name_hash.digest()
  
  #//=======================================================//
  
  def   __getattr__( self, attr ):
    if attr in ('name_key', 'targets_key', 'itargets_key', 'ideps_key', 'signature'):
      self.__setNameAndSignature()
      return getattr(self, attr)
    
    raise AttributeError( self, attr )
  
  #//=======================================================//
  
  def   save( self, vfile, node_targets = None ):
    
    if node_targets is not None:
      self.setTargets( node_targets )
    
    values = [ Value( self.name_key, self.signature ) ]
    
    values += self.target_values
    values += self.itarget_values
    values += self.idep_values
    
    values.append( DependsValue( self.targets_key,  self.target_values )  )
    values.append( DependsValue( self.itargets_key, self.itarget_values ) )
    values.append( DependsValue( self.ideps_key,    self.idep_values )    )
    
    vfile.addValues( values )
  
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
    
    sources_value = Value( self.name_key, self.signature )
    
    targets_value   = DependsValue( self.targets_key   )
    itargets_value  = DependsValue( self.itargets_key  )
    ideps_value     = DependsValue( self.ideps_key     )
    
    values = [ sources_value, targets_value, itargets_value, ideps_value ]
    values = vfile.findValues( values )
    
    if sources_value != values.pop(0):
      return False
    
    for value in values:
      if not value.actual( use_cache ):
        return False
    
    targets_value, itargets_value, ideps_value = values
    
    self.target_values  = targets_value.content
    self.itarget_values = itargets_value.content
    self.idep_values    = ideps_value.content
    
    return True
  
  #//=======================================================//
  
  def   sources(self):
    values = []
    
    for node in self.source_nodes:
      values += node.target_values
    
    values += self.source_values
    
    values.sort( key = lambda v: v.name )
    
    return values
  
  #//=======================================================//
  
  def   dependencies(self):
    values = []
    
    for node in self.dep_nodes:
      values += node.target_values
    
    values += self.dep_values
    
    values.sort( key = lambda v: v.name )
    
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
    try:
      values = [ DependsValue( self.targets_key ), DependsValue( self.itargets_key ) ]
    except AttributeError:
      return False
    
    targets_value, itargets_value = vfile.findValues( values )
    target_values = targets_value.content
    itarget_values = itargets_value.content
    
    self.target_values = target_values
    self.itarget_values = itarget_values
    
    if isinstance( target_values, NoContent ):
      target_values = tuple()
      result = False
    else:
      result = True
    
    if isinstance( itarget_values, NoContent ):
      itarget_values = tuple()
    
    if itarget_values or target_values:
      self.builder.clear( self, target_values, itarget_values )
      
      values = []
      values += target_values
      values += itarget_values
      
      no_content = NoContent()
      for value in values:
        value.content = no_content
      
      vfile.addValues( values )
    
    return result
  
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
      name.append( str( node.builder ) + ': ['  )
      depth += 1
      
      try:
        node = next(iter(node.source_nodes))
      except StopIteration:
        break
        
      first_source = node.__friendlyName()
      if first_source is not None:
        name.append( first_source )
        break
      
    name += [']'] * depth
    
    # g++: [ moc: [ m4: src1.m4 ... ] ]
    
    return ' '.join( name )
