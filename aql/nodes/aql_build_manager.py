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


import os.path
import itertools

from aql.utils import event_status, event_warning, event_error,\
    log_info, log_error, log_warning, TaskManager
from aql.entity import EntitiesFile

__all__ = (
    'BuildManager',
    'ErrorNodeDependencyCyclic', 'ErrorNodeDependencyUnknown',
)

# ==============================================================================


@event_warning
def event_build_target_twice(settings, entity, node1):
    log_warning("Target '%s' is built twice. The last time built by: '%s' " %
               (entity.name, node1.get_build_str(settings.brief)))

# ==============================================================================


@event_error
def event_failed_node(settings, node, error):

    msg = node.get_build_str(settings.brief)
    msg += '\n\n%s\n' % (error,)

    log_error(msg)

# ==============================================================================


@event_status
def event_node_building(settings, node):
    pass

# ==============================================================================


@event_status
def event_node_building_finished(settings, node, builder_output, progress):

    msg = node.get_build_str(settings.brief)
    if settings.with_output and builder_output:
        msg += '\n'
        if builder_output:
            msg += builder_output
            msg += '\n'

    msg = "(%s) %s" % (progress, msg)

    log_info(msg)

# ==============================================================================


@event_status
def event_node_building_failed(settings, node, error):
    pass

# ==============================================================================


@event_status
def event_node_removed(settings, node, progress):
    msg = node.get_build_str(settings.brief)
    if msg:
        log_info("(%s) Removed: %s" % (progress, msg))

# ==============================================================================


class ErrorNodeDependencyCyclic(Exception):

    def __init__(self, node, deps):
        msg = "Node '%s' (%s) has a cyclic dependency: %s" % (
            node, node.get_build_str(True), deps)
        super(ErrorNodeDependencyCyclic, self).__init__(msg)

# ==============================================================================


class ErrorNodeUnknown(Exception):

    def __init__(self, node):
        msg = "Unknown node '%s'" % (node, )
        super(ErrorNodeUnknown, self).__init__(msg)

# ==============================================================================


class ErrorNodeSignatureDifferent(Exception):

    def __init__(self, node):
        msg = "Two similar nodes have different signatures" \
              "(sources, builder parameters or dependencies): %s" % \
              (node.get_build_str(brief=False), )
        super(ErrorNodeSignatureDifferent, self).__init__(msg)

# ==============================================================================


class ErrorNodeDependencyUnknown(Exception):

    def __init__(self, node, dep_node):
        msg = "Unable to add dependency to node '%s' from node '%s'" % (
            node, dep_node)
        super(ErrorNodeDependencyUnknown, self).__init__(msg)

# ==============================================================================


class InternalErrorRemoveNonTailNode(Exception):

    def __init__(self, node):
        msg = "Removing non-tail node: %s" % (node,)
        super(InternalErrorRemoveNonTailNode, self).__init__(msg)

# ==============================================================================


class InternalErrorRemoveUnknownTailNode(Exception):

    def __init__(self, node):
        msg = "Remove unknown tail node: : %s" % (node,)
        super(InternalErrorRemoveUnknownTailNode, self).__init__(msg)

# ==============================================================================


