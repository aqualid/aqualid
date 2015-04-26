import sys
import os
import os.path
import stat

sys.path.insert(
    0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))

from aql_tests import AqlTestCase
from tests_utils import run_local_tests

from aql.utils import equal_function_args, check_function_args,\
    get_function_name, execute_command, flatten_list, group_items, Tempfile,\
    get_shell_script_env


class TestUtils(AqlTestCase):

    # ==============================================================================

    def test_equal_function_args(self):
        def f0(a, b, c):
            pass

        def f1(a, b, c):
            pass

        self.assertTrue(equal_function_args(f0, f1))

        def f2(a, b, c, *args):
            pass

        def f3(a, b, c, *args):
            pass

        self.assertTrue(equal_function_args(f2, f3))

        def f4(a, b, c=3, *args, **kw):
            pass

        def f5(a, b, c, *args, **kw):
            pass

        self.assertTrue(equal_function_args(f4, f5))

        def f6(a, b, c):
            pass

        def f7(a, b, c, *args):
            pass

        self.assertFalse(equal_function_args(f6, f7))

    # ==============================================================================

    def test_check_function_args(self):
        def f():
            pass

        def f0(a, b, c):
            pass

        def f1(a, b, c, d=0, e=1, f=2, *args, **kw):
            pass

        args = []
        kw = {}

        self.assertTrue(check_function_args(f, args, kw))

        args = [1, 2, 3]
        kw = {}

        self.assertTrue(check_function_args(f0, args, kw))

        args = []
        kw = {'a': 2, 'c': 4, 'b': 3}

        self.assertTrue(check_function_args(f0, args, kw))

        args = [1]
        kw = {'c': 4, 'b': 3}

        self.assertTrue(check_function_args(f0, args, kw))

        kw = {'g': 4, 'f': 3}
        args = [1, 2, 3, 4, 5]

        self.assertTrue(check_function_args(f1, args, kw))

        args = [1, 2, 3, 4]
        kw = {'e': 4, 'f': 3}

        self.assertTrue(check_function_args(f1, args, kw))

        args = [1, 2, 3, 4]
        kw = {'a': 4, 'f': 3}

        self.assertFalse(check_function_args(f1, args, kw))

        args = []
        kw = {'e': 4, 'f': 3, 'd': 1}

        self.assertFalse(check_function_args(f1, args, kw))

        args = []
        kw = {}

        self.assertFalse(check_function_args(f1, args, kw))

        # -----------------------------------------------------------

        class Foo:

            def test(self, a, b, c):
                pass

        class Bar(Foo):
            pass

        args = [None, 1, 2, 3]
        kw = {}

        self.assertTrue(check_function_args(Foo().test, args, kw))

    # ==============================================================================

    def test_function_name(self):
        self.assertTrue(get_function_name(), 'test_function_name')

    # ==============================================================================

    def test_exec_command(self):
        if os.name == 'nt':
            result = execute_command("route")
        else:
            result = execute_command("ls")

        self.assertTrue(result.output)

    # ==============================================================================

    def test_get_env(self):

        if os.name == 'nt':
            suffix = ".bat"
        else:
            suffix = ".sh"

        def set_env_var_str(name, value):
            if os.name == 'nt':
                return "set %s=%s\n" % (name, value)
            else:
                return "{name}={value};export {name}\n".format(name=name,
                                                               value=value)

        with Tempfile(suffix=suffix, mode="w+") as script:
            if os.name != 'nt':
                script.write("#!/bin/sh\n")
            script.write(set_env_var_str('TEST_ENV_A', 1))
            script.write(set_env_var_str('TEST_ENV_B', 2))

            script.close()

            os.chmod(script, stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR |
                     stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

            env = get_shell_script_env(script, "x86")
            self.assertGreaterEqual(len(env), 2)
            self.assertEqual(env['TEST_ENV_A'], '1')
            self.assertEqual(env['TEST_ENV_B'], '2')

    # ==============================================================================

    def test_flatten(self):

        l = []
        l_flat = []
        for i in range(2000):
            l = [l, i]
            l_flat.append(i)

        self.assertEqual(flatten_list(l), l_flat)
        self.assertEqual(flatten_list([]), [])
        self.assertEqual(flatten_list([([1, 3, 4], [2, 3])]), [1, 3, 4, 2, 3])

    # ==========================================================

    def test_groups(self):
        items = list(range(10))
        groups = group_items(items, wish_groups=2, max_group_size=-1)
        self.assertEqual(groups, [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]])

        groups = group_items(items, wish_groups=3, max_group_size=0)
        self.assertEqual(groups, [[0, 1, 2], [3, 4, 5], [6, 7, 8, 9]])

        groups = group_items(items, wish_groups=3, max_group_size=3)
        self.assertEqual(groups, [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]])

        groups = group_items(items, wish_groups=4, max_group_size=-1)
        self.assertEqual(groups, [[0, 1], [2, 3], [4, 5, 6], [7, 8, 9]])

        groups = group_items(items, wish_groups=4, max_group_size=1)
        self.assertEqual(
            groups, [[0], [1], [2], [3], [4], [5], [6], [7], [8], [9]])

        groups = group_items(items, wish_groups=1, max_group_size=0)
        self.assertEqual(groups, [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]])

        groups = group_items(items, wish_groups=1, max_group_size=-1)
        self.assertEqual(groups, [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]])

        groups = group_items(items, wish_groups=1, max_group_size=2)
        self.assertEqual(groups, [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]])

# ==============================================================================

if __name__ == "__main__":
    run_local_tests()
