
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

import itertools

from aql.utils import newHash, dumpData
from aql.util_types import toSequence

from aql.values import Value, NoContent, ContentBase, pickleable

#//===========================================================================//

class   ErrorNodeDependencyInvalid( Exception ):
  def   __init__( self, dep ):
    msg = "Invalid node dependency: %s" % (dep,)
    super(ErrorNodeDependencyInvalid, self).__init__( msg )

class   ErrorNoTargets( Exception ):
  def   __init__( self, node ):
    msg = "Node targets are not built yet: %s" % (node.buildStr())
    super(ErrorNoTargets, self).__init__( msg )

class   ErrorNoImplicitDeps( Exception ):
  def   __init__( self, node ):
    msg = "Node implicit dependencies are not built yet: %s" % (node.buildStr())
    super(ErrorNoTargets, self).__init__( msg )

#//===========================================================================//

@pickleable
class   NodeContent( ContentBase ):
  
  __slots__ = (
                'sources_sign',
                'targets',
                'itargets',
                'ideps',
              )
  
  def   __new__( cls, sources_sign, targets = None, itargets = None, ideps = None ):
    
    if isinstance(sources_sign, ContentBase):
      return sources_sign
    
    self = super(NodeContent,cls).__new__(cls)
    
    self.sources_sign = sources_sign
    self.targets = targets
    self.itargets = itargets
    self.ideps = ideps
    
    return self
  
  #//-------------------------------------------------------//
  
  def   __bool__( self ):
    return True
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other ):
    if type(self) != type(other):
      # if __debug__:
      #   print("NodeContent.eq(): Different type: %s" % type(other) )
      return False
    
    if (not self.sources_sign) or (self.sources_sign != other.sources_sign):
      # if __debug__:
      #   print("NodeContent.eq(): Changed sources signature" )
      return False
    
    for targets, other_targets in ((self.targets,other.targets),(self.itargets,other.itargets),(self.ideps,other.ideps) ):
      if (not targets) or (targets != other_targets):
        # if __debug__:
        #   print("NodeContent.eq(): Changed targets" )
        return False
    
    return True
  
  #//-------------------------------------------------------//
  
  def   actual(self, other ):
    
    if type(self) != type(other):
      # if __debug__:
      #   print("NodeContent.actual(): Wrong type: %s" % type(other) )
      return False
    
    if (not self.sources_sign) or (self.sources_sign != other.sources_sign):
      # if __debug__:
      #   print("NodeContent.actual(): Changed sources signature" )
      return False
    
    if (self.targets is None) or (self.itargets is None) or (self.ideps is None):
      # if __debug__:
      #   print("NodeContent.actual(): No targets yet." )
      return False
    
    for value in itertools.chain( self.targets, self.itargets, self.ideps ):
      if not value.actual():
        # if __debug__:
        #   print( "NodeContent.actual(): Changed target value: %s" % (value, ) )
        return False
    
    return True
  
  #//-------------------------------------------------------//
  
  def   remove(self):
    
    targets = itertools.chain( toSequence( self.targets ), toSequence( self.itargets ) )
    
    for value in targets:
      value.remove()
  
  #//-------------------------------------------------------//
  
  def   __getnewargs__(self):
    return self.sources_sign, self.targets, self.itargets, self.ideps

#//===========================================================================//

