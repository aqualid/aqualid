
# Copyright (c) 2011-2014 The developers of Aqualid project - http://aqualid.googlecode.com
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
  'Node', 'BatchNode',
)

import os
import binascii

from aql.utils import simpleObjectSignature, dumpSimpleObject, newHash, Chdir
from aql.util_types import toSequence, toString, isString, FilePath, AqlException

from aql.values import ValueBase, FileValueBase, pickleable

#//===========================================================================//

class   ErrorNodeDependencyInvalid( AqlException ):
  def   __init__( self, dep ):
    msg = "Invalid node dependency: %s" % (dep,)
    super(ErrorNodeDependencyInvalid, self).__init__( msg )
    
class   ErrorNoTargets( AqlException ):
  def   __init__( self, node ):
    msg = "Node targets are not built or set yet: %s" % (node.getBuildStr( brief = False ),)
    super(ErrorNoTargets, self).__init__( msg )

class   ErrorUnactualValue( AqlException ):
  def   __init__( self, value ):
    msg = "Target value is not actual: %s (%s)" % (value.name, type(value))
    super(ErrorUnactualValue, self).__init__( msg )

class   ErrorNoImplicitDeps( AqlException ):
  def   __init__( self, node ):
    msg = "Node implicit dependencies are not built or set yet: %s" % (node.getBuildStr( brief = False ),)
    super(ErrorNoImplicitDeps, self).__init__( msg )

class   ErrorNodeNotInitialized( AqlException ):
  def   __init__( self, node ):
    msg = "Node is not initialized yet: %s" % (node, )
    super(ErrorNodeNotInitialized, self).__init__( msg )

class   ErrorNodeUnknownSource( AqlException ):
  def   __init__( self, src_value ):
    msg = "Unknown source value: %s (%s)" % (src_value, type(src_value))
    super(ErrorNodeUnknownSource, self).__init__( msg )

#//===========================================================================//

def   _actualDeps( vfile, dep_keys ):
  if dep_keys:
    values = vfile.getValues( dep_keys )
    
    if values is None:
      # if __debug__:
      #   print( "ideps are None")
      return False
    
    for key, value in zip(dep_keys, values):
      if not value:
        # if __debug__:
        #   print( "idep '%s' is false" % (value,))
        return False
      
      actual_value = value.getActual()
      if value != actual_value:
        # if __debug__:
        #   print( "idep '%s' changed to '%s'" % (value, actual_value))
        vfile.replaceValue( key, actual_value )
        return False
  
  return True

#//===========================================================================//

def   _actualValues( values ):
  if values is None:
    return False
  
  for value in values:
    if not value.isActual():
      return False
      
  return True

#//===========================================================================//

def   _ensureActualValues( values ):
  for value in values:
    if not value.isActual():
      raise ErrorUnactualValue( value )

#//===========================================================================//

def   _getTraceArg( value, brief ):
  if isinstance( value, FileValueBase ):
    value = value.get()
    if brief:
      value = os.path.basename( value )
  
  elif isinstance( value, FilePath ):
    if brief:
      value = os.path.basename( value )
  
  elif isString( value ):
    value = value.strip()
    
    npos = value.find('\n')
    if npos != -1:
      value = value[:npos]
    
    max_len = 64 if brief else 256
    src_len = len(value)
    if src_len > max_len:
      value = "%s..." % value[:max_len]
  
  else:
    value = None
  
  return value

#//===========================================================================//

def   _joinArgs( values, brief ):
  
  args = []
  
  for arg in toSequence(values):
    arg = _getTraceArg(arg, brief )
    if arg:
      args.append( arg )
  
  if not brief or (len(args) < 3):
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
    
    args_str.append( arg )
    
  args_str.append( last )
  
  return ' '.join( args_str )

#//===========================================================================//

def   _getBuildStr( args, brief ):
    
    args = iter(args)
    
    name    = next(args, None)
    sources = next(args, None)
    targets = next(args, None)
    
    name    = _joinArgs( name,    brief )
    sources = _joinArgs( sources, brief )
    targets = _joinArgs( targets, brief )
    
    build_str  = name
    if sources:
      build_str += ": " + sources
    if targets:
      build_str += " => " + targets
    
    return build_str
  
#//===========================================================================//
  
