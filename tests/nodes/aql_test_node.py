import sys
import os.path
import timeit
import shutil
import hashlib

sys.path.insert(
    0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))
from aql_tests import skip, AqlTestCase, run_local_tests

from aql.util_types import to_sequence

from aql.utils import Tempfile, Tempdir, write_bin_file, enable_default_handlers

from aql.options import builtin_options
from aql.entity import SimpleEntity, NullEntity, FileChecksumEntity, EntitiesFile
from aql.nodes import Node, Builder, FileBuilder

# ==============================================================================


def _split_nodes(items):
    nodes = []
    values = []
    for item in to_sequence(items):
        if isinstance(item, Node):
            nodes.append(item)
        else:
            values.append(item)

    return nodes, values

# ==============================================================================


class ChecksumBuilder (Builder):

    # -----------------------------------------------------------

    def __init__(self, options):
        self.signature = b''

    def build(self, source_entities, targets):
        for source_value in source_entities:
            content = source_value.data.encode()
            chcksum = hashlib.md5()
            chcksum.update(content)
            chcksum_sha512 = hashlib.sha512()
            chcksum_sha512.update(content)

            targets.add(chcksum.digest())
            targets.add_side_effects(chcksum_sha512.digest())

# ==============================================================================


class CopyBuilder (FileBuilder):

    SIGNATURE_ATTRS = ('ext', 'iext')

    def __init__(self, options, ext, iext):
        self.ext = ext
        self.iext = iext

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        target_values = []
        itarget_values = []

        idep = SimpleEntity(b'1234')

        for src in source_entities:
            src = src.get()
            new_name = src + '.' + self.ext
            new_iname = src + '.' + self.iext

            shutil.copy(src, new_name)
            shutil.copy(src, new_iname)

            target_values.append(new_name)
            itarget_values.append(new_iname)

        targets.add(target_values)
        targets.add_side_effects(itarget_values)
        targets.add_implicit_deps(idep)

    # -----------------------------------------------------------

    def build_batch(self, source_entities, targets):

        idep = SimpleEntity(b'1234')

        for src_value in source_entities:
            src = src_value.get()

            new_name = src + '.' + self.ext
            new_iname = src + '.' + self.iext

            shutil.copy(src, new_name)
            shutil.copy(src, new_iname)

            src_targets = targets[src_value]
            src_targets.add(new_name)
            src_targets.add_side_effects(new_iname)
            src_targets.add_implicit_deps(idep)

# ==============================================================================