@pickleable
class   NodeValue (Value):
  
  def   get(self):
    return self.name

  #//-------------------------------------------------------//

  def   actual( self, other ):
    content = self.content
    if not content:
      return False
    
    return content.actual( other.content )
  
  #//-------------------------------------------------------//
  
  def   remove( self ):
    if self.content:
      self.content.remove()

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class Node (object):
  
  __slots__ = \
  (
    'builder',
    'builder_data',
    
    '_sources',
    'source_values',
    'dep_nodes',
    'dep_values',
    
    'node_value',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, builder, sources ):
    
    self.builder = builder
    self.builder_data = None
    self._sources = toSequence( sources )
    self.dep_nodes = set()
    self.dep_values = []
  
  #//=======================================================//
  
  def   depends( self, dependencies ):
    
    for value in toSequence( dependencies ):
      if isinstance( value, Node ):
        self.dep_nodes.add( value )
      
      elif isinstance( value, Value ):
        self.dep_values.append( value )
      
      else:
        raise ErrorNodeDependencyInvalid( value )
  
  #//=======================================================//
  
  def   split( self, builder ):
    nodes = []
    
    dep_nodes = self.dep_nodes
    dep_values = self.dep_values
    for src_value in self.sourceValues():
      node = Node( builder, src_value )
      node.dep_nodes = dep_nodes
      node.dep_values = dep_values
      nodes.append( node )
    
    return nodes
  
  #//=======================================================//
  
  def   __setValue( self ):
    
    names = [ self.builder.name ]
    sign  = [ self.builder.signature ]
    
    # if __debug__:
    #   print( "builder name: '%s', signature: '%s'" % (names, sign) )
    
    sources = sorted( self.sourceValues(), key = lambda v: v.name )
    
    for value in sources:
      names.append( value.name )
      if sign is not None:
        content = value.content
        if content:
          sign.append( content.signature )
        else:
          sign = None
    
    deps = self.dependencies()
    
    if sign is not None:
      for value in deps:
        content = value.content
        if content:
          sign.append( value.name )
          sign.append( content.signature )
        else:
          sign = None
          break
    
    #//-------------------------------------------------------//
    #// Signature
    
    if sign is not None:
      sign_hash = newHash()
      sign_dump = dumpData( sign )
      sign_hash.update( sign_dump )
      sign = sign_hash.digest()
    
    #//-------------------------------------------------------//
    #// Name key
    name_hash = newHash()
    names_dump = dumpData( names )
    name_hash.update( names_dump )
    
    self.node_value = node_value = NodeValue( name = name_hash.digest(), content = NodeContent( sources_sign = sign ) )
    
    # if __debug__:
    #   print("Node.__setValue: name: %s (%s)" % (node_value.name, self) )
    
    return node_value
    
  #//=======================================================//
  
  def   __getattr__( self, attr ):
    if attr == 'node_value':
      return self.__setValue()
    
    if attr == 'source_values':
      self.source_values = source_values = self.__getSourceValues()
      return source_values
    
    raise AttributeError( "%s instance has no attribute '%s'" % (type(self), attr) )
  
  #//=======================================================//
  
  def   name(self):
    return self.node_value.name
  
  #//=======================================================//
  
  def   values( self ):
    return [ self.node_value ]
  
  #//=======================================================//
  
  def   load( self, vfile ):
    self.node_value = vfile.findValues( self.node_value )[0]
  
  #//=======================================================//
  
  def   actual( self, vfile  ):
    
    node_value = vfile.findValues( self.node_value )[0]
    
    if not node_value:
      # if __debug__:
      #   print( "no previous info of node: %s" % (self.name(),))
      return False
    
    if not node_value.actual( self.node_value ):
      return False
    
    self.node_value = node_value
    return True
    
  #//=======================================================//
  
  def   __getSourceValues(self):
    values = []
    
    makeValue = self.builder.makeValue
    
    for src in self._sources:
      
      if isinstance( src, Node ):
        values += src.targets()
      
      elif isinstance( src, Value ):
        values.append( src )
      
      else:
        values.append( makeValue( src, use_cache = True ) )
      
    return tuple(values)
  
  #//=======================================================//
  
  def   sources(self):
    return tuple( src.get() for src in self.source_values )
  
  def   sourceValues(self):
    return self.source_values
  
  def   sourceNodes(self):
    return tuple( node for node in self._sources if isinstance(node,Node) )
  
  #//=======================================================//
  
  def   dependencies(self):
    values = []
    
    for node in self.dep_nodes:
      values += toSequence( node.targets() )
    
    values += self.dep_values
    
    values.sort( key = lambda v: v.name )
    
    return values
  
  #//=======================================================//
  
  def   _getTargets(self, attr, error ):
    content = self.node_value.content
    if not content:
      raise error( self )
    
    targets = getattr(content, attr )
    if targets is None:
      raise error( self )
    
    return targets
  
  #//=======================================================//
  
  def   targets(self):
    return self._getTargets( attr = 'targets', error = ErrorNoTargets )
  
  def   sideEffects(self):
    return self._getTargets( attr = 'itargets', error = ErrorNoTargets )
  
  def   implicitDependencies(self):
    return self._getTargets( attr = 'ideps', error = ErrorNoImplicitDeps )
  
  #//=======================================================//
  
  def   setTargets( self, targets, itargets = None, ideps = None, valuesMaker = None ):
    
    if valuesMaker is None:
      valuesMaker = self.builder.makeValues
    
    node_content = self.node_value.content
    
    node_content.targets  = valuesMaker( targets,  use_cache = False )
    node_content.itargets = valuesMaker( itargets, use_cache = False )
    node_content.ideps    = valuesMaker( ideps,    use_cache = False )
  
  #//=======================================================//
  
  def   setFileTargets( self, targets, itargets = None, ideps = None ):
    self.setTargets( targets = targets, itargets = itargets, ideps = ideps,
                     valuesMaker = self.builder.makeFileValues )
  
  #//-------------------------------------------------------//
  
  def   buildStr( self ):
    return self.builder.buildStr( self )
