#
# Copyright (c) 2014-2015 The developers of Aqualid project
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
#  OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import os
import operator

from aql.util_types import to_sequence
from aql.utils import new_hash, event_status, log_debug, log_info
from aql.entity import EntityBase, SimpleEntity, pickleable

__all__ = (
    'Node',
    'NodeFilter', 'NodeDirNameFilter', 'NodeBaseNameFilter',
)

# ==============================================================================


class ErrorNodeDependencyInvalid(Exception):

    def __init__(self, dep):
        msg = "Invalid node dependency: %s" % (dep,)
        super(ErrorNodeDependencyInvalid, self).__init__(msg)


class ErrorNodeSplitUnknownSource(Exception):

    def __init__(self, node, entity):
        msg = "Node '%s' can't be split to unknown source entity: %s" % (
            node.get_build_str(brief=False), entity)
        super(ErrorNodeSplitUnknownSource, self).__init__(msg)


class ErrorNoTargets(AttributeError):

    def __init__(self, node):
        msg = "Node targets are not built or set yet: %s" % (node,)
        super(ErrorNoTargets, self).__init__(msg)


class ErrorNoSrcTargets(Exception):

    def __init__(self, node, src_entity):
        msg = "Source '%s' targets are not built or set yet: %s" % (
            src_entity.get(), node)
        super(ErrorNoSrcTargets, self).__init__(msg)


class ErrorUnactualEntity(Exception):

    def __init__(self, entity):
        msg = "Target entity is not actual: %s (%s)" % (
            entity.name, type(entity))
        super(ErrorUnactualEntity, self).__init__(msg)


class ErrorNodeUnknownSource(Exception):

    def __init__(self, src_entity):
        msg = "Unknown source entity: %s (%s)" % (src_entity, type(src_entity))
        super(ErrorNodeUnknownSource, self).__init__(msg)

# ==============================================================================


@event_status
def event_node_rebuild_reason(settings, reason):
    if isinstance(reason, NodeRebuildReason):
        msg = reason.get_message(settings.brief)
    else:
        msg = str(reason)

    log_debug(msg)

# ==============================================================================


class NodeRebuildReason (Exception):
    __slots__ = (
        'builder',
        'sources',
    )

    # -----------------------------------------------------------

    def __init__(self, node_entity):
        self.builder = node_entity.builder
        self.sources = node_entity.source_entities

    # -----------------------------------------------------------

    def get_node_name(self, brief):
        return self.builder.get_trace(self.sources, brief=brief)

    # -----------------------------------------------------------

    def __str__(self):
        return self.get_message(False)

    # -----------------------------------------------------------

    def get_message(self, brief):
        node_name = self.get_node_name(brief)
        description = self.get_description(brief)
        return "%s\nRebuilding the node: %s" % (description, node_name)

    # -----------------------------------------------------------

    def get_description(self, brief):
        return "Node's state is changed."

# ==============================================================================


class NodeRebuildReasonAlways (NodeRebuildReason):
    def get_description(self, brief):
        return "Node is marked to rebuild always."


class NodeRebuildReasonNew (NodeRebuildReason):
    def get_description(self, brief):
        return "Node's previous state has not been found."


class NodeRebuildReasonSignature (NodeRebuildReason):
    def get_description(self, brief):
        return "Node`s signature has been changed " \
               "(sources, builder parameters or dependencies were changed)."


class NodeRebuildReasonNoTargets (NodeRebuildReason):
    def get_description(self, brief):
        return "Unknown Node's targets."


class NodeRebuildReasonImplicitDep (NodeRebuildReason):

    __slots__ = (
        'entity',
    )

    def __init__(self, node_entity, idep_entity=None):
        super(NodeRebuildReasonImplicitDep, self).__init__(node_entity)
        self.entity = idep_entity

    def get_description(self, brief):
        dep = (" '%s'" % self.entity) if self.entity is not None else ""
        return "Node's implicit dependency%s has changed, " % (dep,)


class NodeRebuildReasonTarget (NodeRebuildReason):

    __slots__ = (
        'entity',
    )

    def __init__(self, node_entity, target_entity):
        super(NodeRebuildReasonTarget, self).__init__(node_entity)
        self.entity = target_entity

    def get_description(self, brief):
        return "Node's target '%s' has changed." % (self.entity,)

# ==============================================================================


