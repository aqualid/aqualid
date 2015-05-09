import os
import sys
import shutil

sys.path.insert(
    0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))

from aql_tests import AqlTestCase
from tests_utils import run_local_tests

from aql.utils import Tempdir, remove_user_handler, add_user_handler
from aql.utils import EventSettings, set_event_settings
from aql.nodes import Node, BuildManager
from aql.options import builtin_options

from aql.main import Project, ProjectConfig
from aql.builtin_tools.aql_builtin_tools import ExecuteCommandBuilder

# ==============================================================================


class TestBuiltinTools(AqlTestCase):

    # -----------------------------------------------------------

    # noinspection PyUnusedLocal
    def event_node_building(self, settings, node):
        self.building_started += 1

    # -----------------------------------------------------------

    def setUp(self):    # noqa
        super(TestBuiltinTools, self).setUp()

        self.building_started = 0
        add_user_handler(self.event_node_building)

    # -----------------------------------------------------------

    def tearDown(self):     # noqa
        remove_user_handler(self.event_node_building)

        super(TestBuiltinTools, self).tearDown()

    # -----------------------------------------------------------

    def _build(self, bm, **kw):
        is_ok = bm.build(**kw)
        if not is_ok:
            bm.print_fails()

        self.assertTrue(is_ok)

    # -----------------------------------------------------------

    def test_exec(self):

        with Tempdir() as tmp_dir:

            build_dir = os.path.join(tmp_dir, 'build')

            options = builtin_options()

            cmd = [sys.executable, '-c', 'print("TEST EXEC")']

            options.build_dir = build_dir

            exec_cmd = ExecuteCommandBuilder(options)

            bm = BuildManager()
            try:

                result = Node(exec_cmd, cmd)

                bm.add([result])

                self._build(bm, jobs=1, keep_going=False)

                self.assertEqual(self.building_started, 1)
                self.assertEqual(self.building_started, self.built_nodes)

                bm.close()

                result = Node(exec_cmd, cmd)

                bm = BuildManager()
                bm.add([result])

                self.building_started = 0
                self._build(bm, jobs=1, keep_going=False)

                self.assertEqual(self.building_started, 0)

            finally:
                bm.close()

    # -----------------------------------------------------------

    def test_copy_files(self):

        with Tempdir() as tmp_install_dir:
            with Tempdir() as tmp_dir:
                # tmp_install_dir = Tempdir()
                # tmp_dir = Tempdir()

                build_dir = os.path.join(tmp_dir, 'output')

                num_sources = 3
                sources = self.generate_source_files(tmp_dir, num_sources, 200)

                cfg = ProjectConfig(args=["build_dir=%s" % build_dir])

                prj = Project(cfg)

                node = prj.tools.CopyFiles(sources, target=tmp_install_dir)

                node.options.batch_groups = 1

                self.build_prj(prj, 1)

                prj.tools.CopyFiles(sources, target=tmp_install_dir)

                self.build_prj(prj, 0)

    # -----------------------------------------------------------

    def test_exec_method(self):

        def copy_file_ext(builder, source_entities, targets, ext):
            src_file = source_entities[0].get()
            dst_file = os.path.splitext(src_file)[0] + ext
            shutil.copy(src_file, dst_file)
            targets.add(dst_file)

        with Tempdir() as tmp_dir:

            set_event_settings(
                EventSettings(brief=True, with_output=True, trace_exec=False))

            build_dir = os.path.join(tmp_dir, 'build_output')

            num_sources = 2
            sources, headers = self.generate_cpp_files(
                tmp_dir, 'test_method_', num_sources)

            cfg = ProjectConfig(args=["build_dir=%s" % build_dir])

            prj = Project(cfg)

            prj.tools.ExecuteMethod(
                sources, method=copy_file_ext, args=('.cxx',))
            prj.tools.ExecuteMethod(
                headers, method=copy_file_ext, args=('.hxx',))

            self.build_prj(prj, len(sources) + len(headers))

            prj.tools.ExecuteMethod(
                sources, method=copy_file_ext, args=('.cxx',))
            prj.tools.ExecuteMethod(
                headers, method=copy_file_ext, args=('.hxx',))

            self.build_prj(prj, 0)

            prj.tools.ExecuteMethod(sources,
                                    method=copy_file_ext,
                                    args=('.cc',))

            self.build_prj(prj, len(sources))

            prj.tools.ExecuteMethod(
                sources, method=copy_file_ext, args=('.cxx',))
            self.build_prj(prj, len(sources))

            # -----------------------------------------------------------

            for src in sources:
                self.assertTrue(
                    os.path.isfile(os.path.splitext(src)[0] + '.cxx'))

            prj.tools.ExecuteMethod(
                sources, method=copy_file_ext, args=('.cxx',))
            self.clear_prj(prj)

            for src in sources:
                self.assertFalse(
                    os.path.isfile(os.path.splitext(src)[0] + '.cxx'))

            # -----------------------------------------------------------

            prj.tools.ExecuteMethod(
                sources, method=copy_file_ext, args=('.cxx',))
            self.build_prj(prj, len(sources))

            for src in sources:
                self.assertTrue(
                    os.path.isfile(os.path.splitext(src)[0] + '.cxx'))

            prj.tools.ExecuteMethod(sources,
                                    method=copy_file_ext,
                                    args=('.cxx',),
                                    clear_targets=False)
            self.clear_prj(prj)

            for src in sources:
                self.assertTrue(
                    os.path.isfile(os.path.splitext(src)[0] + '.cxx'))

    # -----------------------------------------------------------

    def test_node_filter_dirname(self):

        with Tempdir() as tmp_install_dir:
            with Tempdir() as tmp_dir:

                build_dir = os.path.join(tmp_dir, 'output')

                num_sources = 3
                sources = self.generate_source_files(tmp_dir, num_sources, 200)

                # set_event_settings( EventSettings( brief = False,
                #                                    with_output = True ) )

                cfg = ProjectConfig(args=["build_dir=%s" % build_dir])
                cfg.debug_backtrace = True

                prj = Project(cfg)

                node = prj.tools.CopyFiles(sources[0], target=tmp_install_dir)

                prj.tools.CopyFiles(sources[1:], target=prj.node_dirname(node))

                self.build_prj(prj, 3)

                for src in sources:
                    tgt = os.path.join(tmp_install_dir, os.path.basename(src))
                    self.assertTrue(os.path.isfile(tgt))

                node = prj.tools.CopyFiles(sources[0], target=tmp_install_dir)
                prj.tools.CopyFiles(sources[1:], target=prj.node_dirname(node))

                self.build_prj(prj, 0)

    # -----------------------------------------------------------

    def test_copy_file_as(self):

        with Tempdir() as tmp_install_dir:
            with Tempdir() as tmp_dir:
                # tmp_install_dir = Tempdir()
                # tmp_dir = Tempdir()

                build_dir = os.path.join(tmp_dir, 'output')

                source = self.generate_file(tmp_dir, 0, 200)
                target = os.path.join(tmp_install_dir, 'copy_as_source.dat')

                cfg = ProjectConfig(args=["build_dir=%s" % build_dir])

                prj = Project(cfg)

                prj.tools.CopyFileAs(source, target=target)

                self.build_prj(prj, 1)

                prj.tools.CopyFileAs(source, target=target)

                self.build_prj(prj, 0)

    # -----------------------------------------------------------

    def test_write_file(self):

        with Tempdir() as tmp_install_dir:
            with Tempdir() as tmp_dir:
                # tmp_install_dir = Tempdir()
                # tmp_dir = Tempdir()

                build_dir = os.path.join(tmp_dir, 'output')

                cfg = ProjectConfig(args=["build_dir=%s" % build_dir])

                prj = Project(cfg)

                buf = "Test buffer content"

                target = os.path.join(tmp_install_dir, 'write_content.txt')
                prj.tools.WriteFile(buf, target=target)

                self.build_prj(prj, 1)

                prj.tools.WriteFile(buf, target=target)

                self.build_prj(prj, 0)

    # -----------------------------------------------------------

    def test_zip_files(self):

        with Tempdir() as tmp_install_dir:
            with Tempdir() as tmp_dir:
                # tmp_install_dir = Tempdir()
                # tmp_dir = Tempdir()

                build_dir = os.path.join(tmp_dir, 'output')

                num_sources = 3
                sources = self.generate_source_files(tmp_dir, num_sources, 200)

                zip_file = tmp_install_dir + "/test.zip"

                cfg = ProjectConfig(args=["--bt", "build_dir=%s" % build_dir])

                prj = Project(cfg)

                value = prj.make_entity("test_content.txt",
                                        "To add to a ZIP file")
                rename = [('test_file', sources[0])]

                prj.tools.CreateZip(
                    sources, value, target=zip_file, rename=rename)

                self.build_prj(prj, 1)

                prj.tools.CreateZip(
                    sources, value, target=zip_file, rename=rename)

                self.build_prj(prj, 0)

                self.touch_cpp_file(sources[-1])

                prj.tools.CreateZip(
                    sources, value, target=zip_file, rename=rename)
                self.build_prj(prj, 1)


# ==============================================================================

if __name__ == "__main__":
    run_local_tests()
