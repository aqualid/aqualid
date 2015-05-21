import sys
import os.path

sys.path.insert(
    0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))

from aql_testcase import AqlTestCase
from tests_utils import run_local_tests

from aql.entity import SimpleEntity
from aql.nodes import Builder
from aql.utils import Tempfile, Tempdir, remove_user_handler, add_user_handler
from aql.builtin_tools import Tool
from aql.main import Project, ProjectConfig

# ==============================================================================


class TestNullBuilder (Builder):

    def __init__(self, options, v1, v2, v3):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        pass

# ==============================================================================


class TestTool(Tool):

    def noop(self, options, v1, v2, v3):
        return TestNullBuilder(options, v1, v2, v3)

# ==============================================================================


class TestProject(AqlTestCase):

    # noinspection PyUnusedLocal
    def event_node_building(self, settings, node):
        self.building_started += 1

    # -----------------------------------------------------------

    def setUp(self):    # noqa
        super(TestProject, self).setUp()

        self.building_started = 0
        add_user_handler(self.event_node_building)

    # -----------------------------------------------------------

    def tearDown(self):     # noqa
        remove_user_handler(self.event_node_building)

        super(TestProject, self).tearDown()

    # -----------------------------------------------------------

    def test_prj_config(self):

        with Tempfile() as f:
            cfg = b"""
abc = 123
size = 100
options.build_variant = "final"
"""
            f.write(cfg)
            f.flush()

            args = ["-v", "-j", 5, "-c", f]
            cfg = ProjectConfig(args)

            self.assertEqual(cfg.options.bv, 'final')
            self.assertEqual(cfg.jobs, 5)
            self.assertTrue(cfg.verbose)

    # -----------------------------------------------------------

    def test_prj_builtin_tools(self):

        with Tempdir() as tmp_dir:

            cfg = ProjectConfig(args=["build_dir=%s" % tmp_dir])

            prj = Project(cfg)

            prj.tools.ExecuteCommand("python", "-c", "print('test builtin')")
            prj.build()

            self.assertEqual(self.building_started, 1)
            self.assertEqual(self.built_nodes, 1)

            self.building_started = 0

            prj = Project(cfg)
            prj.tools.ExecuteCommand("python", "-c", "print('test builtin')")
            prj.build()

            self.assertEqual(self.building_started, 0)

    # -----------------------------------------------------------

    def test_prj_targets(self):

        with Tempdir() as tmp_dir:

            cfg = ProjectConfig(args=["build_dir=%s" % tmp_dir, "test", "run"])

            prj = Project(cfg)

            cmd = prj.tools.ExecuteCommand(
                "python", "-c", "print('test builtin')")

            prj.tools.ExecuteCommand("python", "-c", "print('test other')")

            self.assertSequenceEqual(prj.get_build_targets(), ['test', 'run'])

            prj.alias_nodes(prj.get_build_targets(), cmd)
            prj.build()

            self.assertEqual(self.built_nodes, 1)

    # -----------------------------------------------------------

    def test_prj_default_targets(self):

        with Tempdir() as tmp_dir:

            cfg = ProjectConfig(args=["build_dir=%s" % tmp_dir])

            prj = Project(cfg)

            prj.tools.ExecuteCommand(
                "python", "-c", "print('test builtin')")
            cmd_other = prj.tools.ExecuteCommand(
                "python", "-c", "print('test other')")
            cmd_other2 = prj.tools.ExecuteCommand(
                "python", "-c", "print('test other2')")

            prj.default_build([cmd_other, cmd_other2])
            prj.build()

            self.assertEqual(self.built_nodes, 2)

    # ==========================================================

    def test_prj_implicit_value_args(self):

        with Tempdir() as tmp_dir:

            cfg = ProjectConfig(args=["build_dir=%s" % tmp_dir])

            prj = Project(cfg)

            tool = prj.tools.add_tool(TestTool)

            tool.noop(v1="a", v2="b", v3="c")
            prj.build()

            self.assertEqual(self.built_nodes, 1)

            # -----------------------------------------------------------

            self.built_nodes = 0

            tool.noop(v1="aa", v2="bb", v3="cc")
            prj.build()
            self.assertEqual(self.built_nodes, 0)

            # -----------------------------------------------------------

            self.built_nodes = 0

            v1 = SimpleEntity("a", name="value1")

            tool.noop(v1=v1, v2="b", v3="c")
            prj.build()
            self.assertEqual(self.built_nodes, 1)

            # -----------------------------------------------------------

            self.built_nodes = 0

            v1 = SimpleEntity("ab", name="value1")

            tool.noop(v1=v1, v2="b", v3="c")
            prj.build()
            self.assertEqual(self.built_nodes, 1)

            # -----------------------------------------------------------

            self.built_nodes = 0

            v1 = SimpleEntity("ab", name="value1")

            tool.noop(v1=v1, v2="b", v3="c")
            prj.build()
            self.assertEqual(self.built_nodes, 0)

# ==============================================================================

if __name__ == "__main__":
    run_local_tests()
