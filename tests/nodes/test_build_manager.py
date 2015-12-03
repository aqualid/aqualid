import os.path
import time
import threading
import operator

from aql_testcase import AqlTestCase, skip

from aql.util_types import encode_str
from aql.utils import file_checksum, Tempdir, \
    add_user_handler, remove_user_handler

from aql.entity import SimpleEntity, FileChecksumEntity
from aql.options import builtin_options, BoolOptionType
from aql.nodes import Node, Builder, FileBuilder, BuildManager
from aql.nodes.aql_build_manager import ErrorNodeDependencyCyclic,\
    ErrorNodeSignatureDifferent, ErrorNodeDuplicateNames


# ==============================================================================
class FailedBuilder (Builder):

    def build(self, source_entities, targets):
        raise Exception("Builder always fail.")


# ==============================================================================
class ValueBuilder (Builder):

    def build(self, source_entities, targets):

        value = '-'.join(map(str, map(operator.methodcaller('get'),
                                      source_entities)))

        targets.add_targets(value)


# ==============================================================================
class ExpensiveValueBuilder (Builder):

    __slots__ = (
        'event',
        'do_expensive',
    )

    def __init__(self, options, event, do_expensive):
        self.event = event
        self.do_expensive = do_expensive

    # ----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        if self.do_expensive:
            return "Heavy"
        return "Light"

    # ----------------------------------------------------------

    def split(self, source_entities):
        return self.split_single(source_entities)

    # ----------------------------------------------------------

    def build(self, source_entities, targets):

        if self.event.wait(1):
            raise Exception("Concurrent run")

        if self.do_expensive:
            self.event.set()
            time.sleep(1)  # doing a heavy work
            self.event.clear()
        else:
            time.sleep(0.5)

        value = '-'.join(map(str, map(operator.methodcaller('get'),
                                      source_entities)))

        targets.add_targets(value)


# ==============================================================================
class CondBuilder (Builder):

    def build(self, source_entities, targets):
        value = source_entities[0].get()
        targets.add_targets(value)

# ==============================================================================

_sync_lock = threading.Lock()
_sync_value = 0


class SyncValueBuilder (Builder):
    NAME_ATTRS = ('name',)

    def __init__(self, options, name, number, sleep_interval=1):
        self.signature = b''

        self.name = encode_str(name)
        self.sleep_interval = sleep_interval
        self.number = number

        # self.init_locks( lock_names )

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        name = self.__class__.__name__
        name += "(%s:%s)" % (self.name, self.number,)
        return name

    # -----------------------------------------------------------

    def init_locks(self, lock_names, sync_locks):
        self.locks = locks = []
        self.lock_names = lock_names

        for lock_name in lock_names:
            lock = sync_locks.get(lock_name, None)
            if lock is None:
                lock = threading.Lock()
                sync_locks[lock_name] = lock

            locks.append(lock)

    # -----------------------------------------------------------

    def acquire_locks(self):
        locks = []

        try:
            for i, lock in enumerate(self.locks):
                if not lock.acquire(False):
                    raise Exception("Lock '%s' is already acquired." %
                                    (self.lock_names[i]))

                locks.insert(0, lock)
        except:
            self.release_locks(locks)
            raise

        return locks

    # -----------------------------------------------------------

    @staticmethod
    def release_locks(locks):
        for lock in locks:
            lock.release()

    # -----------------------------------------------------------

    def build(self, source_entities, targets):

        if self.number:
            global _sync_value

            with _sync_lock:
                _sync_value = _sync_value + self.number

                if (_sync_value % self.number) != 0:
                    name = self.get_trace(source_entities)
                    raise Exception("_sync_value: %s, number: %s, node: %s" %
                                    (_sync_value, self.number, name))

        time.sleep(self.sleep_interval)

        if self.number:
            with _sync_lock:
                if (_sync_value % self.number) != 0:
                    name = self.get_trace(source_entities)
                    raise Exception("_sync_value: %s, number: %s, node: %s" %
                                    (_sync_value, self.number, name))

                _sync_value = _sync_value - self.number

        target = [src.get() for src in source_entities]
        target = self.make_simple_entity(target)

        targets.add_targets(target)