@pickleable
class NodeEntity (EntityBase):

    __slots__ = (
        'name',
        'signature',

        'builder',
        'source_entities',
        'dep_entities',

        'target_entities',
        'itarget_entities',
        'idep_entities',
        'idep_keys',
    )

    # -----------------------------------------------------------

    def __new__(cls,
                name=NotImplemented,
                signature=NotImplemented,
                targets=None,
                itargets=None,
                idep_keys=None,
                builder=None,
                source_entities=None,
                dep_entities=None):

        self = super(NodeEntity, cls).__new__(cls, name, signature)

        if targets is not None:
            self.target_entities = targets
            self.itarget_entities = itargets
            self.idep_keys = idep_keys
        else:
            self.builder = builder
            self.source_entities = source_entities
            self.dep_entities = dep_entities

        return self

    # -----------------------------------------------------------

    def get(self):
        return self.name

    # -----------------------------------------------------------

    def __getnewargs__(self):
        return (self.name,
                self.signature,
                self.target_entities,
                self.itarget_entities,
                self.idep_keys)

    # -----------------------------------------------------------

    def get_targets(self):
        builder = self.builder
        targets = builder.get_target_entities(self.source_entities)
        if not targets:
            return ()
        return builder.make_entities(targets)

    # -----------------------------------------------------------

    def get_name(self):

        hash_sum = new_hash(self.builder.name)

        name_entities = self.target_entities
        if not name_entities:
            name_entities = self.source_entities

        names = sorted(entity.id for entity in name_entities)
        for name in names:
            hash_sum.update(name)

        return hash_sum.digest()

    # -----------------------------------------------------------

    def get_signature(self):

        builder_signature = self.builder.signature
        if builder_signature is None:
            return None

        hash_sum = new_hash(builder_signature)

        for entity in self.dep_entities:
            ent_sign = entity.signature
            if not ent_sign:
                return None

            hash_sum.update(entity.id)
            hash_sum.update(ent_sign)

        for entity in self.source_entities:
            entity_signature = entity.signature
            if entity_signature is None:
                return None

            hash_sum.update(entity_signature)

        return hash_sum.digest()

    # -----------------------------------------------------------

    def __getattr__(self, attr):
        if attr == 'target_entities':
            self.target_entities = targets = self.get_targets()
            return targets

        return super(NodeEntity, self).__getattr__(attr)

    # -----------------------------------------------------------

    _ACTUAL_IDEPS_CACHE = {}

    def _get_ideps(self, vfile, idep_keys,
                   ideps_cache_get=_ACTUAL_IDEPS_CACHE.__getitem__,
                   ideps_cache_set=_ACTUAL_IDEPS_CACHE.__setitem__):

        entities = vfile.find_entities_by_key(idep_keys)
        if entities is None:
            raise NodeRebuildReasonImplicitDep(self)

        for i, entity in enumerate(entities):
            entity_id = entity.id

            try:
                entities[i] = ideps_cache_get(entity_id)
            except KeyError:
                actual_entity = entity.get_actual()
                ideps_cache_set(entity_id, actual_entity)

                if entity is not actual_entity:
                    vfile.update_entity(actual_entity)

                    raise NodeRebuildReasonImplicitDep(self, entity)

        return entities

    # -----------------------------------------------------------

    def _save_ideps(self, vfile,
                    _actual_ideps_cache_set=_ACTUAL_IDEPS_CACHE.setdefault):

        entities = []
        for entity in self.idep_entities:
            entity_id = entity.id
            cached_entity = _actual_ideps_cache_set(entity_id, entity)

            if cached_entity is entity:
                if entity.signature is None:
                    raise ErrorUnactualEntity(entity)

            entities.append(cached_entity)

        keys = vfile.add_entities(entities)

        self.idep_entities = entities
        self.idep_keys = keys

    # -----------------------------------------------------------

    def _check_targets(self, entities):
        if entities is None:
            raise NodeRebuildReasonNoTargets(self)

        for entity in entities:
            if not entity.is_actual():
                raise NodeRebuildReasonTarget(self, entity)

    # -----------------------------------------------------------

    def check_actual(self, vfile, explain):

        self.target_entities = []
        self.itarget_entities = []
        self.idep_entities = []

        try:
            previous = vfile.find_node_entity(self)

            if previous is None:
                raise NodeRebuildReasonNew(self)

            if not self.signature:
                raise NodeRebuildReasonAlways(self)

            if self.signature != previous.signature:
                raise NodeRebuildReasonSignature(self)

            ideps = self._get_ideps(vfile, previous.idep_keys)

            target_entities = previous.target_entities

            self._check_targets(target_entities)

            self.builder.check_actual(target_entities)

        except Exception as reason:
            if explain:
                event_node_rebuild_reason(reason)

            return False

        self.target_entities = target_entities
        self.itarget_entities = previous.itarget_entities
        self.idep_entities = ideps

        return True

    # -----------------------------------------------------------

    def save(self, vfile):

        for entity in self.target_entities:
            if entity.signature is None:
                raise ErrorUnactualEntity(entity)

        self._save_ideps(vfile)

        vfile.add_node_entity(self)

    # -----------------------------------------------------------

    def clear(self, vfile):
        """
        Clear produced target entities
        """

        self.idep_entities = tuple()

        node_entity = vfile.find_node_entity(self)

        if node_entity is None:
            self.itarget_entities = tuple()

        else:
            targets = node_entity.target_entities
            itargets = node_entity.itarget_entities

            if targets:
                self.target_entities = targets
            else:
                self.target_entities = tuple()

            if itargets:
                self.itarget_entities = itargets
            else:
                self.itarget_entities = tuple()

        try:
            self.builder.clear(self.target_entities, self.itarget_entities)
        except Exception:
            pass

    # -----------------------------------------------------------

    def add_targets(self, entities, tags=None):
        self.target_entities.extend(
            self.builder.make_entities(to_sequence(entities), tags))

    def add_target_files(self, entities, tags=None):
        self.target_entities.extend(
            self.builder.make_file_entities(to_sequence(entities), tags))

    add = add_targets
    add_files = add_target_files

    # -----------------------------------------------------------

    def add_side_effects(self, entities, tags=None):
        self.itarget_entities.extend(
            self.builder.make_entities(to_sequence(entities), tags))

    def add_side_effect_files(self, entities, tags=None):
        self.itarget_entities.extend(
            self.builder.make_file_entities(to_sequence(entities), tags))

    # -----------------------------------------------------------

    def add_implicit_deps(self, entities, tags=None):
        self.idep_entities.extend(
            self.builder.make_entities(to_sequence(entities), tags))

    def add_implicit_dep_files(self, entities, tags=None):
        self.idep_entities.extend(
            self.builder.make_file_entities(to_sequence(entities), tags))


