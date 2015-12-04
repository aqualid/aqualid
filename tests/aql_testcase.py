import os.path
import pickle
import shutil
import random
import unittest

import pytest

from aql.utils import Tempfile, add_user_handler, remove_user_handler, \
    enable_default_handlers

# ==============================================================================

skip = pytest.mark.skipif("True")
skipped = pytest.skip

# ==============================================================================


class AqlTestCase(unittest.TestCase):

    def event_node_building_finished(self, settings, node,
                                     builder_output, progress):
        self.built_nodes += 1

    def event_node_removed(self, settings, node, progress):
        self.removed_nodes += 1

    # ==============================================================================

    def setUp(self):    # noqa
        super(AqlTestCase, self).setUp()

        self.built_nodes = 0
        self.removed_nodes = 0
        add_user_handler(self.event_node_building_finished)
        add_user_handler(self.event_node_removed)

    # ----------------------------------------------------------

    def tearDown(self):     # noqa
        remove_user_handler(self.event_node_building_finished)
        remove_user_handler(self.event_node_removed)

        enable_default_handlers()

        super(AqlTestCase, self).tearDown()

    # ----------------------------------------------------------

    if not hasattr(unittest.TestCase, 'assertItemsEqual'):
        def assertItemsEqual(self, actual, expected, msg=None):  # noqa
            def _value_counts(seq):
                counts = dict()
                for value in seq:
                    counts.setdefault(value, 0)
                    counts[value] += 1
                return counts

            actual_counts = _value_counts(actual)
            expected_counts = _value_counts(expected)

            if msg is None:
                msg = str(actual) + " != " + str(expected)

            self.assertTrue(actual_counts == expected_counts, msg)

    # ----------------------------------------------------------

    def build_prj(self, prj, num_built_nodes, num_failed_nodes=0, jobs=4):
        self.built_nodes = 0

        ok = prj.build(jobs=jobs)
        if not ok:
            if num_failed_nodes == 0:
                prj.build_manager.print_fails()
                assert False, "Build failed"

        self.assertEqual(prj.build_manager.fails_count(), num_failed_nodes)
        self.assertEqual(self.built_nodes,               num_built_nodes)

    # ==============================================================================

    def clear_prj(self, prj):
        self.removed_nodes = 0

        prj.clear()

        self.assertGreater(self.removed_nodes, 0)

    # ==============================================================================

    def _test_save_load(self, value):
        data = pickle.dumps((value, ), protocol=pickle.HIGHEST_PROTOCOL)

        loaded_values = pickle.loads(data)
        loaded_value = loaded_values[0]

        self.assertEqual(value, loaded_value)

    # ==============================================================================

    @staticmethod
    def regenerate_file(filepath, size=200):
        with open(filepath, 'wb') as f:
            f.write(bytearray(random.randint(0, 255) for i in range(size)))

    # ==============================================================================

    @staticmethod
    def generate_file(tmp_dir, size, suffix='.tmp'):
        tmp = Tempfile(root_dir=tmp_dir, suffix=suffix)
        tmp.write(bytearray(random.randint(0, 255) for i in range(size)))

        tmp.close()

        return tmp

    # ==============================================================================

    @staticmethod
    def remove_files(files):
        for f in files:
            try:
                os.remove(f)
            except (OSError, IOError):
                pass

    # ==============================================================================

    @staticmethod
    def copy_file(src_file, dst_file):
        shutil.copy(src_file, dst_file)

    # ==============================================================================

    @staticmethod
    def generate_source_files(tmp_dir, num, size, suffix='.tmp'):

        src_files = []

        try:
            while num > 0:
                num -= 1
                src_file = AqlTestCase.generate_file(tmp_dir, size, suffix)
                src_files.append(src_file)
        except:
            AqlTestCase.remove_files(src_files)
            raise

        return src_files

# ==============================================================================
