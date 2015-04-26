import sys
import os.path
import pickle
import shutil

_search_paths = ['.', 'tests_utils', 'tools']
sys.path[:0] = map(lambda p: os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', p)), _search_paths)

from tests_utils import TestCaseBase, run_tests, TestsOptions

from aql.utils import Tempfile, add_user_handler, remove_user_handler, \
    enable_default_handlers

from aql.util_types import FilePath
from aql.nodes.aql_node import NodeEntity

# ==============================================================================

SRC_FILE_TEMPLATE = """
#include <cstdio>
#include "%s.h"

void  %s()
{}
"""

MAIN_SRC_FILE_TEMPLATE = """
#include <cstdio>

int  main()
{
  return 0;
}
"""

HDR_FILE_TEMPLATE = """
#ifndef HEADER_%s_INCLUDED
#define HEADER_%s_INCLUDED

extern void  %s();

#endif
"""

RES_FILE_TEMPLATE = """

#define VERSION_TEST "0.0.0.1"
#define VERSION_WORDS 0,0,0,1

VS_VERSION_INFO VERSIONINFO
FILEVERSION     VERSION_WORDS
PRODUCTVERSION  VERSION_WORDS
FILEFLAGSMASK   0x3fL
FILEFLAGS 0
BEGIN
  BLOCK "VarFileInfo"
  BEGIN
    VALUE "Translation",0x409,1200
  END
  BLOCK "StringFileInfo"
  BEGIN
    BLOCK "040904b0"
    BEGIN
      VALUE "CompanyName",  "Test\\0"
      VALUE "FileDescription",  "Test\\0"
      VALUE "FileVersion",  VERSION_TEST "\\0"
      VALUE "InternalName", "Test\\0"
      VALUE "LegalCopyright", "Copyright 2014 by Test\\0"
      VALUE "OriginalFilename", "Test\\0"
      VALUE "ProductName",  "Test\\0"
      VALUE "ProductVersion", VERSION_TEST "\\0"
    END
  END
END
"""

# ==============================================================================


class AqlTestCase(TestCaseBase):

    # noinspection PyUnusedLocal
    def event_node_building_finished(self, settings, node,
                                     builder_output, progress):
        self.built_nodes += 1

    # noinspection PyUnusedLocal
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

    def generate_main_cpp_file(self, dirname, name, content=None):
        if not content:
            content = MAIN_SRC_FILE_TEMPLATE

        src_file = os.path.join(dirname, name + '.cpp')

        with open(src_file, 'w') as f:
            f.write(content)

        return src_file

    # ==============================================================================

    def generate_cpp_file(self, dirname, name):
        src_content = SRC_FILE_TEMPLATE % (name, 'foo_' + name)
        hdr_content = HDR_FILE_TEMPLATE % (
            name.upper(), name.upper(), 'foo_' + name)

        src_file = os.path.join(dirname, name + '.cpp')
        hdr_file = os.path.join(dirname, name + '.h')

        with open(src_file, 'w') as f:
            f.write(src_content)

        with open(hdr_file, 'w') as f:
            f.write(hdr_content)

        return src_file, hdr_file

    # ==============================================================================

    def generate_res_file(self, dirname, name):
        src_content = RES_FILE_TEMPLATE

        src_file = os.path.join(dirname, name + '.rc')

        with open(src_file, 'w') as f:
            f.write(src_content)

        return src_file

    # ==============================================================================

    def generate_cpp_files(self, dirname, name, count):
        src_files = []
        hdr_files = []
        for i in range(count):
            src_file, hdr_file = self.generate_cpp_file(dirname, name + str(i))
            src_files.append(FilePath(src_file))
            hdr_files.append(FilePath(hdr_file))

        return src_files, hdr_files

    # ==============================================================================

    @staticmethod
    def touch_cpp_file(cpp_file):
        AqlTestCase.update_cpp_file(cpp_file, "\n// touch file\n")

    @staticmethod
    def add_error_to_cpp_file(cpp_file):
        AqlTestCase.update_cpp_file(cpp_file, "\n#error TEST ERROR\n")

    # ==============================================================================

    @staticmethod
    def update_cpp_file(cpp_file, new_line):
        with open(cpp_file, 'a') as f:
            f.write(new_line)

        NodeEntity._ACTUAL_IDEPS_CACHE.clear()    # clear nodes cache

    # ==============================================================================

    @staticmethod
    def touch_cpp_files(cpp_files):
        for cpp_file in cpp_files:
            AqlTestCase.touch_cpp_file(cpp_file)

    # ==============================================================================

    @staticmethod
    def generate_file(tmp_dir, start, stop):
        tmp = Tempfile(folder=tmp_dir)
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
    def generate_source_files(tmp_dir, num, size):

        src_files = []

        start = 0

        try:
            while num > 0:
                num -= 1
                src_files.append(
                    AqlTestCase.generate_file(tmp_dir, start, start + size))
                start += size
        except:
            AqlTestCase.remove_files(src_files)
            raise

        return src_files

# ==============================================================================

if __name__ == '__main__':

    options = TestsOptions.instance()
    options.set_default('test_modules_prefix', 'aql_test_')

    run_tests(options=options)