class _NodesTree (object):

    __slots__ = (
        'node2deps',
        'dep2nodes',
        'tail_nodes',
    )

    # -----------------------------------------------------------

    def __init__(self):
        self.node2deps = {}
        self.dep2nodes = {}
        self.tail_nodes = set()

    # -----------------------------------------------------------

    def __len__(self):
        return len(self.node2deps)

    def get_nodes(self):
        return frozenset(self.node2deps)

    # -----------------------------------------------------------

    def __has_cycle(self, node, new_deps):

        if node in new_deps:
            return True

        deps = set(new_deps)
        node2deps = self.node2deps

        while deps:
            dep = deps.pop()

            dep_deps = node2deps[dep]

            if node in dep_deps:
                return True

            deps |= dep_deps

        return False

    # -----------------------------------------------------------

    def _depends(self, node, deps):

        node2deps = self.node2deps
        dep2nodes = self.dep2nodes

        try:
            current_node_deps = node2deps[node]

            deps = set(dep for dep in deps if not dep.is_built())
            new_deps = deps - current_node_deps

            if not new_deps:
                return

            if self.__has_cycle(node, new_deps):
                raise ErrorNodeDependencyCyclic(node, new_deps)

            self.tail_nodes.discard(node)

            # -----------------------------------------------------------

            current_node_deps.update(new_deps)

            # -----------------------------------------------------------

            for dep in new_deps:
                dep2nodes[dep].add(node)

        except KeyError as dep_node:
            raise ErrorNodeDependencyUnknown(node, dep_node.args[0])

    # -----------------------------------------------------------

    def add(self, nodes):
        for node in nodes:
            if node not in self.node2deps:
                self.node2deps[node] = set()
                self.dep2nodes[node] = set()
                self.tail_nodes.add(node)

                node_srcnodes = node.get_source_nodes()
                node_depnodes = node.get_dep_nodes()

                # recursively add sources and depends
                self.add(node_srcnodes)
                # TODO: It would be better to rewrite this code to avoid the
                # recursion
                self.add(node_depnodes)

                self._depends(node, node_srcnodes)
                self._depends(node, node_depnodes)

    # -----------------------------------------------------------

    def depends(self, node, deps):
        self.add(deps)
        self._depends(node, deps)

    # -----------------------------------------------------------

    def remove_tail(self, node):
        node2deps = self.node2deps

        try:
            deps = node2deps.pop(node)
            if deps:
                raise InternalErrorRemoveNonTailNode(node)
        except KeyError as node:
            raise InternalErrorRemoveUnknownTailNode(node.args[0])

        tail_nodes = self.tail_nodes

        for dep in self.dep2nodes.pop(node):
            d = node2deps[dep]
            d.remove(node)
            if not d:
                tail_nodes.add(dep)

    # -----------------------------------------------------------

    def filter_unknown_deps(self, deps):
        return [dep for dep in deps if dep in self.node2deps]

    # -----------------------------------------------------------

    def pop_tails(self):
        tails = self.tail_nodes
        self.tail_nodes = set()
        return tails

    # -----------------------------------------------------------

    def __get_all_nodes(self, nodes):
        nodes = set(nodes)
        all_nodes = set(nodes)

        node2deps = self.node2deps
        while nodes:
            node = nodes.pop()

            try:
                deps = node2deps[node] - all_nodes
            except KeyError as node:
                raise ErrorNodeUnknown(node.args[0])

            all_nodes.update(deps)
            nodes.update(deps)

        return all_nodes

    # -----------------------------------------------------------

    def shrink_to(self, nodes):

        node2deps = self.node2deps
        dep2nodes = self.dep2nodes

        ignore_nodes = set(node2deps) - self.__get_all_nodes(nodes)

        self.tail_nodes -= ignore_nodes

        for node in ignore_nodes:
            del node2deps[node]
            del dep2nodes[node]

        for dep_nodes in dep2nodes.values():
            dep_nodes.difference_update(ignore_nodes)

    # -----------------------------------------------------------

    def self_test(self):
        if set(self.node2deps) != set(self.dep2nodes):
            raise AssertionError("Not all deps are added")

        all_dep_nodes = set()

        for node in self.dep2nodes:
            if node not in self.node2deps:
                raise AssertionError("Missed node: %s" % (node,))

            node_deps = self.node2deps[node]

            if node_deps:
                if node in self.tail_nodes:
                    raise AssertionError("Invalid tail node: %s" % (node,))

            all_dep_nodes |= node_deps

            for dep in node_deps:
                if node not in self.dep2nodes[dep]:
                    raise AssertionError(
                        "node not in self.dep2nodes[dep]: "
                        "dep: %s, node: %s" % (dep, node))

        if all_dep_nodes - set(self.dep2nodes):
            raise AssertionError("Not all deps are added")

# ==============================================================================


