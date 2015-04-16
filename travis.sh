set -ex

python tests/aql_tests.py
pep8 `find aql -name "[a-zA-Z]*.py"`
#flake8 `find aql -name "[a-zA-Z]*.py"`
