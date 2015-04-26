import os
import sys
import random
import uuid

sys.path.insert(
    0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))

from aql_tests import skip, AqlTestCase, run_local_tests

from aql.utils import Tempfile, Chrono
from aql.utils import DataFile, SqlDataFile

from aql.util_types import encode_str

# ==============================================================================


def generate_data(min_size, max_size):
    return encode_str(''.join(chr(random.randint(32, 127))
                              for i in range(random.randint(min_size,
                                                            max_size))))

# ==============================================================================


def generate_data_map(size, min_data_size, max_data_size):
    data_map = {}
    for i in range(0, size):
        data_id = uuid.uuid4().bytes
        data_map[data_id] = generate_data(min_data_size, max_data_size)

    return data_map

# ==============================================================================


def extend_data_map(data_map):
    for data_id in data_map:
        data_size = len(data_map[data_id])
        data_map[data_id] = generate_data(data_size + 1, data_size * 2)

# ==============================================================================


class TestDataFile(AqlTestCase):

    def _test_data_file_add(self, data_file_type):
        with Tempfile() as tmp:
            tmp.remove()

            data_map = generate_data_map(2100, 16, 128)

            df = data_file_type(tmp)
            try:
                df.self_test()

                df.clear()

                df.self_test()

                for data_id, data in data_map.items():
                    df.write_with_key(data_id, data)
                    df.self_test()
                    stored_data = df.read(data_id)
                    self.assertEqual(stored_data, data)

            finally:
                df.close()

    # ==========================================================

    def _test_data_file_update(self, data_file_type):
        with Tempfile() as tmp:
            tmp.remove()

            data_map = generate_data_map(100, 16, 128)
            data_keys = {}

            df = data_file_type(tmp)
            try:
                df.self_test()

                df.clear()

                df.self_test()

                for data_id, data in data_map.items():
                    df.write(data_id, data)
                    df.self_test()
                    stored_data = df.read(data_id)
                    self.assertEqual(stored_data, data)

                extend_data_map(data_map)

                for data_id, data in data_map.items():
                    df.write(data_id, data)
                    df.self_test()
                    stored_data = df.read(data_id)
                    self.assertEqual(stored_data, data)

                df.close()
                df.self_test()

                df.open(tmp)
                df.self_test()

                for data_id, data in data_map.items():
                    stored_data = df.read(data_id)
                    self.assertEqual(stored_data, data)

                for data_id, data in data_map.items():
                    key = df.write_with_key(data_id, data)
                    df.self_test()
                    data_keys[data_id] = key
                    tmp_data_id = df.get_ids([key])[0]
                    self.assertEqual(tmp_data_id, data_id)
                    new_key = df.write_with_key(data_id, data)
                    df.self_test()
                    self.assertGreater(new_key, key)
                    self.assertIsNone(df.get_ids([key]))
                    self.assertSequenceEqual(df.get_ids([new_key]), [data_id])

                    stored_data = df.read(data_id)
                    self.assertEqual(stored_data, data)

                for data_id in data_map:
                    df.remove((data_id,))

            finally:
                df.close()

    # ==========================================================

    def _test_data_file_remove(self, data_file_type):
        with Tempfile() as tmp:
            tmp.remove()

            data_map = generate_data_map(1025, 16, 128)

            df = data_file_type(tmp)
            try:
                df.self_test()

                df.clear()

                df.self_test()

                for data_id, data in data_map.items():
                    df.write(data_id, data)

                for data_id in data_map:
                    df.remove((data_id,))
                    df.self_test()

                df.close()
                df = data_file_type(tmp)
                df.self_test()

                for data_id, data in data_map.items():
                    df.write(data_id, data)

                df.remove(data_map)
                df.self_test()

                for data_id, data in data_map.items():
                    df.write(data_id, data)

                data_ids = list(data_map)
                random.shuffle(data_ids)

                df.remove(data_ids[:len(data_ids) // 2])
                df.self_test()

                df.close()
                df = data_file_type(tmp)
                df.self_test()

                df.remove(data_ids[len(data_ids) // 2:])
                df.self_test()

                for data_id, data in data_map.items():
                    df.write(data_id, data)

                data_ids = list(data_map)
                remove_data_ids1 = [data_ids[i * 2 + 0]
                                    for i in range(len(data_ids) // 2)]
                remove_data_ids2 = [data_ids[i * 2 + 1]
                                    for i in range(len(data_ids) // 2)]
                df.remove(remove_data_ids1)
                df.self_test()

                df.close()
                df = data_file_type(tmp)
                df.self_test()

                for data_id in remove_data_ids2:
                    data = data_map[data_id]
                    stored_data = df.read(data_id)
                    self.assertEqual(stored_data, data)

                df.remove(remove_data_ids2)
                df.self_test()

            finally:
                df.close()

    # -----------------------------------------------------------

    def _test_data_file_speed(self, data_file_type):

        with Tempfile() as tmp:
            timer = Chrono()

            with timer:
                data_map = generate_data_map(20000, 123, 123)

            print("generate data time: %s" % timer)

            df = data_file_type(tmp)
            try:

                with timer:
                    for data_id, data in data_map.items():
                        df.write_with_key(data_id, data)

                print("add time: %s" % timer)

                df.close()

                with timer:
                    df = data_file_type(tmp)
                print("load time: %s" % timer)

                with timer:
                    for data_id, data in data_map.items():
                        df.write_with_key(data_id, data)

                print("update time: %s" % timer)

                with timer:
                    for data_id in data_map:
                        df.read(data_id)

                print("read time: %s" % timer)

                data_ids = list(data_map)
                remove_data_ids1 = [data_ids[i * 2 + 0]
                                    for i in range(len(data_ids) // 2)]
                remove_data_ids2 = [data_ids[i * 2 + 1]
                                    for i in range(len(data_ids) // 2)]
                with timer:
                    df.remove(remove_data_ids1)
                    df.remove(remove_data_ids2)

                print("remove time: %s" % timer)

            finally:
                df.close()

    @skip
    def test_data_file_speed(self):
        self._test_data_file_speed(DataFile)

    @skip
    def test_data_file_speed_sql(self):
        self._test_data_file_speed(SqlDataFile)

    def test_data_file_add(self):
        self._test_data_file_add(DataFile)

    def test_data_file_add_sql(self):
        self._test_data_file_add(SqlDataFile)

    def test_data_file_update(self):
        self._test_data_file_update(DataFile)

    def test_data_file_update_sql(self):
        self._test_data_file_update(SqlDataFile)

    def test_data_file_remove(self):
        self._test_data_file_remove(DataFile)

    def test_data_file_remove_sql(self):
        self._test_data_file_remove(SqlDataFile)


# ==============================================================================

if __name__ == "__main__":
    run_local_tests()
