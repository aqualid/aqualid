import timeit
try:
    import c_pickle as pickle
except ImportError:
    import pickle

from aql_testcase import AqlTestCase, skip

from aql.utils import Tempfile
from aql.entity import FileChecksumEntity, FileTimestampEntity, SimpleEntity,\
    EntityPickler

# ==============================================================================


class TestValuePickler(AqlTestCase):

    def test_value_pickler(self):

        with Tempfile() as tmp:
            tmp_name = str(tmp)
            vpick = EntityPickler()
            value = FileChecksumEntity(tmp)

            vl = vpick.dumps(value)
            vl = vpick.dumps(value)
            vl = vpick.dumps(value)

            v = vpick.loads(vl)
            v = vpick.loads(vl)
            v = vpick.loads(vl)
            self.assertEqual(value, v)

            value = FileTimestampEntity(tmp)
            v = vpick.loads(vpick.dumps(value))
            self.assertEqual(value, v)

        value = SimpleEntity('123-345', name=tmp_name)
        v = vpick.loads(vpick.dumps(value))
        self.assertEqual(value, v)

        value = SimpleEntity('123-345', name=tmp_name)
        v = vpick.loads(vpick.dumps(value))
        self.assertEqual(value, v)

        value = SimpleEntity(name=tmp_name)
        v = vpick.loads(vpick.dumps(value))
        self.assertEqual(value.name, v.name)
        self.assertIsNone(v.signature)

    # ==============================================================================

    @skip
    def test_value_pickler_speed(self):

        with Tempfile() as tmp:

            vpick = EntityPickler()
            value = FileChecksumEntity(tmp)

            t = lambda vpick = vpick, value = value: \
                vpick.loads(vpick.dumps(value))

            t = timeit.timeit(t, number=10000)
            print("value picker: %s" % t)

            t = lambda vpick = vpick, value = value:\
                vpick.loads(vpick.dumps(value,
                                        protocol=pickle.HIGHEST_PROTOCOL))

            t = timeit.timeit(t, number=10000)
            print("pickle: %s" % t)

        vl = vpick.dumps(value)
        print("vl: %s" % len(vl))

        pl = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        print("pl: %s" % len(pl))