def   _getClearStr( args, brief = True ):
  
  args    = iter(args)
  next(args, None ) # name
  next(args, None ) # sources
  targets = next(args, None )
  
  return _joinArgs( targets, brief )

#//===========================================================================//

@pickleable
class   NodeValue (ValueBase):
  
  __slots__ = (
    'targets',
    'itargets',
    'idep_keys',
  )
  
  #//-------------------------------------------------------//
  
  def   __new__( cls, name, signature = None, targets = None, itargets = None, idep_keys = None ):
    
    self = super(NodeValue,cls).__new__(cls, name, signature )
    
    self.targets    = targets
    self.itargets   = itargets
    self.idep_keys  = idep_keys
    
    return self
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other):
    return (type(self) == type(other)) and (self.__getnewargs__() == other.__getnewargs__())
  
  #//-------------------------------------------------------//
  
  def   get(self):
    return self.name
  
  #//-------------------------------------------------------//
  
  def     __getnewargs__(self):
    return self.name, self.signature, self.targets, self.itargets, self.idep_keys
  
  #//-------------------------------------------------------//
  
  def   __bool__( self ):
    return (self.signature is not None) and (self.targets is not None)
  
  #//-------------------------------------------------------//
  
  def   actual( self, vfile ):
    if not self.signature:
      # if __debug__:
      #   print( "No signature.")
      return False
    
    other = vfile.findValue( self )
    
    if other is None:
      # if __debug__:
      #   print( "Previous value '%s' has not been found." % (self.name,))
      return False
    
    if self.signature != other.signature:
      # if __debug__:
      #   print( "Sources signature is changed: %s - %s" % (self.signature, other.signature) )
      return False
    
    targets   = other.targets
    itargets  = other.itargets
    idep_keys = other.idep_keys
    
    if not _actualDeps( vfile, idep_keys ):
      # if __debug__:
      #   print( "ideps are not actual: %s" % (self.name,))
      return False
    
    if not _actualValues( targets ):
      # if __debug__:
      #   print( "targets are not actual: %s" % (self.name,))
      return False
    
    self.targets = targets
    self.itargets = itargets
    
    return True

  
  #//-------------------------------------------------------//

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class Node (object):
  
  __slots__ = \
  (
    'builder',
    'builder_data',
    'options',
    'cwd',
    
    'name',
    'signature',
    
    'sources',
    'source_values',
    
    'dep_nodes',
    'dep_values',
    
    'targets',
    'itargets',
    'ideps',
  )
  
  #//-------------------------------------------------------//
  
  def   __init__( self, builder, sources, cwd = None ):
    
    self.builder = builder
    self.options = getattr( builder, 'options', None )
    self.builder_data = None
    
    if cwd is None:
      self.cwd = os.path.abspath( os.getcwd() )
    else:
      self.cwd = cwd
    
    self.sources = toSequence( sources )
    self.source_values = None
    self.dep_nodes = set()
    self.dep_values = []

    self.name = None
    self.signature = None
    
    self.targets = None
    self.itargets = None
    self.ideps = None
  
  #//=======================================================//
  
  def   depends( self, dependencies ):
    
    dep_nodes = self.dep_nodes
    dep_values = self.dep_values
    
    for value in toSequence( dependencies ):
      if isinstance( value, Node ):
        dep_nodes.add( value )
      
      elif isinstance( value, ValueBase ):
        dep_values.append( value )
      
      else:
        raise ErrorNodeDependencyInvalid( value )
    
    dep_values.sort( key = lambda v: v.name )
  
  #//=======================================================//
  
  def   getDepNodes(self):
    return self.dep_nodes
  
  #//=======================================================//
  
  def   getDepValues(self):
    dep_nodes = self.dep_nodes
    dep_values = self.dep_values
    
    if not dep_nodes:
      return dep_values
    
    for node in dep_nodes:
      dep_values += node.getTargetValues()
    
    dep_nodes.clear()
    dep_values.sort( key = lambda v: v.name )
    
    return dep_values
  
  #//=======================================================//
  
  def   split( self, builder ):
    nodes = []
    
    cwd = self.cwd
    
    dep_values = self.getDepValues()
    for src_value in self.getSourceValues():
      node = Node( builder, src_value, cwd )
      node.dep_values = dep_values
      nodes.append( node )
    
    return nodes
  
  #//=======================================================//
  
  def   initiate(self):
    if self.source_values is None:
      self.builder = self.builder.initiate()
      self._setSourceValues()
      
      self._initId()
  
  #//=======================================================//
  
  def   _initId(self):
    self._setName()
    self._setSignature()
  
  #//=======================================================//
  
  def   _addDepsSignature( self, sign ):
    if sign is not None:
      deps = self.getDepValues()
      
      for value in deps:
        if value:
          sign.append( value.name )
          sign.append( value.signature )
        else:
          return None
    
    return sign
  
  #//=======================================================//
  
  def   _setName(self ):
    
    targets = self.builder.getTargetValues( self )
    if targets:
      self.targets = tuple( toSequence( targets ) )
      names = sorted( value.valueId() for value in targets )
    else:
      sources = sorted( self.getSourceValues(), key = lambda v: v.name )
      names = [ self.builder.name ]
      names += [ value.name for value in sources ]
    
    self.name = simpleObjectSignature( names )
  
  #//=======================================================//
  
  def   _setSignature( self ):
    
    sign  = [ self.builder.signature ]
    
    for value in self.getSourceValues():
      if value:
        sign.append( value.signature )
      else:
        sign = None
        break
    
    sign = self._addDepsSignature( sign )
    
    if sign is not None:
      sign = simpleObjectSignature( sign )
    
    self.signature = sign
  
  #//=======================================================//
  
  def   _setSourceValues(self):
    values = []
    
    makeValue = self.builder.makeValue
    
    with Chdir(self.cwd):
      for src in self.sources:
        
        if isinstance( src, Node ):
          values += src.getTargetValues()
        
        elif isinstance( src, ValueBase ):
          values.append( src )
        
        else:
          value = makeValue( src, use_cache = True )
          values.append( value )
      
    self.sources = None
    self.source_values = tuple(values)
  
  #//=======================================================//
  
  def   getSources(self):
    return tuple( src.get() for src in self.getSourceValues() )
  
  #//=======================================================//
  
  def   getSourceValues(self):
    if self.source_values is None:
      raise ErrorNodeNotInitialized( self )
    
    return self.source_values
  
  #//=======================================================//
  
  def   getSourceNodes(self):
    return tuple( node for node in self.sources if isinstance(node,Node) )
  
  #//=======================================================//
  
  def   shrink(self):
    self.cwd = None
    self.dep_nodes = None
    self.dep_values = None
    self.sources = None
    self.source_values = None
    
    self.name = None
    self.signature = None
    self.builder = None
    self.builder_data = None
    self.options = None
  
  #//=======================================================//
  
  def   getName(self):
    return binascii.hexlify( self.name )
  
  #//=======================================================//
  
  def   build(self):
    self.targets = None
    output = self.builder.build( self )
    
    if self.targets is None:
      raise ErrorNoTargets( self )
    
    return output
  
  #//=======================================================//
  
  def   prebuild(self):
    self.initiate()
    return self.builder.prebuild( self )
  
  #//=======================================================//
  
  def   prebuildFinished(self, prebuild_nodes ):
    return self.builder.prebuildFinished( self, prebuild_nodes )
  
  #//=======================================================//
  
  def   save( self, vfile ):
    
    targets = self.targets
    
    if __debug__:
      if targets is None:
        raise ErrorNoTargets( self )
    
    idep_keys = vfile.addValues( self.ideps )
    
    node_value = NodeValue( name = self.name, signature = self.signature,
                            targets = targets, itargets = self.itargets, idep_keys = idep_keys )
    
    vfile.addValue( node_value )
  
  #//=======================================================//
  
  def   clear( self, vfile ):
    """
    Cleans produced values
    """
    node_value = NodeValue( name = self.name )
    
    node_value = vfile.findValue( node_value )
    if node_value:
      targets = node_value.targets
      itargets = node_value.itargets
      
      if targets is not None:
        self.targets  = targets
        self.itargets = itargets
    
    vfile.removeValues( [ node_value ] )
    
    try:
      self.builder.clear( self )
    except Exception:
      pass
    
  #//=======================================================//
  
  def   isActual( self, vfile ):
    
    node_value = NodeValue( name = self.name, signature = self.signature )
    
    if not node_value.actual( vfile ):
      return False
    
    self.targets  = node_value.targets
    self.itargets = node_value.itargets
    
    return True
    
  #//=======================================================//
  
  def   setTargets( self, targets, itargets = None, ideps = None, valuesMaker = None ):
    
    if valuesMaker is None:
      valuesMaker = self.builder.makeValues
    
    self.targets  = valuesMaker( targets,   use_cache = False )
    self.itargets = valuesMaker( itargets,  use_cache = False )
    self.ideps    = valuesMaker( ideps,     use_cache = True )
    
    if __debug__:
      _ensureActualValues( self.targets )
      _ensureActualValues( self.ideps )
    
  #//=======================================================//
  
  def   setFileTargets( self, targets, itargets = None, ideps = None ):
    self.setTargets( targets = targets, itargets = itargets, ideps = ideps,
                     valuesMaker = self.builder.makeFileValues )
  
  #//=======================================================//
  
  def   setNoTargets( self ):
    self.setTargets( targets = None )
  
  #//=======================================================//
  
  def   get(self):
    return self.getTargets()
  
  #//=======================================================//
  
  def   getTargets(self):
    return tuple( target.get() for target in self.getTargetValues() )
  
  #//=======================================================//
  
  def   getTargetValues(self):
    targets = self.targets
    
    if __debug__:
      if targets is None:
        raise ErrorNoTargets( self )
    
    return targets 
  
  #//=======================================================//
  
  def   getSideEffectValues(self):
    targets = self.itargets
    if __debug__:
      if targets is None:
        raise ErrorNoTargets( self )
    
    return targets
  
  #//=======================================================//
  
  def   removeTargets(self):
    for value in self.getTargetValues():
      value.remove()
    
    for value in self.getSideEffectValues():
      value.remove()
  
  #//=======================================================//
  
  def   getBuildStr( self, brief = True ):
    args = self.builder.getBuildStrArgs( self, brief = brief, batch = False )
    return _getBuildStr( args, brief )
  
  #//=======================================================//
  
  def   getClearStr( self, brief = True ):
    args = self.builder.getBuildStrArgs( self, brief = brief, batch = False )
    return _getClearStr( args, brief )

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class BatchNode (Node):
  
  __slots__ = \
    (
      'node_values',
      'batch_source_values',
    )
  
  #//=======================================================//
  
  def   __init__( self, builder, sources, cwd = None ):
    super(BatchNode,self).__init__( builder, sources, cwd )
    
    self.node_values = None
    self.batch_source_values = None
  
  #//=======================================================//
  
  def   _initId(self):
    self.name = self.builder.name
    
    name_hash = newHash( dumpSimpleObject( self.name ) )
    sign_hash = self._setSignature()
    
    node_values = {}
    
    for src_value in self.source_values:
      name = simpleObjectSignature( src_value.name, name_hash )
      
      if sign_hash and src_value.signature:
        signature = simpleObjectSignature( src_value.signature, sign_hash )
      else:
        signature = None
      
      ideps = []
      node_values[ src_value ] = NodeValue( name, signature ), ideps
    
    self.node_values = node_values
      
  #//=======================================================//
  
  def   _setSignature( self ):
    
    sign  = [ self.builder.signature ]
    
    sign = self._addDepsSignature( sign )
    
    if sign is None:
      self.signature = None
      return None
    
    sign_hash = newHash( dumpSimpleObject( sign ) )
    self.signature = sign_hash.digest()
    
    return sign_hash
  
  #//=======================================================//
  
  def   _setSourceValues(self):
    super(BatchNode,self)._setSourceValues()
    self.batch_source_values = self.source_values
  
  #//=======================================================//
  
  def   getBatchSources(self):
    return tuple( src.get() for src in self.getBatchSourceValues() )
  
  #//=======================================================//
  
  def   getBatchSourceValues(self):
    if self.batch_source_values is None:
      raise ErrorNodeNotInitialized( self )
    
    return self.batch_source_values
  
  #//=======================================================//
  
  def   save( self, vfile ):
    
    for src_value in self.batch_source_values:
      node_value, ideps = self.node_values[ src_value ]
      if __debug__:
        if node_value.targets is None:
          raise ErrorNoTargets( self )
      
      node_value.idep_keys = vfile.addValues( ideps )
      
      # if __debug__:
      #   print("save node value: %s" % (node_value.name))
      
      vfile.addValue( node_value )
  
  #//=======================================================//
  
  def   clear( self, vfile ):
    targets = []
    itargets = []
    node_values = []
    
    for src_value in self.source_values:
      node_value, ideps = self.node_values[ src_value ]
      
      node_value = vfile.findValue( node_value )
      
      if node_value:
        node_values.append( node_value )
        
        if node_value.targets is not None:
          targets   += node_value.targets
          itargets  += node_value.itargets
              
    self.targets  = targets
    self.itargets = itargets
    
    vfile.removeValues( node_values )
    
    try:
      self.builder.clear( self )
    except Exception:
      pass
  
  #//=======================================================//
  
  def   build(self):
    output = self.builder.buildBatch( self )
    self.__populateTargets()
    
    return output
  
  #//=======================================================//
  
  def   __populateTargets( self ):
    targets   = []
    itargets  = []
    
    for src_value in self.source_values:
      node_value, ideps = self.node_values[ src_value ]
      node_targets = node_value.targets
      if node_targets is None:
        raise ErrorNoTargets( self )
      
      targets += node_targets
      itargets += node_value.itargets
    
    self.targets = tuple(targets)
    self.itargets = tuple(itargets)
  
  #//=======================================================//
  
  def   isActual( self, vfile ):
    
    if not self.signature:
      # if __debug__:
      #   print( "Sources signature is False" )
      return False
    
    changed_sources = []
    targets = []
    itargets = []
    
    for src_value in self.source_values:
      node_value, ideps = self.node_values[ src_value ]
    
      if not node_value.actual( vfile ):
        changed_sources.append( src_value )
      else:
        targets   += node_value.targets
        itargets  += node_value.itargets
    
    if changed_sources:
      self.batch_source_values = changed_sources
      return False
    
    self.targets  = targets
    self.itargets = itargets
    return True
  
  #//=======================================================//
  
  def   setTargets( self, targets, itargets = None, ideps = None, valuesMaker = None ):
    raise Exception( "setTargets() is not allowed for batch build." )
  
  #//=======================================================//
  
  def   split( self, builder ):
    raise Exception( "split() is not allowed for batch build." )
  
  #//=======================================================//
  
  def   setSourceTargets( self, src_value, targets, itargets = None, ideps = None, valuesMaker = None ):
    
    if valuesMaker is None:
      valuesMaker = self.builder.makeValues
    
    try:
      node_value, node_ideps = self.node_values[ src_value ]
    except KeyError:
      raise ErrorNodeUnknownSource( src_value )
    
    node_value.targets  = valuesMaker( targets,   use_cache = False )
    node_value.itargets = valuesMaker( itargets,  use_cache = False )
    ideps               = valuesMaker( ideps,     use_cache = True )
    
    if __debug__:
      _ensureActualValues( node_value.targets )
      _ensureActualValues( ideps )
    
    node_ideps[:] = ideps
    
  #//=======================================================//
  
  def   setNoTargets( self ):
    for src_value in self.batch_source_values:
      node_value, node_ideps = self.node_values[ src_value ]
      node_value.targets = tuple()
      node_value.itargets = tuple()
  
  #//=======================================================//
  
  def   setSourceFileTargets( self, src_value, targets, itargets = None, ideps = None ):
    self.setSourceTargets( src_value, targets = targets, itargets = itargets, ideps = ideps,
                     valuesMaker = self.builder.makeFileValues )
  
  #//=======================================================//
  
  def   getBatchTargetValues(self):
    targets = []
    
    for src_value in self.batch_source_values:
      node_value, ideps = self.node_values[ src_value ]
      node_targets = node_value.targets
      if node_targets:
        targets += node_targets
    
    return targets
  
  #//=======================================================//
  
  def   shrink(self):
    super( BatchNode, self).shrink()
    
    self.node_values = None
    self.batch_source_values = None

  #//=======================================================//
  
  def   getBuildStr( self, brief = True ):
    args = self.builder.getBuildStrArgs( self, brief = brief, batch = True )
    return _getBuildStr( args, brief )
  
  #//=======================================================//
  
  def   getClearStr( self, brief = True ):
    args = self.builder.getBuildStrArgs( self, brief = brief, batch = True )
    return _getClearStr( args, brief )