class TestNodes(AqlTestCase):

    def tearDown(self):
        enable_default_handlers()
        super(TestNodes, self).tearDown()

    def test_node_value(self):

        with Tempfile() as tmp:

            vfile = EntitiesFile(tmp)
            try:
                value1 = SimpleEntity(
                    "http://aql.org/download1", name="target_url1")
                value2 = SimpleEntity(
                    "http://aql.org/download2", name="target_url2")
                value3 = SimpleEntity(
                    "http://aql.org/download3", name="target_url3")
                dep_value1 = SimpleEntity("SOME_VALUE1", name="dep_value")
                dep_value2 = SimpleEntity("SOME_VALUE2", name="dep_value")

                options = builtin_options()
                builder = ChecksumBuilder(options)

                # -----------------------------------------------------------

                node = Node(builder, [value1, value2, value3])
                node.depends(dep_value1)
                node.initiate()
                node.build_split(vfile, False)

                self.assertFalse(node.check_actual(vfile, False))
                out = node.build()
                node.save(vfile)

                # -----------------------------------------------------------

                node = Node(builder, [value1, value2, value3])
                node.depends(dep_value1)
                node.initiate()
                node.build_split(vfile, False)
                self.assertTrue(node.check_actual(vfile, False))

                # -----------------------------------------------------------

                node = Node(builder, [value1, value2, value3])
                node.depends(dep_value2)
                node.initiate()
                node.build_split(vfile, False)

                self.assertFalse(node.check_actual(vfile, False))
                out = node.build()
                node.save(vfile)

                # -----------------------------------------------------------

                node = Node(builder, [value1, value2, value3])
                node.depends(dep_value2)
                node.initiate()
                node.build_split(vfile, False)
                self.assertTrue(node.check_actual(vfile, False))

                # -----------------------------------------------------------

                node = Node(builder, [value1, value2, value3])
                node.depends(dep_value2)
                node.depends(NullEntity())
                node.initiate()
                node.build_split(vfile, False)

                self.assertFalse(node.check_actual(vfile, False))
                node.build()
                node.save(vfile)

                node = Node(builder, [value1, value2, value3])
                node.depends(dep_value2)
                node.depends(NullEntity())
                node.initiate()
                node.build_split(vfile, False)

                self.assertFalse(node.check_actual(vfile, False))

            finally:
                vfile.close()

    # ==============================================================================

    def _rebuild_node(self, vfile, builder, values, deps, tmp_files):
        node = Node(builder, values)
        node.depends(deps)

        node.initiate()
        node.build_split(vfile, False)

        self.assertFalse(node.check_actual(vfile, False))
        node.build()
        node.save(vfile)

        # -----------------------------------------------------------

        node = Node(builder, values)
        node.depends(deps)

        node.initiate()
        node.build_split(vfile, explain=True)

        self.assertTrue(node.check_actual(vfile, explain=True))

        tmp_files.extend(target.get() for target in node.get_target_entities())
        tmp_files.extend(target.get()
                         for target in node.get_side_effect_entities())

        return node

    # ==========================================================

    def test_node_file(self):

        try:
            tmp_files = []

            with Tempfile() as tmp:

                vfile = EntitiesFile(tmp)
                try:
                    with Tempfile(suffix='.1') as tmp1:
                        with Tempfile(suffix='.2') as tmp2:
                            value1 = FileChecksumEntity(tmp1)
                            value2 = FileChecksumEntity(tmp2)

                            options = builtin_options()

                            builder = CopyBuilder(options, "tmp", "i")
                            node = self._rebuild_node(
                                vfile, builder, [value1, value2], [], tmp_files)

                            builder = CopyBuilder(options, "ttt", "i")
                            node = self._rebuild_node(
                                vfile, builder, [value1, value2], [], tmp_files)

                            builder = CopyBuilder(options, "ttt", "d")
                            node = self._rebuild_node(
                                vfile, builder, [value1, value2], [], tmp_files)

                            tmp1.write(b'123')
                            tmp1.flush()
                            value1 = FileChecksumEntity(tmp1)
                            node = self._rebuild_node(
                                vfile, builder, [value1, value2], [], tmp_files)

                            with Tempfile(suffix='.3') as tmp3:
                                value3 = FileChecksumEntity(tmp3)

                                node3 = self._rebuild_node(
                                    vfile, builder, [value3], [], tmp_files)

                                node = self._rebuild_node(
                                    vfile, builder, [value1, node3], [], tmp_files)

                                # node3: CopyBuilder, tmp, i, tmp3 -> tmp3.tmp, ,tmp3.i
                                # node: CopyBuilder, tmp, i, tmp1, tmp3.tmp ->
                                # tmp1.tmp, tmp3.tmp.tmp, , tmp1.i, tmp3.tmp.i

                                builder3 = CopyBuilder(options, "xxx", "3")
                                node3 = self._rebuild_node(
                                    vfile, builder3, [value3], [], tmp_files)

                                # node3: CopyBuilder, xxx, 3, tmp3 -> tmp3.xxx,
                                # ,tmp3.3

                                node = self._rebuild_node(
                                    vfile, builder, [value1, node3], [], tmp_files)

                                # node: CopyBuilder, tmp, i, tmp1, tmp3.xxx ->
                                # tmp1.tmp, tmp3.xxx.tmp, , tmp1.i, tmp3.xxx.i

                                node = self._rebuild_node(
                                    vfile, builder, [value1], [node3], tmp_files)

                                dep = SimpleEntity("1", name="dep1")
                                node = self._rebuild_node(
                                    vfile, builder, [value1, node3], [dep], tmp_files)

                                dep = SimpleEntity("11", name="dep1")
                                node = self._rebuild_node(
                                    vfile, builder, [value1, node3], [dep], tmp_files)
                                node3 = self._rebuild_node(
                                    vfile, builder3, [value1], [], tmp_files)
                                node = self._rebuild_node(
                                    vfile, builder, [value1], [node3], tmp_files)
                                node3 = self._rebuild_node(
                                    vfile, builder3, [value2], [], tmp_files)
                                node = self._rebuild_node(
                                    vfile, builder, [value1], [node3], tmp_files)

                                node_tname = node.get_target_entities()[0].name

                                with open(node_tname, 'wb') as f:
                                    f.write(b'333')
                                    f.flush()

                                node = self._rebuild_node(
                                    vfile, builder, [value1], [node3], tmp_files)

                                with open(node.get_side_effect_entities()[0].name, 'wb') as f:
                                    f.write(b'abc')
                                    f.flush()

                                node = Node(builder, [value1])
                                node.depends([node3])
                                node.initiate()
                                node.build_split(vfile, False)

                                self.assertTrue(node.check_actual(vfile, False))
                                # node = self._rebuild_node( vfile, builder, [value1], [node3], tmp_files )
                finally:
                    vfile.close()
        finally:
            for tmp_file in tmp_files:
                try:
                    os.remove(tmp_file)
                except OSError:
                    pass

    # ==========================================================

    def _rebuild_batch_node(self, vfile, src_files, built_count):
        options = builtin_options()
        options.batch_build = True
        options.batch_groups = 2

        builder = CopyBuilder(options, "tmp", "i")

        node = Node(builder, src_files)
        dep = SimpleEntity("11", name="dep1")
        node.depends(dep)

        node.initiate()
        split_nodes = node.build_split(vfile, False)

        if built_count == 0:
            self.assertFalse(split_nodes)
            self.assertTrue(node.check_actual(vfile, False))
        else:
            for split_node in split_nodes:
                self.assertFalse(split_node.check_actual(vfile, False))
                split_node.build()
                split_node.save(vfile)

            self.assertEqual(len(split_nodes), 2)
            self.assertTrue(node.check_actual(vfile, False))

    # ==========================================================

    def test_node_batch(self):

        with Tempdir() as tmp_dir:
            vfile_name = Tempfile(folder=tmp_dir)
            vfile_name.close()
            with EntitiesFile(vfile_name) as vfile:
                src_files = self.generate_source_files(tmp_dir, 5, 100)

                self._rebuild_batch_node(vfile, src_files, len(src_files))
                self._rebuild_batch_node(vfile, src_files, 0)
                self._rebuild_batch_node(vfile, src_files[:-2], 0)
                self._rebuild_batch_node(vfile, src_files[0:1], 0)

                # -----------------------------------------------------------

                write_bin_file(src_files[1], b"src_file1")
                write_bin_file(src_files[2], b"src_file1")

                self._rebuild_batch_node(vfile, src_files, 2)

