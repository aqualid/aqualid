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

import optparse

__all__ = ('TestsOptions',)

try:
    StrTypes = (str, unicode)
except NameError:
    StrTypes = (str, )


def _to_sequence(value):
    if value is None:
        return None

    try:
        if isinstance(value, StrTypes):
            return value.split(',')
        else:
            return tuple(value)
    except TypeError:
        pass

    return value,

# ==============================================================================


def _exec_file(filename, in_context):
    with open(filename) as f:
        source = f.read()

    code = compile(source, filename, 'exec')
    out_context = {}
    exec(code, in_context, out_context)
    return out_context

# ==============================================================================


def _to_bool(value):
    if isinstance(value, StrTypes):
        return value.lower() == 'true'

    return bool(value)

# ==============================================================================


class CLIOption(object):
    __slots__ = (
        'cli_name', 'cli_long_name', 'opt_name', 'value_type',
        'default', 'help', 'metavar'
    )

    def __init__(self, cli_name, cli_long_name, opt_name, value_type,
                 default, description, metavar=None):

        self.cli_name = cli_name
        self.cli_long_name = cli_long_name
        self.opt_name = opt_name
        self.value_type = value_type
        self.default = value_type(default)
        self.help = description
        self.metavar = metavar

    # -----------------------------------------------------------

    def add_to_parser(self, parser):
        args = []
        if self.cli_name is not None:
            args.append(self.cli_name)

        if self.cli_long_name is not None:
            args.append(self.cli_long_name)

        if (self.value_type is bool) or (self.value_type is _to_bool):
            action = 'store_false' if self.default else 'store_true'
        else:
            action = 'store'

        kw = {'dest': self.opt_name, 'help': self.help, 'action': action}
        if self.metavar:
            kw['metavar'] = self.metavar
        parser.add_option(*args, **kw)

# ==============================================================================


class Singleton(object):

    @classmethod
    def instance(cls, *args, **kw):

        instance = cls._instance

        if not instance:
            main_dict = __import__('__main__').__dict__
            instance_name = (cls.__module__, cls.__name__)
            instance.append(main_dict.setdefault(instance_name, [None]))

        instance = instance[0]

        if instance[0] is not None:
            return instance[0]

        self = cls(*args, **kw)
        instance[0] = self

        return self

# ==============================================================================


