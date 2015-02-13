
# Copyright (c) 2011-2014 The developers of Aqualid project
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
  'NodeFilter', 'NodeDirNameFilter', 'NodeBaseNameFilter',
)

import os
import operator

from aql.utils import simpleObjectSignature, dumpSimpleObject, newHash, Chdir, eventStatus, logDebug, logInfo
from aql.util_types import toSequence, isString, FilePath, AqlException

from aql.entity import EntityBase, FileEntityBase, SimpleEntity, pickleable

#//===========================================================================//

class   ErrorNodeDependencyInvalid( AqlException ):
  def   __init__( self, dep ):
    msg = "Invalid node dependency: %s" % (dep,)
    super(ErrorNodeDependencyInvalid, self).__init__( msg )

class   ErrorNodeSplitUnknownSource( AqlException ):
  def   __init__( self, node, entity ):
    msg = "Node '%s' can't be split to unknown source entity: %s" % (node.getBuildStr( brief = False ), entity )
    super(ErrorNodeSplitUnknownSource, self).__init__( msg )
    
class   ErrorNoTargets( AttributeError ):
  def   __init__( self, node ):
    msg = "Node targets are not built or set yet: %s" % (node,)
    super(ErrorNoTargets, self).__init__( msg )

class   ErrorNoSrcTargets( AqlException ):
  def   __init__( self, node, src_entity ):
    msg = "Source '%s' targets are not built or set yet: %s" % (src_entity.get(), node)
    super(ErrorNoSrcTargets, self).__init__( msg )

class   ErrorUnactualEntity( AqlException ):
  def   __init__( self, entity ):
    msg = "Target entity is not actual: %s (%s)" % (entity.name, type(entity))
    super(ErrorUnactualEntity, self).__init__( msg )

class   ErrorNodeUnknownSource( AqlException ):
  def   __init__( self, src_entity ):
    msg = "Unknown source entity: %s (%s)" % (src_entity, type(src_entity))
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
      'entity',
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
    self.entity = None
  
  #//-------------------------------------------------------//
  
  def   _set(self, code, entity = None ):
    self.code = code
    self.entity = entity
    
    eventNodeStaleReason( self )
  
  #//-------------------------------------------------------//
  
  def   setNoSignature( self, NO_SIGNATURE = NO_SIGNATURE ):
    self._set( NO_SIGNATURE )
  
  def   setNew( self, NEW = NEW ):
    self._set( NEW )
      
  def   setSignatureChanged( self, SIGNATURE_CHANGED = SIGNATURE_CHANGED ):
    self._set( SIGNATURE_CHANGED )
  
  def   setImplicitDepChanged( self, entity = None, IMPLICIT_DEP_CHANGED = IMPLICIT_DEP_CHANGED ):
    self._set( IMPLICIT_DEP_CHANGED, entity )
  
  def   setNoTargets( self, NO_TARGETS = NO_TARGETS):
    self._set( NO_TARGETS )
  
  def   setTargetChanged( self, entity, TARGET_CHANGED = TARGET_CHANGED ):
    self._set( TARGET_CHANGED, entity )
  
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
      dep = "'%s'" % self.entity if self.entity else ""
      msg = "Node's implicit dependency %s has changed, rebuilding the node: %s" % (dep, node_name)
    
    elif code == NodeStaleReason.NO_TARGETS:
      msg = "Node's targets were not previously stored, rebuilding the node: %s" % (node_name,)
    
    elif code == NodeStaleReason.TARGET_CHANGED:
      msg = "Node's target '%s' has changed, rebuilding the node: %s" % (self.entity, node_name)
    
    elif code == NodeStaleReason.FORCE_REBUILD:
      msg = "Forced rebuild, rebuilding the node: %s" % (node_name,)
    
    else:
      msg = "Node's state is outdated, rebuilding the node: %s" % node_name
    
    return msg
      
#//===========================================================================//