# ==============================================================================
class CopyValueBuilder (Builder):

    def __init__(self, options):
        self.signature = b''

    def build(self, source_entities, targets):
        target_entities = []

        for source_value in source_entities:
            copy_value = SimpleEntity(
                source_value.get(), name=source_value.name + '_copy')
            target_entities.append(copy_value)

        targets.add_targets(target_entities)

    def get_trace_targets(self, target_entities, brief):
        return tuple(value.name for value in target_entities)

    def get_trace_sources(self, source_entities, brief):
        return tuple(value.name for value in source_entities)


# ==============================================================================
class ChecksumBuilder (FileBuilder):

    NAME_ATTRS = ('replace_ext',)
    SIGNATURE_ATTRS = ('offset', 'length')

    def __init__(self, options, offset, length, replace_ext=False):

        self.offset = offset
        self.length = length
        self.replace_ext = replace_ext

    # -----------------------------------------------------------

    def _build_src(self, src, alg):
        chcksum = file_checksum(src, self.offset, self.length, alg)

        if self.replace_ext:
            chcksum_filename = os.path.splitext(src)[0]
        else:
            chcksum_filename = src

        chcksum_filename += '.%s.chksum' % alg

        chcksum_filename = self.get_source_target_path(chcksum_filename)

        with open(chcksum_filename, 'wb') as f:
            f.write(chcksum.digest())

        return self.make_file_entity(chcksum_filename, tags=alg)

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        target_entities = []

        for src in source_entities:
            src = src.get()
            target_entities.append(self._build_src(src, 'md5'))
            target_entities.append(self._build_src(src, 'sha512'))

        targets.add_targets(target_entities)

    # -----------------------------------------------------------

    def build_batch(self, source_entities, targets):
        print("build_batch: %s" % (source_entities,))
        for src_value in source_entities:
            target_files = [self._build_src(src_value.get(), 'md5'),
                            self._build_src(src_value.get(), 'sha512')]

            targets[src_value].add_targets(target_files)


# ==============================================================================
class ChecksumSingleBuilder (ChecksumBuilder):

    split = ChecksumBuilder.split_single


# ==============================================================================
class ChecksumBadBuilder (ChecksumBuilder):

    def get_target_entities(self, source_entities):
        return self.get_source_target_path('bad_target')


# ==============================================================================
def _add_nodes_to_bm(builder, src_files):
    bm = BuildManager()
    try:
        checksums_node = Node(builder, src_files)
        checksums_node2 = Node(builder, checksums_node)

        bm.add([checksums_node])
        bm.self_test()
        bm.add([checksums_node2])
        bm.self_test()
    except Exception:
        bm.close()
        raise

    return bm


# ==============================================================================
def _build(bm, jobs=1, keep_going=False, explain=False):
    try:
        bm.self_test()
        success = bm.build(jobs=jobs, keep_going=keep_going, explain=explain)
        bm.self_test()
        if not success:
            bm.print_fails()
            raise Exception("Nodes failed")

    finally:
        bm.close()
        bm.self_test()

# ==============================================================================


def _build_checksums(builder, src_files, jobs=1):

    bm = _add_nodes_to_bm(builder, src_files)
    _build(bm, jobs=jobs)

# ==============================================================================


