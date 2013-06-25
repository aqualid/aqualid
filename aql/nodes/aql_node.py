#
# Copyright (c) 2011-2013 The developers of Aqualid project - http://aqualid.googlecode.com
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

__all__ = (
  'Node',
)

import hashlib

from aql.types import toSequence
from aql.values import Value, SignatureValue, NoContent, DependsValue, DependsValueContent

#//===========================================================================//

class Node (object):
  
  __slots__ = \
  (
    'builder',
    'builder_data',
    
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
  
  def   __init__( self, builder, source_nodes, source_values ):
    
    self.builder = builder
    self.builder_data = None
    self.source_nodes = frozenset( toSequence( source_nodes ) )
    self.source_values = tuple( toSequence( source_values ) )
    self.dep_nodes = set()
    self.dep_values = []
  
  #//=======================================================//
  
  def   depends( self, dep_nodes, dep_values ):
    self.dep_nodes.update( toSequence( dep_nodes ) )
    self.dep_values += toSequence( dep_values )
  
  #//=======================================================//
  
  def   split( self, builder ):
    nodes = []
    
    dep_nodes = self.dep_nodes
    dep_values = self.dep_values
    for src_value in self.sources():
      node = Node( builder, None, src_value )
      node.dep_nodes = dep_nodes
      node.dep_values = dep_values
      nodes.append( node )
    
    return nodes
  
  #//=======================================================//
  
  def   __setValues( self ):
    
    names = [ self.builder.name.encode('utf-8') ]
    sign  = [ self.builder.signature ]
    
    sources = self.sources()
    names += ( value.name.encode('utf-8') for value in sources )
    
    #names += sorted( map( lambda value: value.name.encode('utf-8'), self.source_values ) )
    #names += sorted( map( lambda node: node.sources_value.name, self.source_nodes ) )
    
    sign += ( value.content.signature for value in sources )
    
    deps = self.dependencies()
    
    sign += ( value.name.encode('utf-8') for value in deps )
    sign += ( value.content.signature for value in deps )
    
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
    
    self.sources_value = SignatureValue( name_key, signature )
    
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
    
    raise AttributeError( "%s instance has no attribute '%s'" % (type(self), attr) )
  
  #//=======================================================//
  
  def   values( self ):
    
    values = [ self.sources_value, self.targets_value, self.itargets_value, self.ideps_value ]
    
    targets = self.targets_value.content.data
    if targets: values += targets
    
    itargets = self.itargets_value.content.data
    if itargets: values += itargets
    
    ideps = self.ideps_value.content.data
    if ideps: values += ideps
    
    return values
  
  #//=======================================================//
  
  def   load( self, vfile ):
    
    values = [ self.targets_value, self.itargets_value, self.ideps_value ]
    values = vfile.findValues( values )
    
    self.targets_value, self.itargets_value, self.ideps_value = values
  
  #//=======================================================//
  
  def   actual( self, vfile  ):
    
    values = [ self.sources_value, self.targets_value, self.itargets_value, self.ideps_value ]
    values = vfile.findValues( values )
    
    if self.sources_value != values.pop(0):
      return False
    
    for value in values:
      if not value.actual():
        return False
    
    self.targets_value, self.itargets_value, self.ideps_value = values
    
    return True
  
  #//=======================================================//
  
  def   sources(self):
    values = []
    
    for node in self.source_nodes:
      values += node.targets()
    
    values += self.source_values
    
    values.sort( key = lambda v: v.name )
    
    return values
  
  #//=======================================================//
  
  def   dependencies(self):
    values = []
    
    for node in self.dep_nodes:
      values += toSequence( node.targets_value.content.data )
    
    values += self.dep_values
    
    values.sort( key = lambda v: v.name )
    
    return values
  
  #//=======================================================//
  
  def   targets(self):
    targets = self.targets_value.content.data
    return targets if targets else tuple()
  
  #//=======================================================//
  
  def   sideEffects(self):
    itargets = self.itargets_value.content.data
    return itargets if itargets else tuple()
  
  #//=======================================================//
  
  def   setTargets( self, targets, itargets = None, ideps = None ):
    
    makeValues = self.builder.makeValues
    
    target_values = makeValues( targets, use_cache = False )
    itarget_values = makeValues( itargets, use_cache = False )
    idep_values = makeValues( ideps, use_cache = True )
    
    self.targets_value.content = DependsValueContent( target_values )
    self.itargets_value.content = DependsValueContent( itarget_values )
    self.ideps_value.content = DependsValueContent( idep_values )
  
  #//-------------------------------------------------------//
  
  def   _friendlyName( self ):
    
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
    
    name = self._friendlyName()
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
        
      first_source = node._friendlyName()
      if first_source is not None:
        name.append( first_source )
        break
      
    name += [']'] * depth
    
    # g++: [ moc: [ m4: src1.m4 ... ] ]
    
    return ' '.join( name )
  
  #//-------------------------------------------------------//
  
  def   buildStr( self ):
    return self.builder.buildStr( self )