# ==============================================================================

class _NodeBatchTargets (object):

    def __init__(self, node_entities_map):
        self.node_entities_map = node_entities_map

    # -----------------------------------------------------------

    def __getitem__(self, source):
        try:
            return self.node_entities_map[source]
        except KeyError:
            raise ErrorNodeUnknownSource(source)

# ==============================================================================


class NodeFilter (object):

    __slots__ = (
        'node',
        'node_attribute',
    )

    def __init__(self, node, node_attribute='target_entities'):
        self.node = node
        self.node_attribute = node_attribute

    # -----------------------------------------------------------

    def get_node(self):
        node = self.node

        while isinstance(node, NodeFilter):
            node = node.node

        return node

    # -----------------------------------------------------------

    def __iter__(self):
        raise TypeError()

    def __getitem__(self, item):
        return NodeIndexFilter(self, item)

    # -----------------------------------------------------------

    def get(self):

        entities = self.get_entities()
        if len(entities) == 1:
            return entities[0]

        return entities

    # -----------------------------------------------------------

    def get_entities(self):
        node = self.node
        if isinstance(node, NodeFilter):
            entities = node.get_entities()
        else:
            entities = getattr(node, self.node_attribute)

        return entities

# ==============================================================================


class NodeTagsFilter(NodeFilter):
    __slots__ = (
        'tags',
    )

    def __init__(self, node, tags, node_attribute='target_entities'):
        super(NodeTagsFilter, self).__init__(node, node_attribute)
        self.tags = frozenset(to_sequence(tags))

    def get_entities(self):
        entities = super(NodeTagsFilter, self).get_entities()

        tags = self.tags
        return tuple(entity for entity in entities
                     if entity.tags and (entity.tags & tags))

# ==============================================================================


class NodeIndexFilter(NodeFilter):
    __slots__ = (
        'index',
    )

    def __init__(self, node, index, node_attribute='target_entities'):
        super(NodeIndexFilter, self).__init__(node, node_attribute)
        self.index = index

    def get_entities(self):
        entities = super(NodeIndexFilter, self).get_entities()

        try:
            return to_sequence(entities[self.index])
        except IndexError:
            return tuple()