class TestBuildManager(AqlTestCase):

    def event_node_building(self, settings, node):
        self.building_nodes += 1

    # -----------------------------------------------------------

    def event_node_removed(self, settings, node, progress):
        self.removed_nodes += 1

    # -----------------------------------------------------------

    def setUp(self):    # noqa
        super(TestBuildManager, self).setUp()

        self.building_nodes = 0
        add_user_handler(self.event_node_building)

    # -----------------------------------------------------------

    def tearDown(self):     # noqa
        remove_user_handler([self.event_node_building])

        super(TestBuildManager, self).tearDown()

    # -----------------------------------------------------------

    def test_bm_deps(self):

        bm = BuildManager()

        value1 = SimpleEntity("http://aql.org/download1", name="target_url1")
        value2 = SimpleEntity("http://aql.org/download2", name="target_url2")
        value3 = SimpleEntity("http://aql.org/download3", name="target_url3")

        options = builtin_options()

        builder = CopyValueBuilder(options)

        node0 = Node(builder, value1)
        node1 = Node(builder, node0)
        node2 = Node(builder, node1)
        node3 = Node(builder, value2)
        node4 = Node(builder, value3)
        node5 = Node(builder, node4)

        node6 = Node(builder, node5)
        node6.depends([node0, node1])

        bm.add([node0])
        bm.self_test()
        self.assertEqual(len(bm), 1)
        bm.add([node1])
        bm.self_test()
        self.assertEqual(len(bm), 2)
        bm.add([node2])
        bm.self_test()
        self.assertEqual(len(bm), 3)
        bm.add([node3])
        bm.self_test()
        self.assertEqual(len(bm), 4)
        bm.add([node4])
        bm.self_test()
        self.assertEqual(len(bm), 5)
        bm.add([node5])
        bm.self_test()
        self.assertEqual(len(bm), 6)
        bm.add([node6])
        bm.self_test()
        self.assertEqual(len(bm), 7)

        node0.depends(node3)
        bm.depends(node0, [node3])
        bm.self_test()
        node1.depends(node3)
        bm.depends(node1, [node3])
        bm.self_test()
        node2.depends(node3)
        bm.depends(node2, [node3])
        bm.self_test()
        node3.depends(node4)
        bm.depends(node3, [node4])
        bm.self_test()
        node0.depends(node5)
        bm.depends(node0, [node5])
        bm.self_test()
        node5.depends(node3)
        bm.depends(node5, [node3])
        bm.self_test()

        def _cyclic_deps(src_node, dep_node):
            src_node.depends(dep_node)
            bm.depends(src_node, [dep_node])

        self.assertRaises(ErrorNodeDependencyCyclic,
                          _cyclic_deps, node4, node3)

    # -----------------------------------------------------------

    def test_bm_build(self):

        with Tempdir() as tmp_dir:

            options = builtin_options()
            options.build_dir = tmp_dir

            src_files = self.generate_source_files(tmp_dir, 5, 201)

            builder = ChecksumBuilder(options, 0, 256)

            self.building_nodes = self.built_nodes = 0
            _build_checksums(builder, src_files)
            self.assertEqual(self.building_nodes, 2)
            self.assertEqual(self.building_nodes, self.built_nodes)

            # -----------------------------------------------------------

            self.building_nodes = self.built_nodes = 0
            _build_checksums(builder, src_files)
            self.assertEqual(self.building_nodes, 0)
            self.assertEqual(self.building_nodes, self.built_nodes)

            # -----------------------------------------------------------

            builder = ChecksumBuilder(options, 32, 1024)

            self.building_nodes = self.built_nodes = 0
            _build_checksums(builder, src_files)
            self.assertEqual(self.building_nodes, 2)
            self.assertEqual(self.building_nodes, self.built_nodes)

            # -----------------------------------------------------------

            self.building_nodes = self.built_nodes = 0
            _build_checksums(builder, src_files)
            self.assertEqual(self.building_nodes, 0)
            self.assertEqual(self.building_nodes, self.building_nodes)

    # -----------------------------------------------------------

    def test_bm_nodes(self):

        def _make_nodes(builder):
            node1 = Node(builder, value1)
            copy_node1 = Node(builder, node1)
            copy2_node1 = Node(builder, copy_node1)
            node2 = Node(builder, value2)
            node3 = Node(builder, value3)
            copy_node3 = Node(builder, node3)

            copy2_node3 = Node(builder, copy_node3)
            copy2_node3.depends([node1, copy_node1])

            return node1, node2, node3, copy_node1,\
                copy_node3, copy2_node1, copy2_node3

        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir

            bm = BuildManager()

            value1 = SimpleEntity(
                "http://aql.org/download1", name="target_url1")
            value2 = SimpleEntity(
                "http://aql.org/download2", name="target_url2")
            value3 = SimpleEntity(
                "http://aql.org/download3", name="target_url3")

            builder = CopyValueBuilder(options)

            bm.add(_make_nodes(builder))

            self.built_nodes = 0
            bm.build(jobs=1, keep_going=False)
            bm.close()
            self.assertEqual(self.built_nodes, 7)

            # ----------------------------------------------------------

            bm.add(_make_nodes(builder))

            self.built_nodes = 0
            bm.build(jobs=1, keep_going=False)
            bm.close()
            self.assertEqual(self.built_nodes, 0)

            # ----------------------------------------------------------

            bm.add(_make_nodes(builder))

            self.removed_nodes = 0
            bm.clear()
            bm.close()
            self.assertEqual(self.removed_nodes, 7)

            # ----------------------------------------------------------

            nodes = _make_nodes(builder)
            copy_node3 = nodes[4]
            bm.add(nodes)

            self.built_nodes = 0
            bm.build(jobs=1, keep_going=False, nodes=[copy_node3])
            bm.close()
            self.assertEqual(self.built_nodes, 2)

            # ----------------------------------------------------------

            nodes = _make_nodes(builder)
            node2 = nodes[1]
            copy_node3 = nodes[4]
            bm.add(nodes)

            self.built_nodes = 0
            bm.build(jobs=1, keep_going=False, nodes=[node2, copy_node3])
            bm.close()
            self.assertEqual(self.built_nodes, 1)

    # ==========================================================

    def test_bm_check(self):

        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir

            src_files = self.generate_source_files(tmp_dir, 3, 201)

            builder = ChecksumBuilder(options, 0, 256, replace_ext=True)

            self.building_nodes = self.built_nodes = 0
            _build_checksums(builder, src_files)
            self.assertEqual(self.building_nodes, 2)
            self.assertEqual(self.building_nodes, self.built_nodes)

            self.built_nodes = 0
            _build_checksums(builder, src_files)
            self.assertEqual(self.built_nodes, 0)

            bm = _add_nodes_to_bm(builder, src_files)
            try:
                bm.clear()
                bm.self_test()
            finally:
                bm.close()

    # -----------------------------------------------------------

    def test_bm_batch(self):

        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir
            options.batch_build = True

            src_files = self.generate_source_files(tmp_dir, 3, 201)

            builder = ChecksumBuilder(options, 0, 256, replace_ext=True)

            self.building_nodes = self.built_nodes = 0
            _build_checksums(builder, src_files)
            self.assertEqual(self.building_nodes, 2)
            self.assertEqual(self.building_nodes, self.built_nodes)

            self.built_nodes = 0
            _build_checksums(builder, src_files)
            self.assertEqual(self.built_nodes, 0)

            bm = _add_nodes_to_bm(builder, src_files)
            try:
                bm.clear()
                bm.self_test()
            finally:
                bm.close()

    # -----------------------------------------------------------

    def test_bm_dup_names(self):

        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir
            options.batch_build = True
            # options.batch_groups = 4
            options.batch_size = 3

            src_files = self.generate_source_files(tmp_dir, 10, 201)

            builder = ChecksumBadBuilder(options, 0, 256, replace_ext=True)

            self.building_nodes = self.built_nodes = 0

            with self.assertRaises(ErrorNodeDuplicateNames):
                _build_checksums(builder, src_files, jobs=4)

    # -----------------------------------------------------------

    def test_bm_rebuild(self):

        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir

            num_src_files = 10
            src_files = self.generate_source_files(tmp_dir, num_src_files, 201)

            def _build_nodes(num_dups, uptodate):
                bm = BuildManager()

                self.building_nodes = self.built_nodes = 0

                builder = ChecksumSingleBuilder(options, 0, 256)

                src_entities = tuple(map(FileChecksumEntity, src_files))

                num_built_nodes = 0

                for i in range(num_dups):
                    num_built_nodes = 1
                    node = Node(builder, src_entities)

                    node = Node(builder, node)
                    num_built_nodes += 2

                    node = Node(builder, node)
                    num_built_nodes += 2 ** 2

                    node = Node(builder, node)
                    num_built_nodes += 2 ** 3

                    bm.add([node])

                _build(bm, jobs=10, explain=False)

                if uptodate:
                    num_built_nodes = 0
                else:
                    num_built_nodes *= num_src_files

                self.assertEqual(self.building_nodes, num_built_nodes)

            _build_nodes(3, False)
            _build_nodes(3, True)

    # -----------------------------------------------------------

    def test_bm_tags(self):

        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir

            num_src_files = 3
            src_files = self.generate_source_files(tmp_dir, num_src_files, 201)

            builder = ChecksumSingleBuilder(options, 0, 256)

            bm = BuildManager()

            self.built_nodes = 0

            node = Node(builder, src_files)

            node_md5 = Node(builder, node.at('md5'))

            bm.add([node_md5])

            _build(bm)

            self.assertEqual(self.built_nodes, num_src_files * 2)

            # -----------------------------------------------------------

            self.regenerate_file(src_files[0], )

            bm = BuildManager()

            self.built_nodes = 0

            node = Node(builder, src_files)

            node_md5 = Node(builder, node.at('md5'))

            bm.add([node_md5])

            _build(bm)

            self.assertEqual(self.built_nodes, 2)

    # -----------------------------------------------------------

    def test_bm_tags_batch(self):

        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir
            options.batch_build = True

            num_src_files = 3
            src_files = self.generate_source_files(tmp_dir, num_src_files, 201)

            builder = ChecksumBuilder(options, 0, 256)

            options.batch_build = False
            single_builder = ChecksumSingleBuilder(options, 0, 256)
            bm = BuildManager()

            self.built_nodes = 0

            node = Node(builder, src_files)

            node_md5 = Node(single_builder, node.at('md5'))

            bm.add([node_md5])

            _build(bm)

            self.assertEqual(self.built_nodes, num_src_files + 1)

            # -----------------------------------------------------------

            self.regenerate_file(src_files[0], 201)

            bm = BuildManager()

            self.built_nodes = 0

            node = Node(builder, src_files)

            node_md5 = Node(single_builder, node.at('md5'))

            bm.add([node_md5])

            _build(bm)

            self.assertEqual(self.built_nodes, 2)

    # -----------------------------------------------------------

    def test_bm_conflicts(self):

        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir

            num_src_files = 3
            src_files = self.generate_source_files(tmp_dir, num_src_files, 201)

            bm = BuildManager()

            self.built_nodes = 0

            builder1 = ChecksumSingleBuilder(options, 0, 256)
            builder2 = ChecksumSingleBuilder(options, 0, 1024)

            node1 = Node(builder1, src_files)
            node2 = Node(builder2, src_files)
            # node1 = Node( builder1, node1 )
            # node2 = Node( builder2, node2 )

            bm.add([node1, node2])
            self.assertRaises(ErrorNodeSignatureDifferent, _build, bm)

    # -----------------------------------------------------------

    def test_bm_no_conflicts(self):

        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir

            num_src_files = 3
            src_files = self.generate_source_files(tmp_dir, num_src_files, 201)

            bm = BuildManager()

            self.built_nodes = 0

            builder1 = ChecksumSingleBuilder(options, 0, 256)
            builder2 = ChecksumSingleBuilder(options, 0, 256)

            node1 = Node(builder1, src_files)
            node2 = Node(builder2, src_files)
            node1 = Node(builder1, node1)
            node2 = Node(builder2, node2)

            bm.add([node1, node2])
            _build(bm)

            self.assertEqual(
                self.built_nodes, num_src_files + num_src_files * 2)

    # -----------------------------------------------------------

    def test_bm_node_index(self):

        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir

            num_src_files = 2
            src_files = self.generate_source_files(tmp_dir, num_src_files, 201)

            bm = BuildManager()

            self.built_nodes = 0

            builder = ChecksumSingleBuilder(options, 0, 256)

            node = Node(builder, src_files)
            nodes = [Node(builder, node[i * 2])
                     for i in range(num_src_files + 1)]
            node2 = Node(builder, node[1:2][:])
            #
            bm.add([node2])
            bm.add(nodes)
            _build(bm)

            self.assertEqual(
                self.built_nodes, num_src_files + num_src_files + 1 + 1)

    # -----------------------------------------------------------

    def test_bm_node_build_fail(self):

        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir

            bm = BuildManager()

            self.built_nodes = 0

            builder = FailedBuilder(options)

            nodes = [Node(builder, SimpleEntity("123-%s" % (i,)))
                     for i in range(4)]
            bm.add(nodes)

            self.assertRaises(Exception, _build, bm)
            self.assertEqual(self.built_nodes, 0)

    # -----------------------------------------------------------

    def test_bm_sync_nodes(self):

        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir

            bm = BuildManager()

            self.built_nodes = 0

            nodes = [Node(SyncValueBuilder(options, name="%s" % i, number=n),
                          SimpleEntity("123-%s" % i))
                     for i, n in zip(range(4), [3, 5, 7, 11])]

            bm.add(nodes)
            bm.sync(nodes)

            _build(bm, jobs=4)

    # -----------------------------------------------------------

    @skip
    def test_bm_sync_modules(self):

        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir

            bm = BuildManager()

            self.built_nodes = 0

            """
             10    11__
            / | \ / \  \
          20 21  22  23 24
         /  \ | / \   \ |
        30    31   32  33
      """

            node30 = Node(SyncValueBuilder(options, name="30", number=7),
                          SimpleEntity("30"))

            node31 = Node(SyncValueBuilder(options, name="31", number=0,
                                           sleep_interval=0),
                          SimpleEntity("31"))

            node32 = Node(SyncValueBuilder(options, name="32", number=0,
                                           sleep_interval=0),
                          SimpleEntity("32"))

            node33 = Node(SyncValueBuilder(options, name="33", number=17),
                          SimpleEntity("33"))

            node20 = Node(SyncValueBuilder(options, name="20", number=7),
                          (node30, node31))

            node21 = Node(SyncValueBuilder(options, name="21", number=7),
                          (node31,))

            node22 = Node(SyncValueBuilder(options, name="22", number=0,
                                           sleep_interval=5),
                          (node31, node32))

            node23 = Node(SyncValueBuilder(options, name="23", number=17),
                          (node33,))

            node24 = Node(SyncValueBuilder(options, name="24", number=17),
                          (node33,))

            node10 = Node(SyncValueBuilder(options, name="10", number=7),
                          (node20, node21, node22))

            node11 = Node(SyncValueBuilder(options, name="11", number=17),
                          (node22, node23, node24))

            bm.add((node10, node11))
            bm.sync((node10, node11), deep=True)

            _build(bm, jobs=4)

    # -----------------------------------------------------------

    def test_bm_require_modules(self):

        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir

            bm = BuildManager()

            self.built_nodes = 0

            """
                 10    11__
                / | \ / \  \
              20 21  22  23 24
             /  \ | / \   \ |
            30    31   32  33
            """

            node30 = Node(SyncValueBuilder(options, name="30", number=7),
                          SimpleEntity("30"))

            node31 = Node(SyncValueBuilder(options, name="31", number=0,
                                           sleep_interval=0),
                          SimpleEntity("31"))

            node32 = Node(SyncValueBuilder(options, name="32", number=0,
                                           sleep_interval=0),
                          SimpleEntity("32"))

            node33 = Node(SyncValueBuilder(options, name="33", number=17),
                          SimpleEntity("33"))

            node20 = Node(SyncValueBuilder(options, name="20", number=7),
                          (node30, node31))

            node21 = Node(SyncValueBuilder(options, name="21", number=7),
                          (node31,))

            node22 = Node(SyncValueBuilder(options, name="22", number=0,
                                           sleep_interval=5),
                          (node31, node32))

            node23 = Node(SyncValueBuilder(options, name="23", number=17),
                          (node33,))

            node24 = Node(SyncValueBuilder(options, name="24", number=17),
                          (node33,))

            node10 = Node(SyncValueBuilder(options, name="10", number=7),
                          (node20, node21, node22))

            node11 = Node(SyncValueBuilder(options, name="11", number=17),
                          (node22, node23, node24))

            # print( "node30: %s" % node30 )
            # print( "node31: %s" % node31 )
            # print( "node32: %s" % node32 )
            # print( "node33: %s" % node33 )
            #
            # print( "node20: %s" % node20 )
            # print( "node21: %s" % node21 )
            # print( "node22: %s" % node22 )
            # print( "node23: %s" % node23 )
            # print( "node24: %s" % node24 )
            #
            # print( "node10: %s" % node10 )
            # print( "node11: %s" % node11 )

            bm.add((node10, node11))
            bm.module_depends(node10, [node11])

            _build(bm, jobs=4)

    # -----------------------------------------------------------

    def test_bm_skip_nodes_by_value(self):
        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir

            bm = BuildManager()

            self.built_nodes = 0

            node = Node(ValueBuilder(options), [1, 2, 3, 4])
            bm.add([node])

            bm.build_if(False, node)

            _build(bm, jobs=4)
            self.assertEqual(self.built_nodes, 0)

    # ----------------------------------------------------------

    def test_bm_skip_nodes_by_node(self):
        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir

            bm = BuildManager()

            self.built_nodes = 0

            cond_node1 = Node(CondBuilder(options), False)
            node1 = Node(ValueBuilder(options), [1, 2])
            cond_node2 = Node(CondBuilder(options), True)
            node2 = Node(ValueBuilder(options), [3, 4])
            main = Node(ValueBuilder(options), [7, 8, node1, node2])

            bm.add([main])

            bm.build_if(cond_node1, node1)
            bm.build_if(cond_node2, node2)

            _build(bm, jobs=4)
            self.assertEqual(main.get(), "7-8-3-4")
            self.assertEqual(self.built_nodes, 4)

    # ----------------------------------------------------------

    def test_bm_skip_nodes_by_option(self):
        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir

            bm = BuildManager()
            self.built_nodes = 0

            cond_node = Node(CondBuilder(options), False)

            options.has_openmp = BoolOptionType(default=True)
            options.has_openmp = cond_node

            node = Node(ValueBuilder(options), None)
            bm.add([node])

            bm.build_if(options.has_openmp, node)
            bm.depends(node, [cond_node])

            _build(bm, jobs=4)
            self.assertEqual(self.built_nodes, 1)

    # ----------------------------------------------------------

    def test_bm_expensive(self):
        with Tempdir() as tmp_dir:
            options = builtin_options()
            options.build_dir = tmp_dir

            bm = BuildManager()
            self.built_nodes = 0

            event = threading.Event()

            heavy = ExpensiveValueBuilder(options, event, do_expensive=True)
            light = ExpensiveValueBuilder(options, event, do_expensive=False)

            node1 = Node(heavy, [1, 2, 3, 4, 5, 7])
            node2 = Node(light, list(range(10, 100, 10)))
            bm.add([node2, node1])
            bm.expensive(node1)

            _build(bm, jobs=16)


# ==============================================================================
def _generate_node_tree(bm, builder, node, depth):
    while depth:
        node = Node(builder, node)
        bm.add([node])
        depth -= 1


# ==============================================================================
@skip
class TestBuildManagerSpeed(AqlTestCase):

    def test_bm_deps_speed(self):

        bm = BuildManager()

        value = SimpleEntity("http://aql.org/download", name="target_url1")
        builder = CopyValueBuilder()

        node = Node(builder, value)
        bm.add([node])

        _generate_node_tree(bm, builder, node, 5000)