class _VFiles(object):
    __slots__ = (
        'names',
        'handles',
        'use_sqlite',
        'force_lock',
    )

    # -----------------------------------------------------------

    def __init__(self, use_sqlite=False, force_lock=False):
        self.handles = {}
        self.names = {}
        self.use_sqlite = use_sqlite
        self.force_lock = force_lock

    # -----------------------------------------------------------

    def __iter__(self):
        raise TypeError()

    # -----------------------------------------------------------

    def __getitem__(self, builder):

        builder_name = builder.name

        try:
            vfilename = self.names[builder_name]
        except KeyError:
            vfilename = os.path.join(builder.get_build_dir(), '.aql.db')
            self.names[builder_name] = vfilename

        try:
            return self.handles[vfilename]

        except KeyError:
            vfile = EntitiesFile(
                vfilename, use_sqlite=self.use_sqlite, force=self.force_lock)
            self.handles[vfilename] = vfile

            return vfile

    # -----------------------------------------------------------

    def close(self):
        for vfile in self.handles.values():
            vfile.close()

        self.handles.clear()
        self.names.clear()

    # -----------------------------------------------------------

    def __enter__(self):
        return self

    # -----------------------------------------------------------

    def __exit__(self, exc_type, exc_value, backtrace):
        self.close()

# ==============================================================================


def _build_node(node):

    event_node_building(node)

    out = node.build()

    if out:
        try:
            out = out.strip()
        except Exception:
            pass

    return out

# ==============================================================================


def _get_module_nodes(node, module_cache, node_cache):
    try:
        return module_cache[node]
    except KeyError:
        pass

    result = set((node,))

    try:
        src_nodes = node_cache[node]
    except KeyError:
        node_cache[node] = src_nodes = frozenset(node.get_source_nodes())

    for src in src_nodes:
        result.update(_get_module_nodes(src, module_cache, node_cache))

    module_cache[node] = result
    return result

# ==============================================================================


def _get_leaf_nodes(nodes, exclude_nodes, node_cache):
    leafs = set()
    for node in nodes:
        if node_cache[node].issubset(exclude_nodes):
            leafs.add(node)

    return leafs

# ==============================================================================


class _NodeLocker(object):
    __slots__ = (
        'node2deps',
        'dep2nodes',
        'locked_nodes',
        'unlocked_nodes',
    )

    def __init__(self):
        self.node2deps = {}
        self.dep2nodes = {}
        self.locked_nodes = {}
        self.unlocked_nodes = []

    # -----------------------------------------------------------

    def sync_modules(self, nodes, module_cache=None, node_cache=None):

        if module_cache is None:
            module_cache = {}

        if node_cache is None:
            node_cache = {}

        for node1, node2 in itertools.product(nodes, nodes):
            if node1 is not node2:
                self.__add_modules(node1, node2, module_cache, node_cache)

    # -----------------------------------------------------------

    def __add_modules(self, node1, node2, module_cache, node_cache):

        node1_sources = _get_module_nodes(node1, module_cache, node_cache)
        node2_sources = _get_module_nodes(node2, module_cache, node_cache)

        common = node1_sources & node2_sources
        node1_sources -= common
        node2_sources -= common

        leafs1 = _get_leaf_nodes(node1_sources, common, node_cache)
        leafs2 = _get_leaf_nodes(node2_sources, common, node_cache)

        for leaf in leafs1:
            self.__add(leaf, node2_sources)

        for leaf in leafs2:
            self.__add(leaf, node1_sources)

    # -----------------------------------------------------------

    def sync(self, nodes):
        for node in nodes:
            node_deps = self.__add(node, nodes)
            node_deps.remove(node)

    # -----------------------------------------------------------

    def __add(self, node, deps):
        try:
            node_set = self.node2deps[node]
        except KeyError:
            node_set = set()
            self.node2deps[node] = node_set

        node_set.update(deps)

        for dep in deps:
            if dep is not node:
                try:
                    dep_set = self.dep2nodes[dep]
                except KeyError:
                    dep_set = set()
                    self.dep2nodes[dep] = dep_set

                dep_set.add(node)

        return node_set

    # -----------------------------------------------------------

    def lock(self, node):

        deps = self.node2deps.get(node, None)
        if not deps:
            # node doesn't have to be synchronized
            return True

        locked_nodes = self.locked_nodes

        for dep in deps:
            if dep in locked_nodes:
                locked_nodes[dep].add(node)
                return False

        self.locked_nodes[node] = set()

        return True

    # -----------------------------------------------------------

    def unlock(self, node):

        deps = self.node2deps.pop(node, ())
        nodes = self.dep2nodes.pop(node, ())
        if not deps and not nodes:
            return

        for dep in deps:
            self.dep2nodes[dep].remove(node)

        for dep in nodes:
            self.node2deps[dep].remove(node)

        unlocked_nodes = self.locked_nodes.pop(node, None)
        if not unlocked_nodes:
            return

        self.unlocked_nodes.extend(unlocked_nodes)

    # -----------------------------------------------------------

    def pop_unlocked(self):
        unlocked_nodes = self.unlocked_nodes
        self.unlocked_nodes = []

        return unlocked_nodes

    # -----------------------------------------------------------

    def self_test(self):
        for node, deps in self.node2deps.items():
            if node in deps:
                raise AssertionError("Node depends from itself: %s" % (node,))

            for dep in deps:
                if node not in self.dep2nodes[dep]:
                    raise AssertionError(
                        "Dependency '%s' doesn't have node '%s'" %
                        (dep, node,))

        for node, deps in self.locked_nodes.items():
            for dep in deps:
                if node not in self.node2deps[dep]:
                    raise AssertionError(
                        "Locked node %s doesn't actually depend from node %s" %
                        (dep, node))

                if dep in self.unlocked_nodes:
                    raise AssertionError(
                        "Locked node %s is actually locked" % (dep,))

        for node in self.unlocked_nodes:
            if node not in self.node2deps:
                raise AssertionError("Unknown unlocked node %s" % (node,))


