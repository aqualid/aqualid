#!/usr/bin/env python

import os
import sys
import imp
import uuid
import argparse
import subprocess


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
    module = _load_module('run', tests_dir)

    try:
        import coverage
    except Exception:
        print("WARNING: Module 'coverage' has not been found")
        cov = None
    else:
        cov = coverage.coverage(source=[source_dir])

    if cov is not None:
        cov.start()

    result = module.run([])

    if cov is not None:
        cov.stop()
        cov.save()

    if result:
        sys.exit(result)


# ==============================================================================
def _run_flake8(source_files, ignore=None, complexity=-1):
    try:
        import flake8.main
    except Exception:
        print("WARNING: flake8 has not been found")
        return

    if not isinstance(source_files, (list, tuple, frozenset, set)):
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
        if isinstance(path, (list, tuple, set, frozenset)):
            path = os.pathsep.join(path)

        env['PYTHONPATH'] = path
    else:
        env = None

    print(cmd)

    p = subprocess.Popen(cmd, env=env, shell=False)
    result = p.wait()

    if result:
        sys.exit(result)


# ==============================================================================
def _fetch_repo(cur_dir, repo_name, repo_dir=None):
    if repo_dir:
        repo_dir = os.path.abspath(repo_dir)
    else:
        repo_dir = os.path.join(cur_dir, repo_name)

        _run_cmd(["git", "clone", "-b", "master", "--depth", "1",
                  "https://github.com/aqualid/%s.git" % repo_name, repo_dir])

    print("%s: %s" % (repo_name, repo_dir))

    return repo_dir


# ==============================================================================
def run(core_dir, tools_dir, examples_dir, run_tests=None):

    tests_dir = os.path.join(core_dir, 'tests')
    source_dir = os.path.join(core_dir, 'aql')

    if (run_tests is None) or 'tests' in run_tests:
        _run_tests(tests_dir, source_dir)

    if (run_tests is None) or 'make' in run_tests:
        make_dir = os.path.join(core_dir, "make")
        _run_cmd([sys.executable, "-c",
                  "import aql;import sys;sys.exit(aql.main())", "-C", make_dir,
                  "-l"], [core_dir, make_dir])

        _run_cmd([sys.executable, "-c",
                  "import aql;import sys;sys.exit(aql.main())", "-C", make_dir,
                  "-L", "c++"], [core_dir, make_dir])

        _run_cmd([sys.executable, "-c",
                  "import aql;import sys;sys.exit(aql.main())", "-C", make_dir,
                  "-t"], [core_dir, make_dir])

        _run_cmd([sys.executable, "-c",
                  "import aql;import sys;sys.exit(aql.main())", "-C", make_dir,
                  "local"], [core_dir, make_dir])

    if (run_tests is None) or 'flake8' in run_tests:
        # check for PEP8 violations, max complexity and other standards
        _run_flake8(_find_files(source_dir), complexity=9)

        # check for PEP8 violations
        _run_flake8(_find_files(tests_dir))

        make_srcs = _find_files(os.path.join(core_dir, 'make'), recursive=False)
        _run_flake8(make_srcs)

        _run_flake8(os.path.join(core_dir, 'make', 'make.aql'), ignore='F821')

    ###############
    if (run_tests is None) or 'tools' in run_tests:
        tools_dir = _fetch_repo(core_dir, 'tools', tools_dir)

        module = _load_module('run_ci', tools_dir)
        module.run(core_dir, tools_dir, examples_dir)


# ==============================================================================
def _parse_args(choices):
    args_parser = argparse.ArgumentParser()

    args_parser.add_argument('--skip', '-s', action='append', choices=choices,
                             dest='skip_tests',
                             help="Skip specific tests")

    args_parser.add_argument('--run', '-r', action='append', choices=choices,
                             dest='run_tests',
                             help="Run specific tests")

    args_parser.add_argument('--tools-dir', '-T', action='store',
                             dest='tools_dir', metavar='PATH',
                             help="Aqualid examples directory. "
                                  "By default it will be fetched from GitHub.")

    args_parser.add_argument('--examples-dir', '-E', action='store',
                             dest='examples_dir', metavar='PATH',
                             help="Aqualid examples directory. "
                                  "By default it will be fetched from GitHub.")

    return args_parser.parse_args()


# ==============================================================================
def main():
    choices = ('tests', 'make', 'flake8', 'tools')

    args = _parse_args(choices)

    core_dir = os.path.abspath(os.path.dirname(__file__))

    if args.run_tests is None:
        run_tests = set(choices)
    else:
        run_tests = set(args.run_tests)

    if args.skip_tests:
        run_tests.difference_update(args.skip_tests)

    run(core_dir, args.tools_dir, args.examples_dir, run_tests)


# ==============================================================================

if __name__ == '__main__':
    main()
