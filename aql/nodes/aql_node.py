
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
  'Node', 'BatchNode', 'NodeTargetsFilter',
)

import os

from aql.utils import simpleObjectSignature, dumpSimpleObject, newHash, Chdir, eventStatus, logDebug, logInfo
from aql.util_types import toSequence, isString, FilePath, AqlException

from aql.values import ValueBase, FileValueBase, pickleable

#//===========================================================================//

class   ErrorNodeDependencyInvalid( AqlException ):
  def   __init__( self, dep ):
    msg = "Invalid node dependency: %s" % (dep,)
    super(ErrorNodeDependencyInvalid, self).__init__( msg )

class   ErrorNodeSplitUnknownSource( AqlException ):
  def   __init__( self, node, value ):
    msg = "Node '%s' can't be split to unknown source value: %s" % (node.getBuildStr( brief = False ), value )
    super(ErrorNodeSplitUnknownSource, self).__init__( msg )
    
class   ErrorNoTargets( AttributeError ):
  def   __init__( self, node ):
    msg = "Node targets are not built or set yet: %s" % (node.getBuildStr( brief = False ),)
    super(ErrorNoTargets, self).__init__( msg )

class   ErrorNoSrcTargets( AqlException ):
  def   __init__( self, node, src_value ):
    msg = "Source '%s' targets are not built or set yet: %s" % (src_value.get(), node.getBuildStr( brief = False ),)
    super(ErrorNoSrcTargets, self).__init__( msg )

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

@eventStatus
def   eventNodeStaleReason( brief, reason ):
  msg = reason.getDescription( brief )
  logDebug( msg )

#//===========================================================================//

class NodeStaleReason (object):
  __slots__ = (
      'code',
      'value',
      'builder',
      'sources',
      'targets',
  )
  
  ACTUAL, \
  NO_SIGNATURE, \
  NEW, \
  SIGNATURE_CHANGED, \
  IMPLICIT_DEP_CHANGED, \
  NO_TARGETS, \
  TARGET_CHANGED, \
  FORCE_REBUILD, \
    = range(8)
  
  #//-------------------------------------------------------//
  
  def   __init__( self, builder, sources, targets ):
    self.builder = builder
    self.sources = sources
    self.targets = targets
    self.code = self.ACTUAL
    self.value = None
  
  #//-------------------------------------------------------//
  
  def   _set(self, code, value = None ):
    self.code = code
    self.value = value
    
    eventNodeStaleReason( self )
  
  #//-------------------------------------------------------//
  
  def   setNoSignature( self, NO_SIGNATURE = NO_SIGNATURE ):
    self._set( NO_SIGNATURE )
  
  def   setNew( self, NEW = NEW ):
    self._set( NEW )
      
  def   setSignatureChanged( self, SIGNATURE_CHANGED = SIGNATURE_CHANGED ):
    self._set( SIGNATURE_CHANGED )
  
  def   setImplicitDepChanged( self, value = None, IMPLICIT_DEP_CHANGED = IMPLICIT_DEP_CHANGED ):
    self._set( IMPLICIT_DEP_CHANGED, value )
  
  def   setNoTargets( self, NO_TARGETS = NO_TARGETS):
    self._set( NO_TARGETS )
  
  def   setTargetChanged( self, value, TARGET_CHANGED = TARGET_CHANGED ):
    self._set( TARGET_CHANGED, value )
  
  def   setForceRebuild( self, FORCE_REBUILD = FORCE_REBUILD ):
    self._set( FORCE_REBUILD )
  
  #//-------------------------------------------------------//
  
  def   getNodeName( self, brief ):
    name = self.builder.getTraceName( brief )
    return _getBuildStr( [ name, self.sources, self.targets ], brief )
  
  #//-------------------------------------------------------//
  
  def   getDescription( self, brief = True ):
    
    node_name = self.getNodeName( brief )
    code = self.code
    
    if code == NodeStaleReason.NO_SIGNATURE:
      msg = "Node`s is marked to rebuild always, rebuilding the node: %s" % node_name
    
    elif code == NodeStaleReason.SIGNATURE_CHANGED:
      msg = "Node`s signature has been changed (sources, builder parameters or dependencies were changed), rebuilding the node: %s" % node_name
    
    elif code == NodeStaleReason.NEW:
      msg = "Node's previous state has not been found, building the new node: %s" % node_name
      # msg += "\nbuilder sig: %s" % (self.builder.signature)
      # msg += "\nsources sig: %s" % ([ src.signature for src in self.sources], )
    
    elif code == NodeStaleReason.IMPLICIT_DEP_CHANGED:
      dep = "'%s'" % self.value if self.value else ""
      msg = "Node's implicit dependency %s has changed, rebuilding the node: %s" % (dep, node_name)
    
    elif code == NodeStaleReason.NO_TARGETS:
      msg = "Node's targets were not previously stored, rebuilding the node: %s" % (node_name,)
    
    elif code == NodeStaleReason.TARGET_CHANGED:
      msg = "Node's target '%s' has changed, rebuilding the node: %s" % (self.value, node_name)
    
    elif code == NodeStaleReason.FORCE_REBUILD:
      msg = "Forced rebuild, rebuilding the node: %s" % (node_name,)
    
    else:
      msg = "Node's state is outdated, rebuilding the node: %s" % node_name
    
    return msg
      
