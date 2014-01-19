
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

from aql.values import Value, DependsValue, DependsValueContent, ContentBase, pickleable

#//===========================================================================//

class   ErrorNodeDependencyInvalid( Exception ):
  def   __init__( self, dep ):
    msg = "Invalid node dependency: %s" % (dep,)
    super(ErrorNodeDependencyInvalid, self).__init__( msg )

class   ErrorNoTargets( Exception ):
  def   __init__( self, node ):
    msg = "Node targets are not built yet: %s" % (node.getBuildStr( detailed = True ))
    super(ErrorNoTargets, self).__init__( msg )

class   ErrorNoImplicitDeps( Exception ):
  def   __init__( self, node ):
    msg = "Node implicit dependencies are not built yet: %s" % (node.getBuildStr( detailed = True ))
    super(ErrorNoImplicitDeps, self).__init__( msg )

#//===========================================================================//

@pickleable
class   NodeContent( ContentBase ):
  
  __slots__ = (
                'sources_sign',
                'targets',
                'itargets',
              )
  
  def   __new__( cls, sources_sign, targets = None, itargets = None ):
    
    if isinstance(sources_sign, ContentBase):
      return sources_sign
    
    self = super(NodeContent,cls).__new__(cls)
    
    self.sources_sign = sources_sign
    self.targets = targets
    self.itargets = itargets
    
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
    
    for targets, other_targets in ((self.targets,other.targets),(self.itargets,other.itargets)):
      if (targets is None) or (targets != other_targets):
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
    
    if (self.targets is None) or (self.itargets is None):
      # if __debug__:
      #   print("NodeContent.actual(): No targets yet." )
      return False
    
    for value in itertools.chain( self.targets, self.itargets ):
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
    return self.sources_sign, self.targets, self.itargets

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
    'ideps_value',
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
    
    dep_values = self.getDepValues()
    for src_value in self.getSourceValues():
      node = Node( builder, src_value )
      node.dep_values = dep_values
      nodes.append( node )
    
    return nodes
  
  #//=======================================================//
  
  def   initiate(self):
    self.builder = self.builder.initiate()
    self.__setSourceValues()
    self.__setValues()
    
  #//=======================================================//
  
  def   __setValues( self ):
    
    sources = sorted( self.getSourceValues(), key = lambda v: v.name )
    
    #//-------------------------------------------------------//
    #// Get Node name
    
    names = self.builder.getTargets( self )
    if names:
      names = sorted( (value.name,type(value)) for value in names )
    else:
      names = [ self.builder.name ]
      names += [ value.name for value in sources ]
      
    #//-------------------------------------------------------//
    #// Get Node signature

    sign  = [ self.builder.signature ]
    
    for value in sources:
      content = value.content
      if content:
        sign.append( content.signature )
      else:
        sign = None
        break
    
    if sign is not None:
      deps = self.getDepValues()
      
      for value in deps:
        content = value.content
        if content:
          sign.append( value.name )
          sign.append( content.signature )
        else:
          sign = None
          break
    
    # if __debug__:
    #   print( "builder name: '%s', signature: '%s'" % (names, sign) )
    
    #//-------------------------------------------------------//
    #// Signature key
    
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
    
    self.node_value = NodeValue( name = name_hash.digest(), content = NodeContent( sources_sign = sign ) )
    
    name_hash.update( b"ideps" )
    self.ideps_value = DependsValue( name = name_hash.digest() )
    
    # if __debug__:
    #   print("Node.__setValue: name: %s (%s)" % (node_value.name, self) )
    
  #//=======================================================//
  
  def   __setSourceValues(self):
    values = []
    
    makeValue = self.builder.makeValue
    
    for src in self._sources:
      
      if isinstance( src, Node ):
        values += src.getTargetValues()
      
      elif isinstance( src, Value ):
        values.append( src )
      
      else:
        values.append( makeValue( src, use_cache = True ) )
      
    self.source_values = tuple(values)
  
  #//=======================================================//
  
  def   getName(self):
    return self.node_value.name
  
  #//=======================================================//
  
  def   save( self, vfile ):
    values = [ self.ideps_value, self.node_value ]
    
    ideps = self.ideps_value.content.data
    if ideps:
      values += ideps
    
    vfile.addValues( values )
  
  #//=======================================================//
  
  def   load( self, vfile ):
    self.ideps_value, self.node_value = vfile.findValues( [ self.ideps_value, self.node_value ] )
  
  #//=======================================================//
  
  # noinspection PyMethodMayBeStatic
  def   clear( self, vfile ):
    """
    Cleans produced values
    """
    self.load( vfile )
    
    vfile.removeValues( [ self.node_value, self.ideps_value ] )
    
    self.builder.clear( self )
  
  #//=======================================================//
  
  def   removeTargets(self):
    self.node_value.remove()
  
  #//=======================================================//
  
  def   actual( self, vfile  ):
    
    ideps_value, node_value = vfile.findValues( [self.ideps_value, self.node_value] )
    
    if not node_value:
      # if __debug__:
      #   print( "no previous info of node: %s" % (self.getName(),))
      return False
    
    if not node_value.actual( self.node_value ):
      return False
    
    if not ideps_value.actual():
      # if __debug__:
      #   print( "ideps are not actual: %s" % (self.getName(),))
      return False
    
    self.node_value = node_value
    self.ideps_value = ideps_value
    
    return True
    
  #//=======================================================//
  
  def   getSources(self):
    return tuple( src.get() for src in self.source_values )
  
  def   getSourceValues(self):
    return self.source_values
  
  def   getSourceNodes(self):
    return tuple( node for node in self._sources if isinstance(node,Node) )
  
  #//=======================================================//
  
  def   getDepValues(self):
    values = []
    
    for node in self.dep_nodes:
      values += toSequence( node.getTargetValues() )
    
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
  
  def   get(self):
    return self.getTargets()
  
  #//=======================================================//
  
  def   getTargets(self):
    return tuple( target.get() for target in self.getTargetValues() )
  
  #//=======================================================//
  
  def   getTargetValues(self):
    return self._getTargets( attr = 'targets', error = ErrorNoTargets )
  
  def   getSideEffectValues(self):
    return self._getTargets( attr = 'itargets', error = ErrorNoTargets )
  
  #//=======================================================//
  
  def   setTargets( self, targets, itargets = None, ideps = None, valuesMaker = None ):
    
    if valuesMaker is None:
      valuesMaker = self.builder.makeValues
    
    node_content = self.node_value.content
    
    node_content.targets  = valuesMaker( targets,   use_cache = False )
    node_content.itargets = valuesMaker( itargets,  use_cache = False )
    ideps                 = valuesMaker( ideps,     use_cache = True )
    
    self.ideps_value.content = DependsValueContent( ideps )
    
  #//=======================================================//
  
  def   setFileTargets( self, targets, itargets = None, ideps = None ):
    self.setTargets( targets = targets, itargets = itargets, ideps = ideps,
                     valuesMaker = self.builder.makeFileValues )
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __makeArgsStr( args, detailed ):
    args = [ str(arg) for arg in toSequence(args) ]
    
    if detailed or (len(args) < 3):
      return ' '.join( args )
    
    wish_size = 128
    
    args_str = [ args.pop(0) ]
    last = args.pop()
    
    size = len(args_str[0]) + len(last)
    
    for arg in args:
      size += len(arg)
      
      if size > wish_size:
        args_str.append('...')
        break
      
    args_str.append( last )
    
    return ' '.join( args_str )
  
  #//-------------------------------------------------------//
  
  def   getBuildStr( self, detailed = False ):
    
    args = self.builder.getBuildStrArgs( self, detailed = detailed )
    
    name    = self.builder.__class__.__name__
    args    = iter(args)
    name    = next(args, self.builder.__class__.__name__ )
    sources = next(args, None )
    targets = next(args, None )
    
    name  = str(name)
    sources = self.__makeArgsStr( sources, detailed )
    targets = self.__makeArgsStr( targets, detailed )
    
    if sources:
      name += ": " + sources
    if targets:
      name += "-> " + targets
    
    return name
