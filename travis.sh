set -ex

python tests/aql_tests.py
python -c "import aql;import sys;sys.exit(aql.main())" -C make local -I $PWD/tools
python -c "import aql;import sys;sys.exit(aql.main())" -C examples/cpp_hello -I $PWD/tools
python -c "import aql;import sys;sys.exit(aql.main())" -C examples/cpp_hello -I $PWD/tools -R
python -c "import aql;import sys;sys.exit(aql.main())" -C examples/cpp_generator -I $PWD/tools
python -c "import aql;import sys;sys.exit(aql.main())" -C examples/cpp_generator -I $PWD/tools -R
python -c "import aql;import sys;sys.exit(aql.main())" -C examples/cpp_libs -I $PWD/tools
python -c "import aql;import sys;sys.exit(aql.main())" -C examples/cpp_libs_1 -I $PWD/tools
python -c "import aql;import sys;sys.exit(aql.main())" -C examples/cpp_libs_2 -I $PWD/tools
python -c "import aql;import sys;sys.exit(aql.main())" -C examples/cpp_libs_2 -I $PWD/tools -R

flake8 `find aql -name "[a-zA-Z]*.py"`
#flake8 --max-complexity=7 `find aql -name "[a-zA-Z]*.py"`
