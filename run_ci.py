#!/usr/bin/env python

import os
import sys
import imp
import uuid
import subprocess

import coverage
import flake8.main


# ==============================================================================
def _find_files(path, recursive=True):

    found_files = []

    for root, folders, files in os.walk(path):
        for file_name in files:
            file_name = os.path.normcase(file_name)
            if file_name.endswith('.py'):
                found_files.append(os.path.join(root, file_name))

        if recursive:
            folders[:] = (folder for folder in folders
                            if not folder.startswith('.'))
        else:
            folders[:] = []

    found_files.sort()
    return found_files


# ==============================================================================
def _load_module(name, path):
    fp, pathname, description = imp.find_module(name, [path])
    return imp.load_module(uuid.uuid4().hex, fp, pathname, description)


# ==============================================================================
def _run_tests(tests_dir, source_dir):

    cov = coverage.coverage(source=[source_dir])

    module = _load_module('run', tests_dir)

    cov.start()
    result = module.run()
    cov.stop()
    cov.save()

    if result:
        sys.exit(result)


# ==============================================================================
def _run_flake8( source_files, ignore=None, complexity=-1):
    if not isinstance(source_files, (list,tuple,frozenset,set)):
        source_files = (source_files,)

    ignore_errors = ('F403', 'E241')

    if ignore:
        if isinstance(ignore, (list, tuple, frozenset, set)):
            ignore = tuple(ignore)
        else:
            ignore = (ignore,)

        ignore_errors += ignore

    for source_file in source_files:
        print("flake8 %s" % source_file)
        result = flake8.main.check_file(source_file,
                                        ignore=ignore_errors,
                                        complexity=complexity)
        if result:
            sys.exit(result)


# ==============================================================================
def _run_cmd(cmd, path=None):

    if path:
        env = os.environ.copy()
        env['PYTHONPATH'] = path
    else:
        env = None

    print(cmd)

    p = subprocess.Popen(cmd, env=env, shell=False)
    result = p.wait()

    if result:
        sys.exit(result)


# ==============================================================================
def run(core_dir):

    tests_dir = os.path.join(core_dir, 'tests')
    source_dir = os.path.join(core_dir, 'aql')

    _run_tests(tests_dir, source_dir)

    # python -c "import aql;import sys;sys.exit(aql.main())" -C make - l
    # python -c "import aql;import sys;sys.exit(aql.main())" -C make - L c++
    make_dir = os.path.join(core_dir,"make")
    _run_cmd([sys.executable, "-c",
              "import aql;import sys;sys.exit(aql.main())", "-C", make_dir, "-l"], make_dir)

    _run_cmd([sys.executable, "-c",
              "import aql;import sys;sys.exit(aql.main())", "-C", make_dir, "-L", "c++"], make_dir)

    # check for PEP8 violations, max complexity and other standards
    _run_flake8(_find_files( source_dir ), complexity=9)

    # check for PEP8 violations
    _run_flake8(_find_files(tests_dir))
    _run_flake8(_find_files(os.path.join(core_dir, 'make'), recursive=False))
    _run_flake8(os.path.join(core_dir, 'make', 'make.aql'), ignore='F821')

    ###############
    # test tools
    tools_dir = os.path.join(core_dir, 'tools')
    _run_cmd(["git", "clone", "-b", "pytest", "--depth", "1", "https://github.com/aqualid/tools.git", tools_dir])

    module = _load_module('run_ci', tools_dir)
    module.run(core_dir, tools_dir)


# ==============================================================================

def main():
    core_dir = os.path.abspath(os.path.dirname(__file__))
    run(core_dir)


# ==============================================================================

if __name__ == '__main__':
    main()
