import sys
import os.path

sys.path.insert(
    0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))

from aql_tests import AqlTestCase
from tests_utils import run_local_tests

from aql.options import OptionType, BoolOptionType, EnumOptionType,\
    RangeOptionType, ListOptionType, DictOptionType, PathOptionType, \
    ErrorOptionTypeEnumAliasIsAlreadySet,\
    ErrorOptionTypeEnumValueIsAlreadySet,\
    ErrorOptionTypeUnableConvertValue, ErrorOptionTypeNoEnumValues

from aql.util_types import IgnoreCaseString, UpperCaseString, Dict, FilePath

# ==============================================================================


class TestOptionTypes(AqlTestCase):

    # ==============================================================================

    def test_bool_option(self):
        debug_symbols = BoolOptionType(description='Include debug symbols',
                                       group="Debug", style=(True, False))

        true_values = ['tRUe', 't', '1', 'Yes', 'ENABled',
                       'On', 'y', 1, 2, 3, -1, True]

        false_values = ['FAlsE', 'F', '0', 'No', 'disabled',
                        'oFF', 'N', 0, None, False]

        for t in true_values:
            v = debug_symbols(t)
            self.assertTrue(v)
            self.assertEqual(str(v), str(True))

        for t in false_values:
            v = debug_symbols(t)
            self.assertFalse(v)
            self.assertEqual(str(v), str(False))

        debug_symbols = BoolOptionType(description='Include debug symbols',
                                       group="Debug", style=('ON', 'OFF'))

        v = debug_symbols('TRUE')
        self.assertTrue(v)
        self.assertEqual(debug_symbols.to_str(v), 'ON')

        v = debug_symbols(0)
        self.assertFalse(v)
        self.assertEqual(debug_symbols.to_str(v), 'OFF')

        opt_type = BoolOptionType(
            style=('Yes', 'No'), true_values=[], false_values=[])

        self.assertEqual(opt_type.help_range(), ['Yes', 'No'])

        opt_type.add_values('Y', 'N')
        opt_type.add_values('y', 'n')
        self.assertEqual(opt_type.help_range(), ['Yes (or Y)', 'No (or N)'])

        opt_type.add_values('1', '0')

        v = opt_type('1')
        v |= opt_type(3)
        v = opt_type(v)
        self.assertEqual(v, opt_type('y'))
        v &= opt_type(100)
        v = opt_type(v)
        self.assertEqual(v, opt_type(1))
        v = v & opt_type(0)
        v = opt_type(v)
        self.assertEqual(v, 0)
        v = v | opt_type(5)
        v = opt_type(v)
        self.assertEqual(v, 1)
        v ^= opt_type(2)
        v = opt_type(v)
        self.assertEqual(v, 0)
        v = v ^ opt_type(2)
        v = opt_type(v)
        self.assertEqual(v, 1)

        self.assertNotEqual(opt_type('1'), 0)
        self.assertLess(opt_type('0'), 1)
        self.assertLessEqual(opt_type('0'), 1)
        self.assertLessEqual(opt_type('1'), 1)
        self.assertGreater(opt_type('1'), 0)
        self.assertGreaterEqual(opt_type('1'), 1)
        self.assertGreaterEqual(opt_type('1'), 0)

        bt = OptionType(value_type=bool)

        self.assertEqual(bt('1'), 1)
        self.assertNotEqual(bt('1'), 0)
        self.assertNotEqual(bt('0'), 0)
        self.assertEqual(bt(1), True)
        self.assertEqual(bt(0), False)

        self.assertEqual(str(bt(1)), str(True))
        self.assertEqual(str(bt(0)), str(False))

        bt = BoolOptionType()
        self.assertEqual(str(bt(1)), 'True')
        self.assertEqual(str(bt('disabled')), 'False')

    # ==============================================================================

    def test_enum_option(self):
        optimization = EnumOptionType(
            values=(('off', 0), ('size', 1), ('speed', 2)),
            description='Compiler optimization level',
            group="Optimization",
            default='off')

        values = ['oFF', 'siZe', 'SpeeD', '0', '1', '2', 0, 1, 2]
        base_values = ['off', 'size', 'speed', 'off',
                       'size', 'speed', 'off', 'size', 'speed']

        self.assertEqual(optimization(), 'off')
        self.assertEqual(EnumOptionType(values=[1, 2, 3, 4], default=3)(), 3)

        self.assertNotEqual(EnumOptionType(values=[1, 2, 3, 4], default=1)(),
                            3)

        for v, base in zip(values, base_values):
            self.assertEqual(optimization(v), base)

        self.assertRaises(ErrorOptionTypeUnableConvertValue, optimization, 3)

        optimization.add_values({'final': 3})

        optimization.add_values({'final': 99})
        optimization.add_values({2: 'fast'})

        self.assertRaises(ErrorOptionTypeEnumAliasIsAlreadySet,
                          optimization.add_values, {'slow': 'fast'})

        self.assertRaises(ErrorOptionTypeEnumValueIsAlreadySet,
                          optimization.add_values, {'slow': 'speed'})

        optimization.add_values(('ultra', 'speed'))
        self.assertEqual(optimization('ULTRA'), 'ultra')

        self.assertEqual(sorted(optimization.range()),
                         sorted(['slow', 'off', 'ultra',
                                 'speed', 'final', 'size']))

    # ==============================================================================

    def test_enum_option_int(self):

        optimization = EnumOptionType(values=((0, 10), (1, 100), (2, 1000)),
                                      description='Optimization level',
                                      group="Optimization",
                                      value_type=int)

        values = [0, 1, 2, 10, 100, 1000]
        base_values = [0, 1, 2, 0, 1, 2]

        for v, base in zip(values, base_values):
            self.assertEqual(optimization(v), base)

        self.assertEqual(optimization(), 0)

        self.assertRaises(ErrorOptionTypeUnableConvertValue, optimization, 3)
        self.assertRaises(
            ErrorOptionTypeUnableConvertValue, optimization, 'three')

        et = EnumOptionType(values=[])
        self.assertRaises(ErrorOptionTypeNoEnumValues, et)

    # ==============================================================================

    def test_enum_option_strict(self):
        optimization = EnumOptionType(values=((0, 10), (1, 100), (2, 1000)),
                                      value_type=int, strict=False)

        values = [0, 1, 2, 10, 100, 1000, 3, 4]
        base_values = [0, 1, 2, 0, 1, 2, 3, 4]

        for v, base in zip(values, base_values):
            self.assertEqual(optimization(v), base)

        self.assertRaises(
            ErrorOptionTypeUnableConvertValue, optimization, 'three')

        et = EnumOptionType(values=[], strict=False)
        self.assertEqual(et(), '')

    # ==============================================================================

    def test_range_option(self):
        warn_level = RangeOptionType(min_value=0, max_value=5, coerce=False,
                                     description='Warning level',
                                     group="Diagnostics")

        self.assertEqual(warn_level(0), 0)
        self.assertEqual(warn_level(5), 5)
        self.assertEqual(warn_level(3), 3)

        self.assertRaises(ErrorOptionTypeUnableConvertValue, warn_level, 10)
        self.assertRaises(ErrorOptionTypeUnableConvertValue, warn_level, -1)

        warn_level = RangeOptionType(min_value=0, max_value=5, coerce=True,
                                     description='Warning level',
                                     group="Diagnostics")

        self.assertEqual(warn_level(0), 0)
        self.assertEqual(warn_level(), 0)
        self.assertEqual(warn_level(3), 3)
        self.assertEqual(warn_level(5), 5)
        self.assertEqual(warn_level(-100), 0)
        self.assertEqual(warn_level(100), 5)

        self.assertEqual(warn_level.help_range(), ['0 ... 5'])
        self.assertEqual(warn_level.range(), [0, 5])

        warn_level.set_range(min_value=None, max_value=None, coerce=False)
        self.assertEqual(warn_level(0), 0)
        self.assertRaises(ErrorOptionTypeUnableConvertValue, warn_level, 1)

        warn_level.set_range(min_value=None, max_value=None, coerce=True)
        self.assertEqual(warn_level(0), 0)
        self.assertEqual(warn_level(10), 0)
        self.assertEqual(warn_level(-10), 0)

        self.assertRaises(ErrorOptionTypeUnableConvertValue,
                          warn_level.set_range,
                          min_value="abc",
                          max_value=None)

        self.assertRaises(ErrorOptionTypeUnableConvertValue,
                          warn_level.set_range,
                          min_value=None,
                          max_value="efg")

    # ==============================================================================

    def test_str_option(self):
        range_help = "<Case-insensitive string>"

        opt1 = OptionType(value_type=IgnoreCaseString,
                          description='Option 1',
                          group="group1",
                          range_help=range_help)

        self.assertEqual(opt1(0), '0')
        self.assertEqual(opt1('ABC'), 'abc')
        self.assertEqual(opt1('efg'), 'EFG')
        self.assertEqual(opt1(None), '')

        self.assertEqual(opt1.help_range(), [range_help])

    # ==============================================================================

    def test_int_option(self):
        opt1 = OptionType(
            value_type=int, description='Option 1', group="group1")

        self.assertEqual(opt1(0), 0)
        self.assertEqual(opt1('2'), 2)

        self.assertRaises(ErrorOptionTypeUnableConvertValue, opt1, 'a1')

        self.assertEqual(opt1.help_range(), [])

        self.assertEqual(opt1(), 0)
        self.assertEqual(opt1(1), opt1(1))

        self.assertEqual(set([opt1(7), opt1(5)]),
                         set([opt1(5), opt1(7), opt1(5)]))

    # ==============================================================================

    def test_path_option(self):
        opt1 = OptionType(
            value_type=FilePath, description='Option 1', group="group1")

        self.assertEqual(opt1('abc'), 'abc')
        # self.assertEqual( opt1( '../abc/../123' ), '../123' )
        self.assertEqual(opt1('../abc/../123'), '../abc/../123')

        self.assertEqual(opt1.help_range(), [])

    # ==============================================================================

    def test_list_option(self):
        opt1 = ListOptionType(
            value_type=FilePath, description='Option 1', group="group1")

        self.assertEqual(opt1('abc'), 'abc')
        # self.assertEqual( opt1( '../abc/../123' ), '../123' )
        self.assertEqual(opt1('../abc/../123'), '../abc/../123')
        self.assertEqual(opt1([1, 2, 3, 4]), [1, 2, 3, 4])
        self.assertEqual(opt1(), [])
        self.assertEqual(opt1(NotImplemented), [])

        b = BoolOptionType(description='Test1', group="Debug",
                           style=("On", "Off"), true_values=["Yes", "enabled"],
                           false_values=["No", "disabled"])

        ob = ListOptionType(value_type=b, unique=True)

        self.assertEqual(ob('yes,no'), 'on,disabled')
        self.assertIn('yes', ob('yes,no'))

        self.assertEqual(
            ob.help_range(), ['On (or enabled, Yes)', 'Off (or disabled, No)'])

        on = ListOptionType(
            value_type=int, unique=True, range_help="List of integers")

        self.assertEqual(on('1,0,2,1,1,2,0'), [1, 0, 2])
        self.assertRaises(ErrorOptionTypeUnableConvertValue, on, [1, 'abc'])

        self.assertEqual(on.help_range(), ["List of integers"])

        on = ListOptionType(value_type=int)
        self.assertEqual(on.help_range(), [])

    # ==============================================================================

    def test_dict_option(self):
        opt1 = OptionType(value_type=dict)

        self.assertEqual(opt1({}), {})
        self.assertEqual(opt1({'ABC': 1}), {'ABC': 1})

        opt1 = OptionType(value_type=Dict)

        self.assertEqual(opt1({}), {})
        self.assertEqual(opt1({'ABC': 1}), {'ABC': 1})

        ot = DictOptionType(key_type=int, value_type=int)

        self.assertEqual(str(ot({1: 2, 3: 4})), "1=2,3=4")
        self.assertEqual(ot("1=2,3=4"), "1=2,3=4")

        env = OptionType(value_type=Dict)()
        env['PATH'] = ListOptionType(separators=':')()
        env['PATH'] += '/work/bin'
        env['PATH'] += '/usr/bin'
        env['PATH'] += '/usr/local/bin'
        env['HOME'] = PathOptionType()('/home/user')
        env['HOME'] = '/home/guest'

        self.assertEqual(str(env['PATH']),
                         ':'.join(['/work/bin', '/usr/bin', '/usr/local/bin']))

        self.assertEqual(env['HOME'], '/home/guest')

        env = DictOptionType(key_type=UpperCaseString)()
        env['PATH'] = ListOptionType(
            value_type=PathOptionType(), separators=os.pathsep)()
        env['HOME'] = PathOptionType()()
        env['Path'] = os.path.normpath('/work/bin')
        env['Path'] += os.path.normpath('/usr/bin')
        env['path'] += os.path.normpath('/usr/local/bin')
        env['Home'] = os.path.normpath('/home/user')

        self.assertEqual(env['HOME'], os.path.normpath('/home/user'))
        self.assertEqual(str(env['PATH']),
                         os.pathsep.join(map(os.path.normpath,
                                             ['/work/bin',
                                              '/usr/bin',
                                              '/usr/local/bin'])))


# ==============================================================================

if __name__ == "__main__":
    run_local_tests()