# ==============================================================================

class _NodesBuilder (object):

    __slots__ = (
        'vfiles',
        'build_manager',
        'task_manager',
        'building_nodes',
    )

    # -----------------------------------------------------------

    def __init__(self,
                 build_manager,
                 jobs=0,
                 keep_going=False,
                 with_backtrace=True,
                 use_sqlite=False,
                 force_lock=False
                 ):

        self.vfiles = _VFiles(use_sqlite=use_sqlite, force_lock=force_lock)
        self.building_nodes = {}
        self.build_manager = build_manager
        self.task_manager = TaskManager(num_threads=jobs,
                                        stop_on_fail=not keep_going,
                                        with_backtrace=with_backtrace)

    # -----------------------------------------------------------

    def __enter__(self):
        return self

    # -----------------------------------------------------------

    def __exit__(self, exc_type, exc_value, backtrace):
        self.close()

    # -----------------------------------------------------------

    def _add_building_node(self, node):
        conflicting_nodes = []
        building_nodes = self.building_nodes

        node_names = {}

        for name, signature in node.get_names_and_signatures():
            other = building_nodes.get(name, None)
            if other is None:
                node_names[name] = (node, signature)
                continue

            other_node, other_signature = other
            if other_signature != signature:
                raise ErrorNodeSignatureDifferent(node)

            conflicting_nodes.append(other_node)

        if conflicting_nodes:
            node.recheck_actual()
            self.build_manager.depends(node, conflicting_nodes)
            return False

        building_nodes.update(node_names)
        return True

    # -----------------------------------------------------------

    def _remove_building_node(self, node):
        building_nodes = self.building_nodes
        for name in node.get_names():
            del building_nodes[name]

    # -----------------------------------------------------------

    def is_building(self):
        return bool(self.building_nodes)

    # -----------------------------------------------------------

    def build(self, nodes):

        build_manager = self.build_manager
        explain = build_manager.explain

        vfiles = self.vfiles
        add_task = self.task_manager.add_task

        tasks_check_period = 10
        added_tasks = 0
        changed = False

        for node in nodes:
            if not build_manager.lock_node(node):
                continue

            node.initiate()

            vfile = vfiles[node.builder]

            prebuit_nodes = node.prebuild()
            if prebuit_nodes:
                build_manager.depends(node, prebuit_nodes)
                changed = True
                continue

            split_nodes = node.build_split(vfile, explain)
            if split_nodes:
                build_manager.depends(node, split_nodes)
                changed = True
                continue

            actual = node.check_actual(vfile, explain)

            force_rebuild = build_manager.check_force_rebuild(node)

            if actual and not force_rebuild:
                build_manager.actual_node(node)
                changed = True
                continue

            if not self._add_building_node(node):
                continue

            add_task(-node.get_weight(), node, _build_node, node)

            added_tasks += 1

            if added_tasks == tasks_check_period:
                changed = self._get_finished_nodes(block=False) or changed
                added_tasks = 0

        return self._get_finished_nodes(block=not changed)

    # -----------------------------------------------------------

    def _get_finished_nodes(self, block=True):
        finished_tasks = self.task_manager.get_finished_tasks(block=block)

        vfiles = self.vfiles

        build_manager = self.build_manager

        for task in finished_tasks:

            node = task.task_id
            error = task.error

            self._remove_building_node(node)

            vfile = vfiles[node.builder]

            if error is None:
                node.save(vfile)
                build_manager.completed_node(node, task.result)
            else:
                node.save_failed(vfile)
                build_manager.failed_node(node, error)

        # return false when there are no more task processing threads
        return finished_tasks or not block

    # -----------------------------------------------------------

    def clear(self, nodes):

        vfiles = self.vfiles
        build_manager = self.build_manager

        remove_entities = {}

        for node in nodes:

            node.initiate()

            prebuit_nodes = node.prebuild()
            if prebuit_nodes:
                build_manager.depends(node, prebuit_nodes)
                continue

            vfile = vfiles[node.builder]
            node_entities = node.clear(vfile)

            remove_entities.setdefault(vfile, []).extend(node_entities)

            build_manager.removed_node(node)

        for vfile, entities in remove_entities.items():
            vfile.remove_node_entities(entities)

    # -----------------------------------------------------------

    def close(self):
        try:
            self.task_manager.stop()
            self._get_finished_nodes(block=False)
        finally:
            self.vfiles.close()

