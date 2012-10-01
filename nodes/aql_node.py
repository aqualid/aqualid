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
from aql_depends_value import DependsValue, DependsValueContent
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
    
    'sources_value',
    'targets_value',
    'itargets_value',
    'ideps_value',
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
    
    self.targets_value.content = DependsValueContent( node_targets.target_values )
    self.itargets_value.content = DependsValueContent( node_targets.itarget_values )
    self.ideps_value.content = DependsValueContent( node_targets.idep_values )
  
  #//=======================================================//
  
  def   __setValues( self ):
    
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
    
    signature = sign_hash.digest()
    
    #//-------------------------------------------------------//
    #// Name key
    name_hash = hashlib.md5()
    for s in names:
      name_hash.update( s )
    
    name_key = name_hash.digest()
    
    self.sources_value = Value( name_key, signature )
    
    #//-------------------------------------------------------//
    #// Targets
    
    name_hash.update( b'targets' )
    self.targets_value = DependsValue( name_hash.digest() )
    
    name_hash.update( b'itargets' )
    self.itargets_value = DependsValue( name_hash.digest() )
    
    name_hash.update( b'ideps' )
    self.ideps_value = DependsValue( name_hash.digest() )
  
  #//=======================================================//
  
  def   __getattr__( self, attr ):
    if attr in ('sources_value', 'targets_value', 'itargets_value', 'ideps_value'):
      self.__setValues()
      return getattr(self, attr)
    
    raise AttributeError( self, attr )
  
  #//=======================================================//
  
  def   save( self, vfile, node_targets = None ):
    
    if node_targets is not None:
      self.setTargets( node_targets )
    
    values = [ self.sources_value, self.targets_value, self.itargets_value, self.ideps_value ]
    
    values += self.targets_value.content
    values += self.itargets_value.content
    values += self.ideps_value.content
    
    vfile.addValues( values )
  
  #//=======================================================//
  
  def   prebuild( self, build_manager, vfile ):
    return self.builder.prebuild( build_manager, vfile, self )
  
  #//=======================================================//
  
  def   prebuildFinished( self, build_manager, vfile, prebuild_nodes ):
    self.builder.prebuildFinished( build_manager, vfile, self, prebuild_nodes )
  
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
  
  def   actual( self, vfile ):
    
    values = [ self.sources_value, self.targets_value, self.itargets_value, self.ideps_value ]
    values = vfile.findValues( values )
    
    if self.sources_value != values.pop(0):
      print("not actual sources: %s" % self )
      return False
    
    for value in values:
      if not value.actual():
        print("not actual targets: %s" % self )
        return False
    
    self.targets_value, self.itargets_value, self.ideps_value = values
    
    print("actual: %s" % self )
    
    return True
  
  #//=======================================================//
  
  def   sources(self):
    values = []
    
    for node in self.source_nodes:
      values += node.targets_value.content
    
    values += self.source_values
    
    #~ print("sources: values: %s" % str(list(map(str,values))))
    values.sort( key = lambda v: v.name )
    
    #~ print("sources: sorted values: %s" % str(list(map(str,values))))
    
    return values
  
  #//=======================================================//
  
  def   dependencies(self):
    values = []
    
    for node in self.dep_nodes:
      values += node.targets_value.content
    
    values += self.dep_values
    
    values.sort( key = lambda v: v.name )
    
    return values
  
  #//=======================================================//
  
  def   targets(self):
    return self.targets_value.content
  
  #//=======================================================//
  
  def   sideEffects(self):
    return self.itargets_value.content
  
  #//=======================================================//
  
  def   nodeTargets(self):
    return NodeTargets( self.targets_value.content, self.itargets_value.content, self.ideps_value.content )
  
  #//=======================================================//
  
  def   clear( self, vfile ):
    try:
      values = [ self.targets_value, self.itargets_value ]
    except AttributeError:
      return False
    
    targets_value, itargets_value = vfile.findValues( values )
    target_values = targets_value.content
    itarget_values = itargets_value.content
    
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
