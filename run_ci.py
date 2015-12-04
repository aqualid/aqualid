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

    result = module.run(['--capture=sys'])

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
def _run_cmd_status(cmd, path=None):

    if path:
        env = os.environ.copy()
        if isinstance(path, (list,tuple,set,frozenset)):
            path = os.pathsep.join(path)
        env['PYTHONPATH'] = path
    else:
        env = None

    print(cmd)

    p = subprocess.Popen(cmd, env=env, shell=False)
    return p.wait()


# ==============================================================================
def _run_cmd(cmd, path=None):
    status = _run_cmd_status(cmd, path)
    if status:
        sys.exit(status)


# ==============================================================================
def _fetch_repo(cur_dir, repo_name, repo_dir=None):
    if repo_dir:
        return os.path.abspath(repo_dir)

    repo_dir = os.path.join(cur_dir, repo_name)

    default_branch = 'master'

    branch = os.environ.get('TRAVIS_BRANCH')
    if not branch:
        branch = os.environ.get('APPVEYOR_REPO_BRANCH', default_branch)

    cmd = ["git", "clone", "--depth", "1",
           "https://github.com/aqualid/%s.git" % repo_name, repo_dir]

    status = _run_cmd_status(cmd + ["-b", branch])
    if status:
        if branch == default_branch:
            sys.exit(status)

        _run_cmd(cmd + ["-b", default_branch])

    return repo_dir


# ==============================================================================
def _make_aql(core_dir, args, script=None, module_dir=None):

    make_dir = os.path.join(core_dir, "make")

    cmd = [sys.executable]
    if script is None:
        cmd.extend(["-c", "import aql;import sys;sys.exit(aql.main())"])
    else:
        cmd.append(script)

    cmd.extend(["-C", make_dir, '--bt'])
    cmd.extend(args)

    path = [make_dir]
    if script is None:
        path.append(core_dir)

    elif module_dir:
        path.append(module_dir)

    _run_cmd(cmd, path)


# ==============================================================================
def _run_make(core_dir):
    _make_aql(core_dir, ['-l'])
    _make_aql(core_dir, ['-L', 'c++'])
    _make_aql(core_dir, ['-t'])
    _make_aql(core_dir, ['link'])
    _make_aql(core_dir, ['-R', 'link'])


# ==============================================================================
def _make_dist(core_dir, tools_dir):

    tools_dir = os.path.join(tools_dir, 'tools')
    args = ['-I', tools_dir, 'sdist', 'local']
    if sys.platform.startswith('win'):
        args.append('wdist')

    _make_aql(core_dir, args)


# ==============================================================================
def _run_examples(core_dir, examples_dir):

    output_dir = os.path.join(core_dir, 'make', 'output')

    module = _load_module('run_ci', examples_dir)

    module_dir = os.path.join(output_dir, 'setup', 'modules')
    script = os.path.join(output_dir, 'setup', 'scripts', 'aql')
    module.run_script(script, module_dir, examples_dir)

    standalone_script = os.path.join(output_dir, 'aql.py')
    module.run_script(standalone_script, None, examples_dir)


# ==============================================================================
def run(core_dir, tools_dir, examples_dir, run_tests=None):

    tests_dir = os.path.join(core_dir, 'tests')
    source_dir = os.path.join(core_dir, 'aql')

    if (run_tests is None) or 'tests' in run_tests:
        _run_tests(tests_dir, source_dir)

    if (run_tests is None) or 'make' in run_tests:
        _run_make(core_dir)

    if (run_tests is None) or 'flake8' in run_tests:
        # check for PEP8 violations, max complexity and other standards
        _run_flake8(_find_files(source_dir), complexity=9)

        # check for PEP8 violations
        _run_flake8(_find_files(tests_dir))

        make_srcs = _find_files(os.path.join(core_dir, 'make'), recursive=False)
        _run_flake8(make_srcs)

        _run_flake8(os.path.join(core_dir, 'make', 'make.aql'), ignore='F821')

    if (run_tests is None) or \
       ('dist' in run_tests) or \
       ('examples' in run_tests):

        tools_dir = _fetch_repo(core_dir, 'tools', tools_dir)
        _make_dist(core_dir, tools_dir)

    if (run_tests is None) or 'tools' in run_tests:
        tools_dir = _fetch_repo(core_dir, 'tools', tools_dir)
        examples_dir = _fetch_repo(core_dir, 'examples', examples_dir)

        module = _load_module('run_ci', tools_dir)
        module.run(core_dir, tools_dir, examples_dir)

    if (run_tests is None) or 'examples' in run_tests:
        _run_examples(core_dir, examples_dir)


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
    choices = ('tests', 'make', 'dist', 'flake8', 'tools', 'examples')

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