class TestsOptions(Singleton):

    _instance = []

    # -----------------------------------------------------------

    def __init__(self, args=None):

        cli_usage = "usage: %prog [OPTIONS] [ARGUMENT=VALUE ...]"

        cli_options = (
            CLIOption("-d", "--dir", "tests_dirs", _to_sequence, '.',
                      "Tests directories", 'PATH,...'),

            CLIOption("-p", "--prefix", "test_modules_prefix",  str, 'test_',
                      "File name prefix of test modules", 'PREFIX'),

            CLIOption("-m", "--method-prefix", "test_methods_prefix", str,
                      'test', "Test methods prefix", 'PREFIX'),

            CLIOption("-f", "--config", "configs", _to_sequence, (),
                      "Path to config file(s).", 'FILE PATH, ...'),

            CLIOption("-x", "--tests", "tests", _to_sequence, None,
                      "List of tests which should be executed.",
                      "[+-~]TEST,..."),

            CLIOption(None, "--run-tests", "run_tests", _to_sequence, None,
                      "List of tests which should be executed.", "TEST,..."),

            CLIOption(None, "--skip-tests", "skip_tests", _to_sequence, None,
                      "List of tests which should be skipped.", "TEST,..."),

            CLIOption(None, "--add-tests", "add_tests", _to_sequence, None,
                      "List of tests which should be added.", "TEST,..."),

            CLIOption(None, "--continue", "start_from_tests", _to_sequence,
                      None, "Continue execution from test.", "TEST"),

            CLIOption("-k", "--keep-going", "keep_going", _to_bool, False,
                      "Keep going even if any test case failed"),

            CLIOption("-o", "--list-options", "list_options", _to_bool,
                      False, "List options and exit."),

            CLIOption("-l", "--list", "list_tests", _to_bool, False,
                      "List test cases and exit."),

            CLIOption("-r", "--reset", "reset", _to_bool, False,
                      "Reset configuration."),

            CLIOption("-v", "--verbose", "verbose", _to_bool, False,
                      "Verbose mode."),

            CLIOption("-q", "--quiet", "quiet", _to_bool, False,
                      "Quiet mode."),
        )

        super(TestsOptions, self).__setattr__('targets', tuple())
        super(TestsOptions, self).__setattr__('_set_options', set())
        super(TestsOptions, self).__setattr__('_defaults', {})

        self.__parse_arguments(cli_usage, cli_options, args)

    # -----------------------------------------------------------

    @staticmethod
    def __get_args_parser(cli_usage, cli_options):
        parser = optparse.OptionParser(usage=cli_usage)

        for opt in cli_options:
            opt.add_to_parser(parser)
        return parser

    # -----------------------------------------------------------

    def __set_defaults(self, cli_options):
        defaults = self._defaults
        for opt in cli_options:
            defaults[opt.opt_name] = (opt.default, opt.value_type)

        defaults['targets'] = (tuple(), _to_sequence)

        return defaults

    # -----------------------------------------------------------

    def __parse_values(self, args):
        targets = []

        for arg in args:
            name, sep, value = arg.partition('=')
            name = name.strip()
            if sep:
                setattr(self, name, value.strip())
            else:
                targets.append(name)

        if targets:
            self.targets = tuple(targets)

    # -----------------------------------------------------------

    def __parse_options(self, cli_options, args):
        self.__set_defaults(cli_options)

        defaults = self._defaults

        for opt in cli_options:
            name = opt.opt_name
            value = getattr(args, name)
            default, value_type = defaults[name]

            if value is None:
                value = default
            else:
                self._set_options.add(name)
                value = value_type(value)

            super(TestsOptions, self).__setattr__(name, value)

    # -----------------------------------------------------------

    def __parse_tests(self, tests):

        run_tests = None
        add_tests = None
        skip_tests = None
        start_from_tests = None

        if tests is not None:
            tests = _to_sequence(tests)
        else:
            tests = ()

        for test in tests:
            test = test.strip()
            if test.startswith('+'):
                if add_tests is None:
                    add_tests = set()

                add_tests.add(test[1:])

            elif test.startswith('-'):
                if skip_tests is None:
                    skip_tests = set()
                skip_tests.add(test[1:])

            elif test.startswith('~'):
                if start_from_tests is None:
                    start_from_tests = set()
                start_from_tests.add(test[1:])

            elif test:
                if run_tests is None:
                    run_tests = set()
                run_tests.add(test)

        if run_tests is not None:
            self.run_tests = run_tests
        if add_tests is not None:
            self.add_tests = add_tests
        if skip_tests is not None:
            self.skip_tests = skip_tests
        if start_from_tests is not None:
            self.start_from_tests = start_from_tests

    # -----------------------------------------------------------

    def __parse_arguments(self, cli_usage, cli_options, cli_args):
        parser = self.__get_args_parser(cli_usage, cli_options)
        args, values = parser.parse_args(cli_args)

        self.__parse_options(cli_options, args)
        self.__parse_values(values)
        self.__parse_tests(self.tests)

        for config in self.configs:
            self.read_config(config)

    # -----------------------------------------------------------

    def read_config(self, config_file, exec_locals=None):
        if exec_locals is None:
            exec_locals = {}

        file_locals = _exec_file(config_file, exec_locals)
        for name, value in file_locals.items():
            if name not in exec_locals:
                self.set_default(name, value)

    # -----------------------------------------------------------

    def __set(self, name, value):
        defaults = self._defaults

        try:
            value_type = defaults[name][1]
        except KeyError:
            defaults[name] = (value, type(value))
        else:
            if type(value) is not value_type:
                value = value_type(value)

        super(TestsOptions, self).__setattr__(name, value)

    # -----------------------------------------------------------

    def set_default(self, name, value):
        if name.startswith("_"):
            super(TestsOptions, self).__setattr__(name, value)
        else:
            if name not in self._set_options:
                self.__set(name, value)

    # -----------------------------------------------------------

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super(TestsOptions, self).__setattr__(name, value)
        else:
            self.__set(name, value)
            self._set_options.add(name)

    # -----------------------------------------------------------

    def __getattr__(self, name):
        return None

    # -----------------------------------------------------------

    def items(self):
        for name, value in self.__dict__.items():
            if not name.startswith("_") and (name != "targets"):
                yield (name, value)

    # -----------------------------------------------------------

    def dump(self):
        values = []
        for name in sorted(self.__dict__):
            if not name.startswith('_'):
                values.append([name, getattr(self, name)])

        return values

# ==============================================================================

if __name__ == "__main__":

    import pprint
    pprint.pprint(TestsOptions.instance().__dict__)