#//===========================================================================//

def   _checkDeps( vfile, dep_keys, reason ):
  if dep_keys:
    
    for key in dep_keys:
      value = vfile.getValueByKey( key )
      
      if value is None:
        if reason is not None:
          reason.setImplicitDepChanged()
        return False
      
      actual_value = value.getActual()
      if value != actual_value:
        vfile.replaceValue( key, actual_value )
        if reason is not None:
          reason.setImplicitDepChanged( value )
        return False
        
  return True

#//===========================================================================//

def   _checkTargets( values, reason ):
  if values is None:
    if reason is not None:
      reason.setNoTargets()
    return False
  
  for value in values:
    if not value.isActual():
      if reason is not None:
        reason.setTargetChanged( value )
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
  else:
    if isinstance( value, ValueBase ):
      value = value.get()

    if isinstance( value, FilePath ):
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
      build_str += " << " + sources
    if targets:
      build_str += " >> " + targets
    
    return build_str
  
#//===========================================================================//
  
def   _getClearStr( args, brief = True ):
  
  args    = iter(args)
  next(args, None ) # name
  next(args, None ) # sources
  targets = next(args, None )
  
  return _joinArgs( targets, brief )

#//===========================================================================//

def   _makeNullValue( name, value_type ):
  if isinstance( name, ValueBase ):
    return name
   
  return value_type( name = name, signature = None )

#//===========================================================================//

def   _genNodeValueName( builder, source_values, name_hash ):
  
  target_values = builder.getTargetValues( source_values )
  value_type = builder.getDefaultValueType()
  
  target_values = [ _makeNullValue( value, value_type ) for value in toSequence( target_values ) ]
  
  if target_values:
    names = sorted( value.dumpId() for value in target_values )
    name = simpleObjectSignature( names )
  else:
    names = sorted( value.dumpId() for value in source_values )
    name = simpleObjectSignature( names, name_hash )
  
  return name, target_values

#//===========================================================================//

def   _genNodeValueSignature( source_values, sign_hash ):
  
  if sign_hash is None:
    return None
  
  sign_hash = sign_hash.copy()
  
  for value in source_values:
    sign_hash.update( value.signature )
  
  return sign_hash.digest()

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
    
    self = super(NodeValue,cls).__new__(cls, name, signature)
    
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
  
  def   __getnewargs__(self):
    return self.name, self.signature, self.targets, self.itargets, self.idep_keys
  
  #//-------------------------------------------------------//
  
  def   __bool__( self ):
    return (self.signature is not None) and (self.targets is not None)
  
  #//-------------------------------------------------------//
  
  def   checkActual( self, vfile, built_node_names, reason ):
    
    if (built_node_names is not None) and (self.name not in built_node_names):
      if reason is not None:
        reason.setForceRebuild()
      return False
    
    if not self.signature:
      if reason is not None:
        reason.setNoSignature()
      return False
    
    other = vfile.findValue( self )
    
    if other is None:
      if reason is not None:
        reason.setNew()
      return False
    
    if self.signature != other.signature:
      if reason is not None:
        reason.setSignatureChanged()
      return False
    
    targets   = other.targets
    itargets  = other.itargets
    idep_keys = other.idep_keys
    
    if not _checkDeps( vfile, idep_keys, reason ):
      return False
    
    if not _checkTargets( targets, reason ):
      return False
    
    self.targets = targets
    self.itargets = itargets
    
    return True
  
