import time

from aql_testcase import AqlTestCase

from aql.utils import Tempfile
from aql.entity.aql_file_entity import FilePartChecksumEntity, FileChecksumEntity, FileTimestampEntity


class TestFileValue(AqlTestCase):

    def test_file_value(self):

        with Tempfile() as temp_file:
            test_string = '1234567890'

            temp_file.write(test_string.encode())
            temp_file.flush()

            temp_file_value1 = FileChecksumEntity(temp_file)
            temp_file_value2 = FileChecksumEntity(temp_file)

            self.assertEqual(temp_file_value1, temp_file_value2)
            self.assertTrue(temp_file_value1.is_actual())

            reversed_test_string = str(reversed(test_string))
            temp_file.seek(0)
            temp_file.write(reversed_test_string.encode())
            temp_file.flush()

            self.assertFalse(temp_file_value1.is_actual())

            temp_file_value2 = FileChecksumEntity(temp_file_value1)
            self.assertEqual(temp_file_value1.name, temp_file_value2.name)
            self.assertNotEqual(temp_file_value1, temp_file_value2)

            actual_value = temp_file_value1.get_actual()
            self.assertIsNot(actual_value, temp_file_value1)
            self.assertEqual(actual_value.name, temp_file_value1.name)
            self.assertEqual(actual_value.id, temp_file_value1.id)
            self.assertNotEqual(actual_value.signature, temp_file_value1.signature)

    # ----------------------------------------------------------

    def test_file_part_value(self):

        with Tempfile() as temp_file:
            test_string = '1234567890'

            temp_file.write(test_string.encode())
            temp_file.flush()

            temp_file_value1 = FilePartChecksumEntity(temp_file, offset=4)
            temp_file_value2 = FilePartChecksumEntity(temp_file, offset=4)

            self.assertEqual(temp_file_value1, temp_file_value2)
            self.assertTrue(temp_file_value1.is_actual())
            self.assertIs(temp_file_value1.get_actual(), temp_file_value1)

            temp_file.seek(0)
            temp_file.write("4321".encode())
            temp_file.flush()

            temp_file_value2 = FilePartChecksumEntity(temp_file, offset=4)

            self.assertEqual(temp_file_value1, temp_file_value2)
            self.assertTrue(temp_file_value1.is_actual())
            self.assertIs(temp_file_value1.get_actual(), temp_file_value1)

            temp_file.seek(4)
            temp_file.write("098765".encode())
            temp_file.flush()

            temp_file_value2 = FilePartChecksumEntity(temp_file_value1, offset=4)
            self.assertEqual(temp_file_value1.name, temp_file_value2.name)
            self.assertNotEqual(temp_file_value1, temp_file_value2)
            self.assertFalse(temp_file_value1.is_actual())

            actual_value = temp_file_value1.get_actual()
            self.assertIsNot(actual_value, temp_file_value1)
            self.assertEqual(actual_value.name, temp_file_value1.name)
            self.assertNotEqual(actual_value.signature, temp_file_value1.signature)

    # ----------------------------------------------------------

    def test_file_value_save_load(self):

        with Tempfile() as temp_file:
            test_string = '1234567890'

            temp_file.write(test_string.encode())
            temp_file.flush()

            temp_file_value = FileChecksumEntity(temp_file)

            self._test_save_load(temp_file_value)

        file_value = FileChecksumEntity(temp_file)
        self.assertEqual(temp_file_value.name, file_value.name)
        self.assertNotEqual(temp_file_value, file_value)
        self.assertFalse(file_value.is_actual())

    # ----------------------------------------------------------

    def test_file_part_value_save_load(self):

        with Tempfile() as temp_file:
            test_string = '1234567890'

            temp_file.write(test_string.encode())
            temp_file.flush()

            temp_file_value = FilePartChecksumEntity(temp_file, offset=5)

            self._test_save_load(temp_file_value)

        file_value = FilePartChecksumEntity(temp_file, offset=5)
        self.assertEqual(temp_file_value.name, file_value.name)
        self.assertNotEqual(temp_file_value, file_value)
        self.assertFalse(file_value.is_actual())

    # ==========================================================

    def test_file_value_time(self):
        with Tempfile() as temp_file:
            test_string = '1234567890'

            temp_file.write(test_string.encode())
            temp_file.flush()

            temp_file_value1 = FileTimestampEntity(temp_file)
            temp_file_value2 = FileTimestampEntity(temp_file)

            self.assertEqual(temp_file_value1, temp_file_value2)

            time.sleep(2)
            temp_file.seek(0)
            temp_file.write(b"0987654321")
            temp_file.close()

            FileTimestampEntity(temp_file_value1.name)
            self.assertFalse(temp_file_value1.is_actual())

            temp_file_value2 = FileTimestampEntity(temp_file_value1)
            self.assertEqual(temp_file_value1.name, temp_file_value2.name)
            self.assertNotEqual(temp_file_value1, temp_file_value2)

    # ==========================================================

    def test_file_value_time_save_load(self):

        with Tempfile() as temp_file:
            test_string = '1234567890'

            temp_file.write(test_string.encode())
            temp_file.flush()

            temp_file_value = FileTimestampEntity(temp_file)

            self._test_save_load(temp_file_value)

        file_value = FileTimestampEntity(temp_file)
        self.assertEqual(temp_file_value.name, file_value.name)
        self.assertNotEqual(temp_file_value, file_value)
        self.assertFalse(file_value.is_actual())

    # ==========================================================

    def test_file_empty_value_save_load(self):

        value1 = FileChecksumEntity('__non_exist_file__')

        value2 = FileTimestampEntity(value1.name)

        self._test_save_load(value1)
        self._test_save_load(value2)