# ==============================================================================


class BuildManager (object):

    __slots__ = (
        '_nodes',
        '_built_targets',
        '_failed_nodes',
        '_built_node_names',
        '_node_locker',
        '_module_cache',
        '_node_cache',
        'completed',
        'actual',
        'explain',
    )

    # -----------------------------------------------------------

    def __init__(self):
        self._nodes = _NodesTree()
        self._node_locker = None
        self.__reset()

    # -----------------------------------------------------------

    def __reset(self, build_always=False, explain=False):

        self._built_targets = {}
        self._failed_nodes = {}
        self._module_cache = {}
        self._node_cache = {}
        self._built_node_names = set() if build_always else None

        self.completed = 0
        self.actual = 0
        self.explain = explain

    # -----------------------------------------------------------

    def add(self, nodes):
        self._nodes.add(nodes)

    # -----------------------------------------------------------

    def depends(self, node, deps):
        self._nodes.depends(node, deps)

    # -----------------------------------------------------------

    def module_depends(self, node, deps):
        module_cache = self._module_cache
        node_cache = self._node_cache

        module_nodes = _get_module_nodes(node, module_cache, node_cache)

        for dep in deps:
            dep_nodes = _get_module_nodes(dep, module_cache, node_cache)

            common = module_nodes & dep_nodes
            only_module_nodes = module_nodes - common

            leafs = _get_leaf_nodes(only_module_nodes, common, node_cache)

            for leaf in leafs:
                self._nodes.depends(leaf, (dep,))

    # -----------------------------------------------------------

    def sync(self, nodes, deep=False):
        node_locker = self._node_locker
        if node_locker is None:
            self._node_locker = node_locker = _NodeLocker()

        if deep:
            node_locker.sync_modules(
                nodes, self._module_cache, self._node_cache)
        else:
            node_locker.sync(nodes)

    # -----------------------------------------------------------

    def lock_node(self, node):
        node_locker = self._node_locker
        if node_locker is None:
            return True

        return node_locker.lock(node)

    # -----------------------------------------------------------

    def unlock_node(self, node):
        node_locker = self._node_locker
        if node_locker is not None:
            node_locker.unlock(node)

    # -----------------------------------------------------------

    def __len__(self):
        return len(self._nodes)

    # -----------------------------------------------------------

    def self_test(self):
        self._nodes.self_test()
        if self._node_locker is not None:
            self._node_locker.self_test()

    # -----------------------------------------------------------

    def get_next_nodes(self):
        tails = self._nodes.pop_tails()

        if not tails:
            node_locker = self._node_locker
            if node_locker is not None:
                return node_locker.pop_unlocked()

        return tails

    # -----------------------------------------------------------

    def check_force_rebuild(self, node):
        built_names = self._built_node_names
        if built_names is None:
            return False

        names = frozenset(node.get_names())

        result = not names.issubset(built_names)

        built_names.update(names)

        return result

    # -----------------------------------------------------------

    def actual_node(self, node):
        self.unlock_node(node)
        self._nodes.remove_tail(node)
        self.actual += 1

        node.shrink()

    # -----------------------------------------------------------

    def completed_node(self, node, builder_output):
        self._check_already_built(node)
        self.unlock_node(node)
        self._nodes.remove_tail(node)

        self.completed += 1

        event_node_building_finished(node, builder_output, self.get_progress_str())

        node.shrink()

    # -----------------------------------------------------------

    def failed_node(self, node, error):
        self.unlock_node(node)
        self._failed_nodes[node] = error

        event_node_building_failed(node, error)

    # -----------------------------------------------------------

    def removed_node(self, node):
        self._nodes.remove_tail(node)
        self.completed += 1

        event_node_removed(node, self.get_progress_str())

        node.shrink()

    # -----------------------------------------------------------

    def get_progress_str(self):
        done = self.completed + self.actual
        total = len(self._nodes) + done

        processed = done + len(self._failed_nodes)

        progress = "%s/%s" % (processed, total)
        return progress

    # -----------------------------------------------------------

    def close(self):
        self._nodes = _NodesTree()

    # -----------------------------------------------------------

    def _check_already_built(self, node):
        entities = node.get_target_entities()

        built_targets = self._built_targets

        for entity in entities:
            entity_sign = entity.signature
            other_entity_sign = built_targets.setdefault(
                entity.id, entity_sign)

            if other_entity_sign != entity_sign:
                event_build_target_twice(entity, node)

    # -----------------------------------------------------------

    def shrink(self, nodes):
        if not nodes:
            return

        self._nodes.shrink_to(nodes)

    # -----------------------------------------------------------

    def get_nodes(self):
        return self._nodes.get_nodes()

    # -----------------------------------------------------------

    def build(self,
              jobs,
              keep_going,
              nodes=None,
              build_always=False,
              explain=False,
              with_backtrace=True,
              use_sqlite=False,
              force_lock=False
              ):

        self.__reset(build_always=build_always, explain=explain)

        self.shrink(nodes)

        with _NodesBuilder(self,
                           jobs,
                           keep_going,
                           with_backtrace,
                           use_sqlite=use_sqlite,
                           force_lock=force_lock) as nodes_builder:
            while True:
                tails = self.get_next_nodes()

                if not tails and not nodes_builder.is_building():
                    break

                if not nodes_builder.build(tails):
                    # no more processing threads
                    break

        return self.is_ok()

    # -----------------------------------------------------------

    def is_ok(self):
        return not bool(self._failed_nodes)

    # -----------------------------------------------------------

    def fails_count(self):
        return len(self._failed_nodes)

    # -----------------------------------------------------------

    def print_fails(self):
        for node, error in self._failed_nodes.items():
            event_failed_node(node, error)

    # -----------------------------------------------------------

    def print_build_state(self):
        log_info("Failed nodes: %s" % len(self._failed_nodes))
        log_info("Completed nodes: %s" % self.completed)
        log_info("Actual nodes: %s" % self.actual)

    # -----------------------------------------------------------

    def clear(self, nodes=None, use_sqlite=False, force_lock=False):

        self.__reset()

        self.shrink(nodes)

        with _NodesBuilder(self,
                           use_sqlite=use_sqlite,
                           force_lock=force_lock) as nodes_builder:
            while True:

                tails = self.get_next_nodes()

                if not tails:
                    break

                nodes_builder.clear(tails)
