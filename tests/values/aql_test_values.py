from aql_testcase import AqlTestCase

from aql.entity import SimpleEntity, SignatureEntity, NullEntity

# ==============================================================================


class TestValues(AqlTestCase):

    def test_str_value(self):

        value1 = SimpleEntity('http://buildsrv.com/results.out')
        value2 = SimpleEntity('http://buildsrv.com/results.out')

        self._test_save_load(value1)

        self.assertEqual(value1, value1)
        self.assertEqual(value1, value2)

        self.assertTrue(value1.is_actual())

        self._test_save_load(value2)

        value2 = SimpleEntity('http://buildsrv.com/results2.out')
        self.assertNotEqual(value1, value2)

    # ==============================================================================

    def test_str_empty_value_save_load(self):

        value1 = SimpleEntity(name='results_link')
        value2 = SimpleEntity(name=value1.name)
        self.assertEqual(value1, value2)

        self.assertFalse(value1.is_actual())
        self.assertFalse(value2.is_actual())

        self._test_save_load(value1)
        self._test_save_load(value2)

    # ==========================================================

    def test_sign_value(self):

        value1 = SignatureEntity(b'http://buildsrv.com/results.out')
        value2 = SignatureEntity(b'http://buildsrv.com/results.out')

        self._test_save_load(value1)

        self.assertEqual(value1, value1)
        self.assertEqual(value1, value2)
        self.assertTrue(value1.is_actual())

        self._test_save_load(value2)

        value2 = SignatureEntity(b'http://buildsrv.com/results2.out')
        self.assertNotEqual(value1, value2)

    # ==============================================================================

    def test_sign_empty_value_save_load(self):

        value1 = SignatureEntity(name='results_link')
        value2 = SignatureEntity(name=value1.name)
        self.assertEqual(value1, value2)

        self.assertFalse(value1.is_actual())
        self.assertFalse(value2.is_actual())

        self._test_save_load(value1)
        self._test_save_load(value2)

    # ==============================================================================

    def test_null_value(self):

        value1 = NullEntity()
        value2 = NullEntity()
        self.assertEqual(value1, value2)

        self.assertFalse(value1.is_actual())

        self._test_save_load(value1)