def   _checkDeps( vfile, dep_keys, dep_entities, reason ):
  if dep_keys:
    
    for key in dep_keys:
      entity = vfile.getEntityByKey( key )
      
      if entity is None:
        if reason is not None:
          reason.setImplicitDepChanged()
        return False
      
      actual_entity = entity.getActual()    # TODO: store actual status in vfile
      if entity != actual_entity:
        vfile.replaceEntity( key, actual_entity )
        if reason is not None:
          reason.setImplicitDepChanged( entity )
        return False
      
      dep_entities.append( entity )
      
  return True

#//===========================================================================//

def   _checkTargets( entities, reason ):
  if entities is None:
    if reason is not None:
      reason.setNoTargets()
    return False
  
  for entity in entities:
    if not entity.isActual():
      if reason is not None:
        reason.setTargetChanged( entity )
      return False
      
  return True

#//===========================================================================//

def   _ensureActualEntities( entities ):
  for entity in entities:
    if not entity.isActual():
      raise ErrorUnactualEntity( entity )

#//===========================================================================//

def   _getTraceArg( entity, brief ):
  if isinstance( entity, FileEntityBase ):
    value = entity.get()
    if brief:
      value = os.path.basename( value )
  else:
    if isinstance( entity, EntityBase ):
      value = entity.get()

    elif isinstance( entity, FilePath ):
      if brief:
        value = os.path.basename( entity )

    elif isString( entity ):
      value = entity.strip()

      npos = value.find('\n')
      if npos != -1:
        value = value[:npos]

      max_len = 64 if brief else 256
      src_len = len(value)
      if src_len > max_len:
        value = "%s...%s" % (value[:max_len//2], value[src_len - (max_len//2):])

    else:
      value = None
  
  return value

#//===========================================================================//

def   _joinArgs( entities, brief ):
  
  args = []
  
  for arg in toSequence(entities):
    arg = _getTraceArg(arg, brief )
    if arg and isString( arg ):
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

def   _makeNullEntity( name, entity_type ):
  if isinstance( name, EntityBase ):
    return name
   
  return entity_type( name = name, signature = None )

#//===========================================================================//

def   _genNodeEntityName( builder, source_entities, name_hash ):
  
  target_entities = builder.getTargetEntities( source_entities )
  entity_type = builder.getDefaultEntityType()
  
  target_entities = [ _makeNullEntity( entity, entity_type ) for entity in toSequence( target_entities ) ]
  
  if target_entities:
    names = sorted( entity.dumpId() for entity in target_entities )
    name = simpleObjectSignature( names )
  else:
    names = sorted( entity.dumpId() for entity in source_entities )
    name = simpleObjectSignature( names, name_hash )
  
  return name, target_entities

#//===========================================================================//

def   _genNodeEntitySignature( source_entities, sign_hash ):
  
  if sign_hash is None:
    return None
  
  sign_hash = sign_hash.copy()
  
  for entity in source_entities:
    entity_signature = entity.signature
    if entity_signature is None:
      return None
    
    sign_hash.update( entity_signature )
  
  return sign_hash.digest()

#//===========================================================================//

@pickleable
class   NodeEntity (EntityBase):
  
  __slots__ = (
    'targets',
    'itargets',
    'ideps',
    'idep_keys',
  )
  
  #//-------------------------------------------------------//
  
  def   __new__( cls, name, signature = None, targets = None, itargets = None, idep_keys = None ):
    
    self = super(NodeEntity,cls).__new__(cls, name, signature)
    
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
    
    other = vfile.findEntity( self )
    
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
    
    ideps = []
    
    if not _checkDeps( vfile, idep_keys, ideps, reason ):
      return False
    
    if not _checkTargets( targets, reason ):
      return False
    
    self.targets = targets
    self.itargets = itargets
    self.ideps = ideps
    
    return True
  
#//===========================================================================//

class NodeFilter (object):
  
  __slots__ = \
  (
    'node',
    'node_attribute',
  )
  
  def   __init__( self, node, node_attribute = 'target_entities' ):
    self.node = node
    self.node_attribute = node_attribute
  
  #//-------------------------------------------------------//
  
  def   getNode(self):
    node = self.node
    
    while isinstance( node, NodeFilter ):
      node = node.node
    
    return node
  
  #//-------------------------------------------------------//
  
  def   get(self):
    
    entities = self.getEntities()
    if len(entities) == 1:
      return entities[0]
    
    return entities
 
  #//-------------------------------------------------------//
  
  def   getEntities(self):
    node = self.node
    if isinstance( node, NodeFilter ):
      entities = node.getEntities()
    else:
      entities = getattr( node, self.node_attribute )
    
    return self._get( entities )
  
  #//-------------------------------------------------------//
  
  def   _get( self, entities ):
    return entities
  
#//===========================================================================//

class NodeTagsFilter( NodeFilter ):
  __slots__ = \
    (
      'tags',
    )
  
  def   __init__( self, node, tags, node_attribute = 'target_entities' ):
    super(NodeTagsFilter, self).__init__( node, node_attribute )
    self.tags = frozenset( toSequence( tags ) )
  
  def   _get( self, entities ):
    tags = self.tags
    return tuple( entity for entity in entities if entity.tags and (entity.tags & tags) )

#//===========================================================================//

class NodeDirNameFilter( NodeFilter ):
  
  def   _get( self, entities ):
    return tuple( SimpleEntity( os.path.dirname( entity.get() ) ) for entity in entities )

#//===========================================================================//

class NodeBaseNameFilter( NodeFilter ):
  def   _get( self, entities ):
    return tuple( SimpleEntity( os.path.basename( entity.get() ) ) for entity in entities )

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
    'source_entities',
    
    'dep_nodes',
    'dep_entities',
    
    'target_entities',
    'itarget_entities',
    'idep_entities',
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
    self.dep_entities = []
    
    self.target_entities = None
  
  #//=======================================================//
  
  def   isBatch(self):
    return False
  
  #//=======================================================//
  
  def   getWeight( self ):
    return self.builder.getWeight( self )
  
  #//=======================================================//
  
  def   _split( self, src_entities ):
    
    other = object.__new__( self.__class__ )
    
    other.builder         = self.builder
    other.options         = self.options
    other.builder_data    = None
    other.cwd             = self.cwd
    other.sources         = tuple()
    other.source_entities   = src_entities
    other.dep_nodes       = self.dep_nodes
    other.dep_entities      = self.dep_entities
    other.target_entities   = None
    
    return other
  
  #//=======================================================//
  
  def   split( self, src_entities ):
    
    src_entities = tuple( toSequence( src_entities ) )
    
    other = self._split( src_entities )
    
    if __debug__:
      self_source_entities = frozenset(self.source_entities)
      for src_entity in src_entities:
        if src_entity not in self_source_entities:
          raise ErrorNodeSplitUnknownSource( self, src_entity )
    
    return other
  
  #//=======================================================//

  def   __getattr__(self, attr):
    if attr == 'name':
      return self._setName()

    if attr == 'signature':
      return self._setSignature()

    if attr == 'source_entities':
      return self._setSourceEntities()

    if attr in [ 'itarget_entities', 'idep_entities' ]:
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
    dep_entities = self.dep_entities
    
    for entity in toSequence( dependencies ):
      if isinstance( entity, Node ):
        dep_nodes.add( entity )
      
      elif isinstance( entity, NodeFilter ):
        dep_nodes.add( entity.getNode() )
      
      elif isinstance( entity, EntityBase ):
        dep_entities.append( entity )
      
      else:
        raise ErrorNodeDependencyInvalid( entity )
  
  #//=======================================================//
  
  def   getDepNodes(self):
    return self.dep_nodes
  
  #//=======================================================//
  
  def   updateDepEntities(self):
    dep_nodes = self.dep_nodes
    
    if not dep_nodes:
      return
    
    dep_entities = self.dep_entities
    
    for node in dep_nodes:
      target_entities = node.target_entities
      if target_entities:
        dep_entities.extend( target_entities )
    
    dep_nodes.clear()
    
    dep_entities.sort( key = operator.methodcaller('dumpId') )
  
  #//=======================================================//
  
  def   getDepEntities(self):
    self.updateDepEntities()
    return self.dep_entities
  
  #//=======================================================//
  
  def   initiate(self):
    with Chdir(self.cwd):
      self.builder = self.builder.initiate()

  #//=======================================================//
  
  def   _getNameHash( self ):
    return newHash( dumpSimpleObject( self.builder.name ) )
  
  #//=======================================================//
  
  def   _getSignatureHash( self ):

    builder_signature = self.builder.signature
    if builder_signature is None:
      return None

    sign = [ builder_signature ]
    
    for entity in self.getDepEntities():
      if entity.isNull():
        return None
      
      sign.append( entity.name )
      sign.append( entity.signature )
    
    sign_hash = newHash( dumpSimpleObject( sign ) )

    return sign_hash
  
  #//=======================================================//
  
  def   _setName( self ):
    
    name_hash = self._getNameHash()
    
    source_entities = self.getSourceEntities()
    
    name, target_entities = _genNodeEntityName( self.builder, source_entities, name_hash )
    
    if target_entities:
      self.target_entities = target_entities
    
    self.name = name
    return name

  #//=======================================================//
  
  def   _setSignature( self ):
    sign_hash = self._getSignatureHash()
    self.signature = sign = _genNodeEntitySignature( self.getSourceEntities(), sign_hash )
    return sign
  
  #//=======================================================//
  
  def   _setSourceEntities(self):
    entities = []
    
    makeEntity = self.builder.makeEntity
    
    with Chdir(self.cwd):
      for src in self.sources:
        
        if isinstance( src, Node ):
          entities += src.target_entities
        
        elif isinstance( src, NodeFilter ):
          entities += src.getEntities()
        
        elif isinstance( src, EntityBase ):
          entities.append( src )
        
        else:
          entity = makeEntity( src, use_cache = True )
          entities.append( entity )
    
    self.sources = tuple()
    entities = tuple(entities)
    self.source_entities = entities
    return entities
  
  #//=======================================================//
  
  def   getSources(self):
    return tuple( src.get() for src in self.getSourceEntities() )
  
  #//=======================================================//
  
  def   getSourceEntities(self):
    return self.source_entities
  
  #//=======================================================//
  
  def   getSourceNodes(self):
    nodes = []
    
    for src in self.sources:
      if isinstance(src, Node):
        nodes.append( src )
      
      elif isinstance(src, NodeFilter):
        nodes.append( src.getNode() )
        
    return nodes
  
  #//=======================================================//
  
  def   shrink(self):
    self.cwd = None
    self.dep_nodes = None
    # self.dep_entities = None
    self.sources = None
    # self.source_entities = None
    
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
    self.target_entities = None
    self.itarget_entities = []
    self.idep_entities = []
    
    builder = self.builder
    
    output = builder.build( self )
    
    if self.target_entities is None:
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
    del self.source_entities
    
    return True
  
  #//=======================================================//
  
  def   buildSplit( self ):
    self.updateDepEntities()
    groups = self.builder.split( self )
    if not groups:
      return None
    
    if len(groups) < 2:
      return None
    
    return tuple( self.split( group ) for group in groups )

  #//=======================================================//
  
  def   save( self, vfile ):
    if __debug__:
      _ensureActualEntities( self.target_entities )
      _ensureActualEntities( self.idep_entities )

    idep_keys = vfile.addEntities( self.idep_entities )
    
    node_entity = NodeEntity( name = self.name, signature = self.signature,
                            targets = self.target_entities, itargets = self.itarget_entities, idep_keys = idep_keys )
    
    vfile.addEntity( node_entity )

  #//=======================================================//
  
  def   clear( self, vfile ):
    """
    Clear produced entities
    """
    
    self.idep_entities = tuple()
    
    node_keys = []
    node_entity = NodeEntity( name = self.name )
    
    node_key = vfile.findEntityKey( node_entity )
    if node_key is None:
      if self.target_entities is None:
        self.target_entities = tuple()
      
      self.itarget_entities = tuple()
      
    else:
      node_entity = vfile.getEntityByKey( node_key )
      
      targets = node_entity.targets
      itargets = node_entity.itargets
      
      if targets is not None:
        self.target_entities  = targets
        self.itarget_entities = itargets
      else:
        self.target_entities  = tuple()
        self.itarget_entities = tuple()
      
      node_keys.append( node_key )
      
    try:
      self.builder.clear( self )
    except Exception:
      pass
    
    return node_keys
    
  #//=======================================================//
  
  def   checkActual( self, vfile, built_node_names = None, explain = False ):
    
    node_entity = NodeEntity( name = self.name, signature = self.signature )
    
    reason = NodeStaleReason( self.builder, self.source_entities, self.target_entities ) if explain else None
    
    if not node_entity.checkActual( vfile, built_node_names, reason ):
      return False
      
    self.target_entities  = node_entity.targets
    self.itarget_entities = node_entity.itargets
    self.idep_entities    = node_entity.ideps
    
    return True
    
  #//=======================================================//
  
  def   setNoTargets( self ):
    self.target_entities = []
  
  #//=======================================================//
  
  def   addTargets( self, targets, side_effects = None, implicit_deps = None, tags = None ):
    entity_maker = self.builder.makeEntity
    
    if self.target_entities is None:
      self.target_entities = []
    
    self.target_entities.extend(  entity_maker( entity, tags = tags )     for entity in toSequence(targets) )
    self.itarget_entities.extend( entity_maker( entity )                  for entity in toSequence(side_effects) )
    self.idep_entities.extend(    entity_maker( entity, use_cache = True) for entity in toSequence(implicit_deps) )

  #//=======================================================//
  
  def   at(self, tags ):
    return NodeTagsFilter( self, tags )
  
  #//=======================================================//
  
  def   __filter( self, node_attribute, tags ):
    if tags is None:
      return NodeFilter( self, node_attribute )
    
    return NodeTagsFilter( self, tags, node_attribute )
  
  #//=======================================================//
  
  def   filterSources( self, tags = None ):
    return self.__filter( 'source_entities', tags )
  
  def   filterSideEffects( self, tags = None ):
    return self.__filter( 'itarget_entities', tags )
  
  def   filterImplicitDependencies( self, tags = None ):
    return self.__filter( 'idep_entities', tags )
  
  def   filterDependencies( self, tags = None ):
    return self.__filter( 'dep_entities', tags )
  
  #//=======================================================//
  
  def   get(self):
    targets = self.getTargets()
    if len(targets) == 1:
      return targets[0]
    
    return targets
  
  #//=======================================================//
  
  def   getTargets(self):
    return tuple( target.get() for target in self.getTargetEntities() )
  
  #//=======================================================//
  
  def   getTargetEntities(self):
    target_entities = self.target_entities
    if target_entities is None:
      raise ErrorNoTargets( self )
    
    return target_entities
  
  #//=======================================================//
  
  def   getBuildTargetEntities(self):
    return self.getTargetEntities()
  
  #//=======================================================//

  def   getSideEffectEntities(self):
    return self.itarget_entities
  
  #//=======================================================//
  
  def   removeTargets(self):
    for entity in self.getTargetEntities():
      entity.remove()
    
    for entity in self.getSideEffectEntities():
      entity.remove()
  
  #//=======================================================//
  
  def   _pullTargets( self, nodes ):
    targets   = []
    itargets  = []
    ideps  = []
    
    for node in nodes:
      targets   += node.target_entities
      itargets  += node.itarget_entities
      ideps     += node.idep_entities
      
    self.target_entities = targets
    self.itarget_entities = itargets
    self.idep_entities = ideps
  
  #//=======================================================//
  
  def   getBuildStr( self, brief = True ):
    try:
      args = self.builder.getBuildStrArgs( self, brief = brief )
      return _getBuildStr( args, brief )
    except Exception as ex:
      if 'BuilderInitiator' not in str(ex):
        print("getBuildStr: ex: %s, %s" % (ex,ex.args))
        raise
    
    return str(self)  # TODO: return raw data
    
  #//=======================================================//
  
  def   printSources(self):
    result = []
    sources = self.sources
    if not sources:
      sources = self.source_entities
    
    for src in sources:
      if isinstance(src, EntityBase):
        result.append( src.get() )
      
      elif isinstance( src, Node ):
        targets = getattr(src, 'target_entities', None)
        if targets is not None:
          result += ( target.get() for target in targets )
        else:
          result.append( src ) 
      
      elif isinstance( src, NodeFilter ):
        try:
          targets = src.getEntities()
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
    targets = [ t.get() for t in getattr(self, 'target_entities', []) ]
    logInfo("node '%s' targets: %s" % (self, targets))
  
#//===========================================================================//

#noinspection PyAttributeOutsideInit
class BatchNode (Node):
  
  __slots__ = \
    (
      'node_entities',
      'changed_source_entities',
    )
  
  #//=======================================================//
  
  def   isBatch(self):
    return True
  
  #//=======================================================//
  
  def   getNames(self):
    return (entity.name for entity, ideps in self.node_entities.values())
  
  def   getNamesAndSignatures(self):
    return ((entity.name, entity.signature) for entity, ideps in self.node_entities.values())
  
  #//=======================================================//
  
  def   __getattr__(self, attr):
    if attr in ['name', 'signature']:
      raise AttributeError("Attribute '%s' is not applicable for BatchNode" % (attr,))

    if attr == 'node_entities':
      return self._setNodeEntities()

    if attr == 'changed_source_entities':
      return self._setSourceEntities()

    return super(BatchNode,self).__getattr__( attr )

  #//=======================================================//
  
  def   split( self, src_entities ):
    src_entities = tuple( toSequence( src_entities ) )
    
    other = self._split( src_entities )
    
    other.changed_source_entities = src_entities
    other_node_entities = {}
    other.node_entities = other_node_entities
    
    node_entities = self.node_entities
    for src_entity in src_entities:
      try:
        other_node_entities[ src_entity ] = node_entities[ src_entity ]
      except KeyError:
        raise ErrorNodeSplitUnknownSource( self, src_entity )
    
    return other
  
  #//=======================================================//

  def   _setNodeEntities( self ):

    name_hash = self._getNameHash()
    sign_hash = self._getSignatureHash()
    
    node_entities = {}
    
    for src_entity in self.source_entities:
      
      src_entities = (src_entity,)
      
      name, target_entities = _genNodeEntityName( self.builder, src_entities, name_hash )
      signature = _genNodeEntitySignature( src_entities, sign_hash )
      
      ideps = []
      node_entities[ src_entity ] = NodeEntity( name, signature, target_entities ), ideps
    
    self.node_entities = node_entities
    return node_entities
      
  #//=======================================================//
  
  def   _setSourceEntities(self):
    src_entities = super(BatchNode,self)._setSourceEntities()
    self.changed_source_entities = src_entities
    return src_entities
  
  #//=======================================================//
  
  def   getSourceEntities(self):
    return self.changed_source_entities
  
  #//=======================================================//
  
  def   save( self, vfile ):
    
    for src_entity in self.changed_source_entities:
      node_entity, ideps = self.node_entities[ src_entity ]
      
      targets = node_entity.targets
      
      if targets is None:
        continue
      
      if __debug__:
        _ensureActualEntities( targets )
        _ensureActualEntities( ideps )

      node_entity.idep_keys = vfile.addEntities( ideps )
      
      vfile.addEntity( node_entity )
  
  #//=======================================================//
  
  def   clear( self, vfile ):
    targets = []
    itargets = []
    ideps = []
    node_keys = []
    
    for src_entity in self.source_entities:
      node_entity, src_ideps = self.node_entities[ src_entity ]
      
      other_key = vfile.findEntityKey( node_entity )
      
      if other_key is None:
        if node_entity.targets is None:
          node_entity.targets = tuple()
        
        if node_entity.itargets is None:
          node_entity.itargets = tuple()
          
      else:
        other = vfile.getEntityByKey( other_key )
        
        node_keys.append( other_key )
        
        node_entity.targets = other.targets
        node_entity.itargets = other.itargets
        
        if other.targets is not None:
          targets   += other.targets
          itargets  += other.itargets
          ideps     += src_ideps
              
    self.target_entities  = targets
    self.itarget_entities = itargets
    self.idep_entities    = ideps
    
    try:
      self.builder.clear( self )
    except Exception:
      pass
  
    return node_keys
  
  #//=======================================================//
  
  def   build(self):
    output = self.builder.buildBatch( self )
    self._populateTargets()
    
    return output
  
  #//=======================================================//
  
  def   _populateTargets( self ):
    targets   = []
    itargets  = []
    ideps  = []
    
    for src_entity in self.source_entities:
      node_entity, src_ideps = self.node_entities[ src_entity ]
      node_targets = node_entity.targets
      if node_targets is None:
        raise ErrorNoSrcTargets( self, src_entity )
      
      targets += node_targets
      itargets += node_entity.itargets
      ideps += src_ideps
    
    self.target_entities = targets
    self.itarget_entities = itargets
    self.idep_entities = ideps
  
  #//=======================================================//
  
  def   checkActual( self, vfile, built_node_names = None, explain = False ):
    
    changed_sources = []
    targets = []
    itargets = []
    ideps = []
    
    for src_entity in self.source_entities:
      node_entity, ideps = self.node_entities[ src_entity ]
      
      reason = NodeStaleReason( self.builder, (src_entity,), node_entity.targets ) if explain else None
      
      if not node_entity.checkActual( vfile, built_node_names, reason ):
        node_entity.targets = None
        changed_sources.append( src_entity )
      
      elif not changed_sources:
        targets   += node_entity.targets
        itargets  += node_entity.itargets
        ideps     += node_entity.ideps
    
    if changed_sources:
      self.changed_source_entities = changed_sources
      return False
    
    self.target_entities  = targets
    self.itarget_entities = itargets
    self.idep_entities    = ideps
    
    return True
  
  #//=======================================================//
  
  def   addTargets( self, targets, itargets = None, ideps = None, tags = None ):
    raise Exception( "addTargets() is not allowed for batch build. addSourceTargets() must be used instead." )
  
  #//=======================================================//
  
  def   addSourceTargets( self, src_entity, targets, side_effects = None, implicit_deps = None, tags = None ):
    
    try:
      node_entity, node_ideps = self.node_entities[ src_entity ]
    except KeyError:
      raise ErrorNodeUnknownSource( src_entity )

    entity_maker = self.builder.makeEntity
    
    node_targets = node_entity.targets
    node_itargets = node_entity.itargets
    
    if node_targets is None: node_entity.targets = node_targets = []
    if node_itargets is None: node_entity.itargets = node_itargets = []
    
    node_targets.extend(  entity_maker( entity, tags = tags)        for entity in toSequence( targets ) )
    node_itargets.extend( entity_maker( entity )                    for entity in toSequence( side_effects ) )
    node_ideps.extend(    entity_maker( entity, use_cache = True )  for entity in toSequence( implicit_deps ) )
      
  #//=======================================================//
  
  def   setNoTargets( self ):
    for src_entity in self.changed_source_entities:
      node_entity, node_ideps = self.node_entities[ src_entity ]
      node_entity.targets = []
  
  #//=======================================================//
  
  def   getBuildTargetEntities(self):
    targets = []
    
    for src_entity in self.changed_source_entities:
      node_entity, ideps = self.node_entities[ src_entity ]
      node_targets = node_entity.targets
      if node_targets:
        targets += node_targets
    
    return targets
  
  #//=======================================================//
  
  def   shrink(self):
    super( BatchNode, self).shrink()
    
    self.node_entities = None
    self.changed_source_entities = None

  
