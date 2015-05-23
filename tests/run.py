#!/usr/bin/env python

if __name__ == '__main__':
    import sys
    import os

    sys.path.insert(0, os.path.dirname(__file__))
    sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__),
                                                     '..')))

    from tests_utils import run_tests, TestsOptions

    options = TestsOptions.instance()
    options.set_default('test_modules_prefix', 'aql_test_')

    run_tests(options=options)