# ==============================================================================

class NodeDirNameFilter(NodeFilter):

    def get_entities(self):
        entities = super(NodeDirNameFilter, self).get_entities()
        return tuple(SimpleEntity(os.path.dirname(entity.get()))
                     for entity in entities)

# ==============================================================================


class NodeBaseNameFilter(NodeFilter):

    def get_entities(self):
        entities = super(NodeBaseNameFilter, self).get_entities()
        return tuple(SimpleEntity(os.path.basename(entity.get()))
                     for entity in entities)

# ==============================================================================

# noinspection PyAttributeOutsideInit


class Node (object):

    __slots__ = (
        'builder',
        'options',
        'cwd',

        'initiated',
        'depends_called',
        'replace_called',
        'split_called',
        'is_actual',

        'node_entities',
        'node_entities_map',

        'sources',
        'source_entities',

        'dep_nodes',
        'dep_entities',

        'target_entities',
        'itarget_entities',
        'idep_entities',
    )

    # -----------------------------------------------------------

    def __init__(self, builder, sources, cwd=None):

        self.builder = builder
        self.options = getattr(builder, 'options', None)

        if cwd is None:
            self.cwd = os.path.abspath(os.getcwd())
        else:
            self.cwd = cwd

        self.initiated = False
        self.depends_called = False
        self.replace_called = False
        self.split_called = False
        self.is_actual = False

        self.sources = tuple(to_sequence(sources))
        self.dep_nodes = set()
        self.dep_entities = []

    # ==========================================================

    def shrink(self):
        self.cwd = None
        self.dep_nodes = None
        self.sources = None
        self.node_entities = None
        self.node_entities_map = None

        self.builder = None
        self.options = None

    # ==========================================================

    def depends(self, dependencies):

        dep_nodes = self.dep_nodes
        dep_entities = self.dep_entities

        for entity in to_sequence(dependencies):
            if isinstance(entity, Node):
                dep_nodes.add(entity)

            elif isinstance(entity, NodeFilter):
                dep_nodes.add(entity.get_node())

            elif isinstance(entity, EntityBase):
                dep_entities.append(entity)

            else:
                raise ErrorNodeDependencyInvalid(entity)

    # ==========================================================

    def __getattr__(self, attr):
        if attr in ['target_entities', 'itarget_entities', 'idep_entities']:
            raise ErrorNoTargets(self)

        raise AttributeError("Node has not attribute '%s'" % (attr,))

    # ==========================================================

    def _set_source_entities(self):
        entities = []

        make_entity = self.builder.make_entity

        for src in self.sources:

            if isinstance(src, Node):
                entities += src.target_entities

            elif isinstance(src, NodeFilter):
                entities += src.get_entities()

            elif isinstance(src, EntityBase):
                entities.append(src)

            else:
                entity = make_entity(src)
                entities.append(entity)

        self.sources = None
        self.source_entities = tuple(entities)

    # ==========================================================

    def _update_dep_entities(self):
        dep_nodes = self.dep_nodes

        if not dep_nodes:
            return

        dep_entities = self.dep_entities

        for node in dep_nodes:
            target_entities = node.target_entities
            if target_entities:
                dep_entities.extend(target_entities)

        dep_nodes.clear()

        dep_entities.sort(key=operator.attrgetter('id'))

    # ==========================================================

    def initiate(self, chdir=os.chdir):
        if self.initiated:
            # reinitialize the replaced source entities
            if self.sources:
                self._set_source_entities()
        else:
            chdir(self.cwd)

            self.builder = self.builder.initiate()
            self._set_source_entities()
            self._update_dep_entities()

            self.initiated = True

    # ==========================================================

    def build_depends(self, chdir=os.chdir):
        if self.depends_called:
            return None

        self.depends_called = True

        chdir(self.cwd)
        nodes = self.builder.depends(self.source_entities)
        return nodes

    # ==========================================================

    def build_replace(self, chdir=os.chdir):
        if self.replace_called:
            return None

        self.replace_called = True

        chdir(self.cwd)
        sources = self.builder.replace(self.source_entities)
        if sources is None:
            return False

        # source_entities will be reinitialized later
        self.sources = tuple(to_sequence(sources))

        return self.get_source_nodes()

    # ==========================================================

    def _split_batch(self, vfile, explain):
        builder = self.builder
        dep_entities = self.dep_entities
        node_entities = []
        not_actual_nodes = {}
        not_actual_sources = []
        for src in self.source_entities:
            node_entity = NodeEntity(builder=builder,
                                     source_entities=(src,),
                                     dep_entities=dep_entities)

            if not node_entity.check_actual(vfile, explain):
                not_actual_nodes[src] = node_entity
                not_actual_sources.append(src)

            node_entities.append(node_entity)

        self.node_entities = node_entities
        # we don't need to check actual status anymore
        self.is_actual = True

        if not not_actual_nodes:
            return None

        groups = builder.split_batch(not_actual_sources)
        if not groups:
            # this should never happen, looks like a bug in the builder or
            # Aqualid
            groups = not_actual_sources

        split_nodes = []

        for group in groups:
            group = tuple(to_sequence(group))

            node_entities = tuple(not_actual_nodes[src] for src in group)
            node = self._split(group, node_entities)
            node.node_entities_map = not_actual_nodes

            split_nodes.append(node)

        return split_nodes

    # ==========================================================

    def build_split(self, vfile, explain):
        if self.split_called:
            return None

        self.split_called = True

        builder = self.builder
        dep_entities = self.dep_entities

        if builder.is_batch():
            return self._split_batch(vfile, explain)

        # -----------------------------------------------------------
        sources = self.source_entities

        groups = self.builder.split(sources)

        # No source groups, just build the sources
        if (not groups) or (len(groups) < 2):
            node_entity = NodeEntity(builder=builder,
                                     source_entities=sources,
                                     dep_entities=dep_entities)

            self.is_actual = node_entity.check_actual(vfile, explain)
            self.node_entities = (node_entity,)
            return None

        # -----------------------------------------------------------
        # create split Nodes

        node_entities = []
        split_nodes = []
        for group in groups:

            group = to_sequence(group)

            node_entity = NodeEntity(builder=builder,
                                     source_entities=group,
                                     dep_entities=dep_entities)

            if not node_entity.check_actual(vfile, explain):
                node = self._split(group, (node_entity,))
                split_nodes.append(node)

            node_entities.append(node_entity)

        self.node_entities = node_entities
        # we don't need to check actual status anymore
        self.is_actual = True

        return split_nodes

    # ==========================================================

    def _split(self, source_entities, node_entities):

        other = object.__new__(self.__class__)

        other.builder = self.builder
        other.dep_nodes = ()
        other.sources = ()
        other.source_entities = source_entities
        other.node_entities = node_entities
        other.initiated = True
        other.depends_called = True
        other.replace_called = True
        other.split_called = True
        other.is_actual = False

        return other

    # ==========================================================

    def prebuild(self):
        dep_nodes = self.build_depends()
        if dep_nodes:
            return dep_nodes

        source_nodes = self.build_replace()
        return source_nodes

    # ==========================================================

    def _populate_targets(self):

        node_entities = self.node_entities

        if len(node_entities) == 1:
            node_entity = node_entities[0]

            self.target_entities = node_entity.target_entities
            self.itarget_entities = node_entity.itarget_entities
            self.idep_entities = node_entity.idep_entities

        else:
            targets = []
            itargets = []
            ideps = []

            for node_entity in self.node_entities:
                targets += node_entity.target_entities
                itargets += node_entity.itarget_entities
                ideps += node_entity.idep_entities

            self.target_entities = targets
            self.itarget_entities = itargets
            self.idep_entities = ideps

    # ==========================================================

    def check_actual(self, vfile, explain):

        if self.is_actual is None:
            for node_entity in self.node_entities:
                if not node_entity.check_actual(vfile, explain):
                    return False

            self.is_actual = True

        elif not self.is_actual:
            return False

        self._populate_targets()
        return True

    # ==========================================================

    def recheck_actual(self):
        self.is_actual = None

    # ==========================================================

    def build(self):

        builder = self.builder
        if builder.is_batch():
            targets = _NodeBatchTargets(self.node_entities_map)
            output = builder.build_batch(self.source_entities, targets)
        else:
            targets = self.node_entities
            output = builder.build(self.source_entities, targets[0])

        self._populate_targets()

        return output

    # ==========================================================

    def save(self, vfile):

        for node_entity in self.node_entities:
            node_entity.save(vfile)

    # ==========================================================

    def save_failed(self, vfile):

        node_entities = self.node_entities
        # do not save if only one node regardless targets
        if len(node_entities) < 2:
            return

        for node_entity in node_entities:
            # only nodes with targets should be saved
            if node_entity.target_entities:
                # nodes without targets will be rebuilt next time
                node_entity.save(vfile)

    # ==========================================================

    def _clear_split(self):

        builder = self.builder

        source_entities = self.source_entities
        if builder.is_batch():
            groups = source_entities
        else:
            groups = self.builder.split(source_entities)
            if not groups:
                groups = source_entities

        node_entities = []
        for group in groups:
            group = to_sequence(group)

            node_entity = NodeEntity(builder=builder,
                                     source_entities=group,
                                     dep_entities=())

            node_entities.append(node_entity)

        self.node_entities = node_entities

    # ==========================================================

    def clear(self, vfile):

        self._clear_split()

        node_entities = []

        for node_entity in self.node_entities:
            node_entity.clear(vfile)
            node_entities.append(node_entity)

        self._populate_targets()

        return node_entities

    # ==========================================================

    def get_weight(self):
        return self.builder.get_weight(self.source_entities)

    # ==========================================================

    def get_names(self):
        return (entity.name for entity in self.node_entities)

    def get_names_and_signatures(self):
        return ((entity.name, entity.signature)
                for entity in self.node_entities)

    # ==========================================================

    def get_dep_nodes(self):
        return self.dep_nodes

    # ==========================================================

    def get_sources(self):
        return tuple(src.get() for src in self.get_source_entities())

    # ==========================================================

    def get_source_entities(self):
        return self.source_entities

    # ==========================================================

    def get_source_nodes(self):
        nodes = []

        for src in self.sources:
            if isinstance(src, Node):
                nodes.append(src)

            elif isinstance(src, NodeFilter):
                nodes.append(src.get_node())

        return nodes

    # ==========================================================

    def is_built(self):
        return self.builder is None

    # ==========================================================

    def at(self, tags):
        return NodeTagsFilter(self, tags)

    # ==========================================================

    def __iter__(self):
        raise TypeError()

    def __getitem__(self, item):
        return NodeIndexFilter(self, item)

    # ==========================================================

    def __filter(self, node_attribute, tags):
        if tags is None:
            return NodeFilter(self, node_attribute)

        return NodeTagsFilter(self, tags, node_attribute)

    # ==========================================================

    def filter_sources(self, tags=None):
        return self.__filter('source_entities', tags)

    def filter_side_effects(self, tags=None):
        return self.__filter('itarget_entities', tags)

    def filter_implicit_dependencies(self, tags=None):
        return self.__filter('idep_entities', tags)

    def filter_dependencies(self, tags=None):
        return self.__filter('dep_entities', tags)

    # ==========================================================

    def get(self):
        targets = self.get_target_entities()
        if len(targets) == 1:
            return targets[0].get()

        return tuple(target.get() for target in targets)

    # ==========================================================

    def get_target_entities(self):
        return self.target_entities

    def get_side_effect_entities(self):
        return self.itarget_entities

    # ==========================================================

    def get_build_str(self, brief=True):
        try:
            targets = getattr(self, 'target_entities', None)

            return self.builder.get_trace(self.source_entities, targets, brief)

        except Exception as ex:
            if 'BuilderInitiator' not in str(ex):
                raise

        return str(self)  # TODO: return raw data

    # ==========================================================

    def print_sources(self):    # noqa
        result = []
        sources = self.sources
        if not sources:
            sources = self.source_entities

        for src in sources:
            if isinstance(src, EntityBase):
                result.append(src.get())

            elif isinstance(src, Node):
                targets = getattr(src, 'target_entities', None)
                if targets is not None:
                    result += (target.get() for target in targets)
                else:
                    result.append(src)

            elif isinstance(src, NodeFilter):
                try:
                    targets = src.get_entities()
                except AttributeError:
                    continue

                if targets is not None:
                    result += (target.get() for target in targets)
                else:
                    result.append(src)

            else:
                result.append(src)

        sources_str = ', '.join(map(str, result))

        log_info("node '%s' sources: %s" % (self, sources_str))

    # ==========================================================

    def print_targets(self):
        targets = [t.get() for t in getattr(self, 'target_entities', [])]
        log_info("node '%s' targets: %s" % (self, targets))
