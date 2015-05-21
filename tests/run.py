#!/usr/bin/env python

if __name__ == '__main__':
    from tests_utils import run_tests, TestsOptions

    options = TestsOptions.instance()
    options.set_default('test_modules_prefix', 'aql_test_')

    run_tests(options=options)

