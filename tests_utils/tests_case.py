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

import sys
import unittest

__all__ = ('TestCaseSuite', 'TestCaseBase')

# ==============================================================================


class _ErrorHolder(object):

    def __init__(self, test_class, description, exception):
        self.description = "%s (%s)" % (description, test_class.__name__)
        # attribute used by TestResult._exc_info_to_string
        self.failureException = exception
        self.test_id = test_class.__module__ + '.' + test_class.__name__
        self.__name__ = test_class.__name__

    def shortDescription(self):     # noqa
        return None

    def __str__(self):
        return self.description

    def id(self):
        return self.test_id

# ==============================================================================


class TestCaseSuite(unittest.TestSuite):

    def __init__(self, tests=(), keep_going=False):
        super(TestCaseSuite, self).__init__(tests)
        self.keep_going = keep_going

    # -----------------------------------------------------------

    def __get_test_case_class(self):

        try:
            return next(iter(self)).__class__
        except StopIteration:
            return None

    # -----------------------------------------------------------

    def __set_up_test_case_class(self, test_case_class, result):
        if test_case_class is not None:
            # call setUpClass only if it's not supported
            if not hasattr(unittest.TestCase, 'setUpClass'):
                set_up_class = getattr(test_case_class, 'setUpClass', None)
                if set_up_class is not None:
                    try:
                        set_up_class()
                    except Exception as ex:
                        if not self.keep_going:
                            result.stop()
                        error_name = _ErrorHolder(
                            test_case_class, 'setUpClass', ex)
                        result.add_error(error_name, sys.exc_info())
                        return False

        return True

    # -----------------------------------------------------------

    def __tear_down_test_case_class(self, test_case_class, result):
        """Method tries to call tearDownClass
           method from test case instance."""

        if test_case_class is not None:
            # call tearDownClass only if it's not supported
            if not hasattr(unittest.TestCase, 'tearDownClass'):
                tear_down_class = getattr(test_case_class,
                                          'tearDownClass',
                                          None)
                if tear_down_class is not None:
                    try:
                        tear_down_class()
                    except Exception as ex:
                        if not self.keep_going:
                            result.stop()
                        error_name = _ErrorHolder(test_case_class,
                                                  'tearDownClass',
                                                  ex)
                        result.addError(error_name, sys.exc_info())

    # -----------------------------------------------------------

    def run(self, result, debug=False):

        test_case_class = self.__get_test_case_class()

        if self.__set_up_test_case_class(test_case_class, result):
            super(TestCaseSuite, self).run(result)

        self.__tear_down_test_case_class(test_case_class, result)

# ==============================================================================


class TestCaseBase(unittest.TestCase):

    def __init__(self, method_name='run_test', keep_going=False):

        self.keep_going = keep_going
        super(TestCaseBase, self).__init__(method_name)

    # -----------------------------------------------------------

    @classmethod
    def get_options(cls):
        options = getattr(cls, 'options', None)

        if options:
            return options

        from tests_options import TestsOptions
        options = TestsOptions()
        cls.options = options
        return options

    # -----------------------------------------------------------

    def __getattr__(self, attr):

        if attr == 'options':
            return self.get_options()

        raise AttributeError("Invalid attribute: '%s'" % str(attr))

    # -----------------------------------------------------------

    def run(self, result=None):
        self.result = result

        if self.keep_going or result.wasSuccessful():
            super(TestCaseBase, self).run(result)
        else:
            result.stop()

    # -----------------------------------------------------------

    def tearDown(self):     # noqa
        if not (self.keep_going or self.result.wasSuccessful()):
            self.result.stop()

    # -----------------------------------------------------------

    def setUp(self):    # noqa
        if not (self.keep_going or self.result.wasSuccessful()):
            self.result.stop()

        test_name = self.id()
        description = self.shortDescription()
        if description:
            test_name += " (%s)" % description

        print("\n*** RUN TEST: %s ***" % (test_name,))

    # -----------------------------------------------------------

    if not hasattr(unittest.TestCase, 'assertIn'):
        def assertIn(self, a, b, msg=None):         # noqa
            if msg is None:
                msg = str(a) + " in " + str(b) + ' is False'
            self.assertTrue(a in b, msg)

    if not hasattr(unittest.TestCase, 'assertNotIn'):
        def assertNotIn(self, a, b, msg=None):      # noqa
            if msg is None:
                msg = str(a) + " not in " + str(b) + ' is False'
            self.assertTrue(a not in b, msg)

    if not hasattr(unittest.TestCase, 'assertIsNone'):
        def assertIsNone(self, a, msg=None):        # noqa
            if msg is None:
                msg = str(a) + " is " + str(None) + ' is False'
            self.assertTrue(a is None, msg)

    if not hasattr(unittest.TestCase, 'assertIs'):
        def assertIs(self, a, b, msg=None):         # noqa
            if msg is None:
                msg = str(a) + " is not " + str(b)
            self.assertTrue(a is b, msg)

    if not hasattr(unittest.TestCase, 'assertIsNot'):
        def assertIsNot(self, a, b, msg=None):      # noqa
            if msg is None:
                msg = str(a) + " is " + str(b)
            self.assertTrue(a is not b, msg)

    if not hasattr(unittest.TestCase, 'assertIsNotNone'):
        def assertIsNotNone(self, a, msg=None):     # noqa
            if msg is None:
                msg = str(a) + " is not " + str(None) + ' is False'
            self.assertTrue(a is not None, msg)

    if not hasattr(unittest.TestCase, 'assertGreater'):
        def assertGreater(self, a, b, msg=None):    # noqa
            if msg is None:
                msg = str(a) + " > " + str(b) + ' is False'
            self.assertTrue(a > b, msg)

    if not hasattr(unittest.TestCase, 'assertGreaterEqual'):
        def assertGreaterEqual(self, a, b, msg=None):   # noqa
            if msg is None:
                msg = str(a) + " >= " + str(b) + ' is False'
            self.assertTrue(a >= b, msg)

    if not hasattr(unittest.TestCase, 'assertLess'):
        def assertLess(self, a, b, msg=None):       # noqa
            if msg is None:
                msg = str(a) + " < " + str(b) + ' is False'
            self.assertTrue(a < b, msg)

    if not hasattr(unittest.TestCase, 'assertLessEqual'):
        def assertLessEqual(self, a, b, msg=None):  # noqa
            if msg is None:
                msg = str(a) + " <= " + str(b) + ' is False'
            self.assertTrue(a <= b, msg)

    if not hasattr(unittest.TestCase, 'assertSequenceEqual'):
        def assertSequenceEqual(self,       # noqa
                                first,
                                second,
                                msg=None,
                                seq_type=None):
            if msg is None:
                msg = str(first) + " != " + str(second)

            if seq_type:
                self.assertEqual(type(first), type(second), msg)

            first = iter(first)
            second = iter(second)

            while True:
                try:
                    v1 = next(first)
                except StopIteration:
                    try:
                        v2 = next(second)
                    except StopIteration:
                        return

                    raise AssertionError(msg)

                try:
                    v2 = next(second)
                except StopIteration:
                    raise AssertionError(msg)

                self.assertEqual(v1, v2, msg)

    if not hasattr(unittest.TestCase, 'assertItemsEqual'):
        def assertItemsEqual(self, actual, expected, msg=None):     # noqa
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

# ==============================================================================
