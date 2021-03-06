from aql_testcase import AqlTestCase

from aql.utils import CLIOption, CLIConfig, Tempfile


class TestCLIConfig(AqlTestCase):

    def test_cli_config(self):

        cli_options = (
            CLIOption("-l", "--log-level", "log_level", int, None,
                      "", 'NUMBER'),

            CLIOption("-j", "--jobs", "jobs", int, 1, "", 'NUMBER'),
            CLIOption("-s", "--size", "size", int, 256, "", 'NUMBER'),
            CLIOption("-q", "--quite", "quite", bool, False,  ""),
            CLIOption("-v", "--verbose", "verbose", bool, False,  ""),
        )

        config = CLIConfig(cli_options, ["-j", "0", "-v", "-s32", "foo",
                                         "bv=release", "jobs=10"])

        config.set_default('jobs', 3)
        config.set_default('size', 10)
        config.set_default('new_size', 2)
        self.assertEqual(config.jobs, 10)
        self.assertEqual(config.size, 32)
        self.assertIs(config.log_level, None)
        self.assertEqual(config.new_size, 2)
        self.assertSequenceEqual(config.targets, ['foo'])
        self.assertEqual(config.bv, 'release')
        self.assertFalse(config.quite)
        self.assertTrue(config.verbose)

        config.set_default('log_level', 1)
        self.assertEqual(config.log_level, 1)

        config.log_level = 2
        config.set_default('log_level', 0)
        self.assertEqual(config.log_level, 2)

        config.jobs = 10
        self.assertEqual(config.jobs, 10)
        config.size = 20
        self.assertEqual(config.size, 20)
        config.new_size = 1
        self.assertEqual(config.new_size, 1)

        config.set_default('new_size', 30)
        self.assertTrue(config.new_size, 1)

    # ==========================================================

    def test_cli_config_file(self):

        cli_options = (
            CLIOption("-j", "--jobs", "jobs", int, 1, "", 'NUMBER'),
            CLIOption("-s", "--size", "size", int, 256, "", 'NUMBER'),
            CLIOption("-q", "--quite", "quite", bool, False,  ""),
            CLIOption("-v", "--verbose", "verbose", bool, False,  ""),
        )

        with Tempfile() as f:
            cfg = b"""
abc = 123
size = 100
jobs = 4
options['BUILD'] = "DEBUG"
targets="test1 test2 test3"
"""
            f.write(cfg)
            f.flush()

            config = CLIConfig(cli_options,
                               ["-j", "0", "-v", "foo", "bar",
                                "bv=release", "jobs=10"])
            options = {}
            config.read_file(f, {'options': options})

            self.assertRaises(AttributeError, getattr, config, 'options')
            self.assertEqual(config.abc, 123)
            self.assertEqual(options['BUILD'], 'DEBUG')
            self.assertEqual(config.jobs, 10)
            self.assertEqual(config.size, 100)
            self.assertEqual(config.targets, "foo, bar")

            config = CLIConfig(cli_options, ["-j", "0", "-v",
                                             "bv=release", "jobs=10"])
            options = {}
            config.read_file(f, {'options': options})

            self.assertEqual(
                config.targets, ["test1", "test2", "test3", "test3"])

            cli_values = {'abc': 123, 'jobs': 10, 'verbose': True,
                          'quite': False, 'bv': 'release', 'size': 100}

            self.assertEqual(dict(config.items()), cli_values)
