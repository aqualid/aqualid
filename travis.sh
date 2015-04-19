set -ex

python tests/aql_tests.py
python -c "import aql;import sys;sys.exit(aql.main())" -C make local
python -c "import aql;import sys;sys.exit(aql.main())" -C examples/cpp_hello
python -c "import aql;import sys;sys.exit(aql.main())" -C examples/cpp_generator
python -c "import aql;import sys;sys.exit(aql.main())" -C examples/cpp_libs
python -c "import aql;import sys;sys.exit(aql.main())" -C examples/cpp_libs_1
python -c "import aql;import sys;sys.exit(aql.main())" -C examples/cpp_libs_2

pep8 `find aql -name "[a-zA-Z]*.py"`
#flake8 `find aql -name "[a-zA-Z]*.py"`