#//===========================================================================//

class NodeTargetsFilter( object ):
  __slots__ = \
    (
      'node',
      'tags',
    )
  
  def   __init__(self, node, tags ):
    self.node = node
    self.tags = frozenset( toSequence( tags ) )
  
  def   get(self):
    tags = self.tags
    return tuple( value for value in self.node.getTargetValues() if value.tags and (value.tags & tags) )

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
    
    'target_values',
    'itarget_values',
    'idep_values',
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
    
    self.sources = tuple(toSequence( sources ))
    self.dep_nodes = set()
    self.dep_values = []
    
    self.target_values = None
  
  #//=======================================================//
  
  def   isBatch(self):
    return False
  
  #//=======================================================//
  
  def   _split( self, src_values ):
    
    other = object.__new__( self.__class__ )
    
    other.builder         = self.builder
    other.options         = self.options
    other.builder_data    = None
    other.cwd             = self.cwd
    other.sources         = tuple()
    other.source_values   = src_values
    other.dep_nodes       = self.dep_nodes
    other.dep_values      = self.dep_values
    other.target_values   = None
    
    return other
  
  #//=======================================================//
  
  def   split( self, src_values ):
    
    src_values = tuple( toSequence( src_values ) )
    
    other = self._split( src_values )
    
    if __debug__:
      self_source_values = frozenset(self.source_values)
      for src_value in src_values:
        if src_value not in self_source_values:
          raise ErrorNodeSplitUnknownSource( self, src_value )
    
    return other
  
  #//=======================================================//

  def   __getattr__(self, attr):
    if attr == 'name':
      return self._setName()

    if attr == 'signature':
      return self._setSignature()

    if attr == 'source_values':
      return self._setSourceValues()

    if attr in [ 'itarget_values', 'idep_values' ]:
      raise ErrorNoTargets( self )

    raise AttributeError( "Node has not attribute '%s'" % (attr,) )

  #//=======================================================//
  
  def   getNames(self):
    return (self.name,)
  
  def   getNamesAndSignatures(self):
    return ((self.name,self.signature),)

  
  #//=======================================================//

  def   depends( self, dependencies ):
    
    dep_nodes = self.dep_nodes
    dep_values = self.dep_values
    
    for value in toSequence( dependencies ):
      if isinstance( value, Node ):
        dep_nodes.add( value )
      
      elif isinstance( value, NodeTargetsFilter ):
        dep_nodes.add( value.node )
      
      elif isinstance( value, ValueBase ):
        dep_values.append( value )
      
      else:
        raise ErrorNodeDependencyInvalid( value )
  
  #//=======================================================//
  
  def   getDepNodes(self):
    return self.dep_nodes
  
  #//=======================================================//
  
  def   updateDepValues(self):
    dep_nodes = self.dep_nodes
    
    if not dep_nodes:
      return
    
    dep_values = self.dep_values
    
    for node in dep_nodes:
      dep_values.extend( node.target_values )
    
    dep_nodes.clear()
    
    dep_values.sort( key = lambda v: v.dumpId() )
  
  #//=======================================================//
  
  def   getDepValues(self):
    self.updateDepValues()
    return self.dep_values
  
  #//=======================================================//
  
  def   initiate(self):
    with Chdir(self.cwd):
      self.builder = self.builder.initiate()

  #//=======================================================//
  
  def   _getNameHash( self ):
    return newHash( dumpSimpleObject( self.builder.name ) )
  
  #//=======================================================//
  
  def   _getSignatureHash( self ):
    
    sign  = [ self.builder.signature ]
    
    for value in self.getDepValues():
      if value.isNull():
        return None
      
      sign.append( value.name )
      sign.append( value.signature )
    
    sign_hash = newHash( dumpSimpleObject( sign ) )

    return sign_hash
  
  #//=======================================================//
  
  def   _setName( self ):
    
    name_hash = self._getNameHash()
    
    source_values = self.getSourceValues()
    
    name, self.target_values = _genNodeValueName( self.builder, source_values, name_hash )
    self.name = name
    return name

  #//=======================================================//
  
  def   _setSignature( self ):
    sign_hash = self._getSignatureHash()
    self.signature = sign = _genNodeValueSignature( self.getSourceValues(), sign_hash )
    return sign
  
  #//=======================================================//
  
  def   _setSourceValues(self):
    values = []
    
    makeValue = self.builder.makeValue
    
    with Chdir(self.cwd):
      for src in self.sources:
        
        if isinstance( src, Node ):
          values += src.target_values
        
        elif isinstance( src, NodeTargetsFilter ):
          values += src.get()
        
        elif isinstance( src, ValueBase ):
          values.append( src )
        
        else:
          value = makeValue( src, use_cache = True )
          values.append( value )
    
    self.sources = tuple()
    values = tuple(values)
    self.source_values = values
    return values
  
  #//=======================================================//
  
  def   getSources(self):
    return tuple( src.get() for src in self.getSourceValues() )
  
  #//=======================================================//
  
  def   getSourceValues(self):
    return self.source_values
  
  #//=======================================================//
  
  def   getSourceNodes(self):
    nodes = []
    
    for src in self.sources:
      if isinstance(src, Node):
        nodes.append( src )
      
      elif isinstance(src, NodeTargetsFilter):
        nodes.append( src.node )
        
    return nodes
  
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
  
  def   isBuilt(self):
    return self.builder is None
  
  #//=======================================================//
  
  def   build(self):
    self.target_values = None
    self.itarget_values = []
    self.idep_values = []
    
    output = self.builder.build( self )

    if self.target_values is None:
      raise ErrorNoTargets( self )
    
    return output
  
  #//=======================================================//
  
  def   buildDepends( self ):
    return self.builder.depends( self )
  
  #//=======================================================//
  
  def   buildReplace( self ):
    
    sources = self.builder.replace( self )
    if sources is None:
      return False
    
    self.sources = tuple( toSequence( sources ) )
    del self.source_values
    
    return True
  
  #//=======================================================//
  
  def   buildSplit( self ):
    self.updateDepValues()
    return self.builder.split( self )
  
  #//=======================================================//
  
  def   save( self, vfile ):
    if __debug__:
      _ensureActualValues( self.target_values )
      _ensureActualValues( self.idep_values )

    idep_keys = vfile.addValues( self.idep_values )
    
    node_value = NodeValue( name = self.name, signature = self.signature,
                            targets = self.target_values, itargets = self.itarget_values, idep_keys = idep_keys )
    
    vfile.addValue( node_value )

  #//=======================================================//
  
  def   clear( self, vfile ):
    """
    Cleans produced values
    """
    node_value = NodeValue( name = self.name )
    
    node_value = vfile.findValue( node_value )
    if node_value is not None:
      targets = node_value.targets
      itargets = node_value.itargets
      
      if targets is not None:
        self.target_values  = targets
        self.itarget_values = itargets
      else:
        self.target_values  = tuple()
        self.itarget_values = tuple()

    vfile.removeValues( [ node_value ] )
    
    try:
      self.builder.clear( self )
    except Exception:
      pass
    
  #//=======================================================//
  
  def   checkActual( self, vfile, built_node_names = None, explain = False ):
    
    node_value = NodeValue( name = self.name, signature = self.signature )
    
    reason = NodeStaleReason( self.builder, self.source_values, self.target_values ) if explain else None
    
    if not node_value.checkActual( vfile, built_node_names, reason ):
      return False
      
    self.target_values  = node_value.targets
    self.itarget_values = node_value.itargets
    
    return True
    
  #//=======================================================//
  
  def   setNoTargets( self ):
    self.target_values = []
  
  #//=======================================================//
  
  def   addTargets( self, targets, side_effects = None, implicit_deps = None, tags = None ):
    value_maker = self.builder.makeValue
    
    if self.target_values is None:
      self.target_values = []
    
    self.target_values.extend(  value_maker( value, tags = tags )     for value in toSequence(targets) )
    self.itarget_values.extend( value_maker( value )                  for value in toSequence(side_effects) )
    self.idep_values.extend(    value_maker( value, use_cache = True) for value in toSequence(implicit_deps) )

  #//=======================================================//
  
  def   at(self, tags ):
    return NodeTargetsFilter( self, tags )
  
  #//=======================================================//
  
  def   get(self):
    return self.getTargets()
  
  #//=======================================================//
  
  def   getTargets(self):
    return tuple( target.get() for target in self.getTargetValues() )
  
  #//=======================================================//
  
  def   getTargetValues(self):
    target_values = self.target_values
    if target_values is None:
      raise ErrorNoTargets( self )
    
    return target_values
  
  #//=======================================================//
  
  def   getBuildTargetValues(self):
    return self.getTargetValues()
  
  #//=======================================================//

  def   getSideEffectValues(self):
    return self.itarget_values
  
  #//=======================================================//
  
  def   removeTargets(self):
    for value in self.getTargetValues():
      value.remove()
    
    for value in self.getSideEffectValues():
      value.remove()
  
  #//=======================================================//
  
  def   getBuildStr( self, brief = True ):
    args = self.builder.getBuildStrArgs( self, brief = brief )
    return _getBuildStr( args, brief )
  
  #//=======================================================//
  
  def   printSources(self):
    result = []
    sources = self.sources
    if not sources:
      sources = self.source_values
    
    for src in sources:
      if isinstance(src, ValueBase):
        result.append( src.get() )
      
      elif isinstance( src, Node ):
        targets = getattr(src, 'target_values', None)
        if targets is not None:
          result += ( target.get() for target in targets )
        else:
          result.append( src ) 
      
      elif isinstance( src, NodeTargetsFilter ):
        try:
          targets = src.get()
        except AttributeError:
          continue
        
        if targets is not None:
          result += ( target.get() for target in targets )
        else:
          result.append( src ) 
      
      else:
        result.append( src )
    
    sources_str = ', '.join( map( str, result ) )
    
    logInfo("node '%s' sources: %s" % (self, sources_str))
  
  #//=======================================================//
  
  def   printTargets(self):
    targets = [ t.get() for t in getattr(self, 'target_values', []) ]
    logInfo("node '%s' targets: %s" % (self, targets))
  