# ==============================================================================

_FileValueType = FileChecksumEntity


class TestSpeedBuilder (Builder):

    __slots__ = ('ext', 'idep')

    def __init__(self, options, name, ext, idep):
        self.name = name
        self.ext = ext
        self.idep = idep
        self.signature = str(ext + '|' + idep).encode('utf-8')

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        for source_value in source_entities:
            new_name = source_value.name + '.' + self.ext
            idep_name = source_value.name + '.' + self.idep

            shutil.copy(source_value.name, new_name)

            targets.add_files(new_name)
            targets.add_implicit_dep_files(idep_name)

    # -----------------------------------------------------------

    def __str__(self):
        return ' '.join(self.name)

# ==============================================================================


def _test_no_build_speed(vfile, builder, source_values):
    for source in source_values:
        node = Node(builder, _FileValueType(source))
        node.initiate()
        node.build_split(vfile, False)
        if not node.check_actual(vfile, False):
            raise AssertionError("node is not actual")


def _generate_files(tmp_files, number, size):
    content = b'1' * size
    files = []
    for i in range(0, number):
        t = Tempfile()
        tmp_files.append(t)
        t.write(content)
        files.append(t)

    return files


def _copy_files(tmp_files, files, ext):
    copied_files = []

    for f in files:
        name = f + '.' + ext
        shutil.copy(f, f + '.' + ext)
        tmp_files.append(name)
        copied_files.append(name)

    return copied_files


@skip
class TestNodesSpeed (AqlTestCase):

    def test_node_speed(self):

        try:
            tmp_files = []

            source_files = _generate_files(tmp_files, 4000, 50 * 1024)
            idep_files = _copy_files(tmp_files, source_files, 'h')

            with Tempfile() as tmp:

                vfile = EntitiesFile(tmp)
                try:
                    builder = TestSpeedBuilder("TestSpeedBuilder", "tmp", "h")

                    for source in source_files:
                        node = Node(builder, _FileValueType(source))
                        node.initiate()
                        node.build_split(vfile, False)
                        self.assertFalse(node.check_actual(vfile, False))
                        node.build()
                        node.save(vfile)
                        for tmp_file in node.get_targets():
                            tmp_files.append(tmp_file)

                    t = lambda vfile = vfile, builder = builder, source_files = source_files, test_no_build_speed = _test_no_build_speed: test_no_build_speed(
                        vfile, builder, source_files)
                    t = timeit.timeit(t, number=1)
                finally:
                    vfile.close()

        finally:
            for tmp_file in tmp_files:
                try:
                    os.remove(tmp_file)
                except OSError:
                    pass

# ==============================================================================

if __name__ == "__main__":
    run_local_tests()
