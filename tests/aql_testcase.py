import os.path
import pickle
import shutil
import random

from tests_utils import TestCaseBase

from aql.utils import Tempfile, add_user_handler, remove_user_handler, \
    enable_default_handlers

# ==============================================================================

class AqlTestCase(TestCaseBase):

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

    # ==============================================================================

    def tearDown(self):     # noqa
        remove_user_handler(self.event_node_building_finished)
        remove_user_handler(self.event_node_removed)

        enable_default_handlers()

        super(AqlTestCase, self).tearDown()

    # ==============================================================================

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
    def regenerate_file(filepath, size = 200):
        with open(filepath, 'wb') as f:
            f.write(bytearray(random.randint(0,255) for i in range(size)))

    # ==============================================================================

    @staticmethod
    def generate_file(tmp_dir, start, stop, suffix='.tmp'):
        tmp = Tempfile(folder=tmp_dir, suffix = suffix)
        tmp.write(bytearray(map(lambda v: v % 256, range(start, stop))))

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

        start = 0

        try:
            while num > 0:
                num -= 1
                src_files.append( AqlTestCase.generate_file(tmp_dir,
                                                            start,
                                                            start + size,
                                                            suffix))
                start += size
        except:
            AqlTestCase.remove_files(src_files)
            raise

        return src_files

# ==============================================================================