#//===========================================================================//

#noinspection PyAttributeOutsideInit
class BatchNode (Node):
  
  __slots__ = \
    (
      'node_values',
      'changed_source_values',
    )
  
  #//=======================================================//
  
  def   isBatch(self):
    return True
  
  #//=======================================================//
  
  def   getNames(self):
    return (value.name for value, ideps in self.node_values.values())
  
  def   getNamesAndSignatures(self):
    return ((value.name, value.signature) for value, ideps in self.node_values.values())
  
  #//=======================================================//
  
  def   __getattr__(self, attr):
    if attr in ['name', 'signature']:
      raise AttributeError("Attribute '%s' is not applicable for BatchNode" % (attr,))

    if attr == 'node_values':
      return self._setNodeValues()

    if attr == 'changed_source_values':
      return self._setSourceValues()

    return super(BatchNode,self).__getattr__( attr )

  #//=======================================================//
  
  def   split( self, src_values ):
    src_values = tuple( toSequence( src_values ) )
    
    other = self._split( src_values )
    
    other.changed_source_values = src_values
    other_node_values = {}
    other.node_values = other_node_values
    
    node_values = self.node_values
    for src_value in src_values:
      try:
        other_node_values[ src_value ] = node_values[ src_value ]
      except KeyError:
        raise ErrorNodeSplitUnknownSource( self, src_value )
    
    return other
  
  #//=======================================================//

  def   _setNodeValues( self ):

    name_hash = self._getNameHash()
    sign_hash = self._getSignatureHash()
    
    node_values = {}
    
    for src_value in self.source_values:
      
      src_values = (src_value,)
      
      name, target_values = _genNodeValueName( self.builder, src_values, name_hash )
      signature           = _genNodeValueSignature( src_values, sign_hash )
      
      ideps = []
      node_values[ src_value ] = NodeValue( name, signature, target_values ), ideps
    
    self.node_values = node_values
    return node_values
      
  #//=======================================================//
  
  def   _setSourceValues(self):
    src_values = super(BatchNode,self)._setSourceValues()
    self.changed_source_values = src_values
    return src_values
  
  #//=======================================================//
  
  def   getSourceValues(self):
    return self.changed_source_values
  
  #//=======================================================//
  
  def   save( self, vfile ):
    
    for src_value in self.changed_source_values:
      node_value, ideps = self.node_values[ src_value ]
      
      targets = node_value.targets
      
      if targets is None:
        continue
      
      if __debug__:
        _ensureActualValues( targets )
        _ensureActualValues( ideps )

      node_value.idep_keys = vfile.addValues( ideps )
      
      vfile.addValue( node_value )
  
  #//=======================================================//
  
  def   clear( self, vfile ):
    targets = []
    itargets = []
    node_values = []
    
    for src_value in self.source_values:
      node_value, ideps = self.node_values[ src_value ]
      
      node_value = vfile.findValue( node_value )
      
      if node_value is not None:
        node_values.append( node_value )
        
        if node_value.targets is not None:
          targets   += node_value.targets
          itargets  += node_value.itargets
              
    self.target_values  = targets
    self.itarget_values = itargets
    
    vfile.removeValues( node_values )
    
    try:
      self.builder.clear( self )
    except Exception:
      pass
  
  #//=======================================================//
  
  def   build(self):
    output = self.builder.buildBatch( self )
    self._populateTargets()
    
    return output
  
  #//=======================================================//
  
  def   _populateTargets( self ):
    targets   = []
    itargets  = []
    
    for src_value in self.source_values:
      node_value, ideps = self.node_values[ src_value ]
      node_targets = node_value.targets
      if node_targets is None:
        raise ErrorNoSrcTargets( self, src_value )
      
      targets += node_targets
      itargets += node_value.itargets
    
    self.target_values = targets
    self.itarget_values = itargets
  
  #//=======================================================//
  
  def   checkActual( self, vfile, built_node_names = None, explain = False ):
    
    changed_sources = []
    targets = []
    itargets = []
    
    for src_value in self.source_values:
      node_value, ideps = self.node_values[ src_value ]
      
      reason = NodeStaleReason( self.builder, (src_value,), node_value.targets ) if explain else None
      
      if not node_value.checkActual( vfile, built_node_names, reason ):
        node_value.targets = None
        changed_sources.append( src_value )
      
      elif not changed_sources:
        targets   += node_value.targets
        itargets  += node_value.itargets
    
    if changed_sources:
      self.changed_source_values = changed_sources
      return False
    
    self.target_values  = targets
    self.itarget_values = itargets
    return True
  
  #//=======================================================//
  
  def   addTargets( self, targets, itargets = None, ideps = None, tags = None ):
    raise Exception( "addTargets() is not allowed for batch build. addSourceTargets() must be used instead." )
  
  #//=======================================================//
  
  def   addSourceTargets( self, src_value, targets, side_effects = None, implicit_deps = None, tags = None ):
    
    try:
      node_value, node_ideps = self.node_values[ src_value ]
    except KeyError:
      raise ErrorNodeUnknownSource( src_value )

    value_maker = self.builder.makeValue
    
    node_targets = node_value.targets
    node_itargets = node_value.itargets
    
    if node_targets is None: node_value.targets = node_targets = []
    if node_itargets is None: node_value.itargets = node_itargets = []
    
    node_targets.extend(  value_maker( value, tags = tags)        for value in toSequence( targets ) )
    node_itargets.extend( value_maker( value )                    for value in toSequence( side_effects ) )
    node_ideps.extend(    value_maker( value, use_cache = True )  for value in toSequence( implicit_deps ) )
      
  #//=======================================================//
  
  def   setNoTargets( self ):
    for src_value in self.changed_source_values:
      node_value, node_ideps = self.node_values[ src_value ]
      node_value.targets = []
  
  #//=======================================================//
  
  def   getBuildTargetValues(self):
    targets = []
    
    for src_value in self.changed_source_values:
      node_value, ideps = self.node_values[ src_value ]
      node_targets = node_value.targets
      if node_targets:
        targets += node_targets
    
    return targets
  
  #//=======================================================//
  
  def   shrink(self):
    super( BatchNode, self).shrink()
    
    self.node_values = None
    self.changed_source_values = None

  
