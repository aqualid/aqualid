#!/usr/bin/env python

import os
import sys
import imp
import uuid
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

def _run_module(module_dir, core_dir, tools_dir):
    fp, pathname, description = imp.find_module('run_ci', [module_dir])
    module = imp.load_module(uuid.uuid4().hex, fp, pathname, description)

    module.run(core_dir, tools_dir)


# ==============================================================================

def _run_cmd(cmd, path=None):

    if path:
        env = os.environ.copy()
        env['PYTHONPATH'] = path
    else:
        env = None

    print(cmd)

    p = subprocess.Popen(cmd, env=env, shell=False)
    returncode = p.wait()

    if returncode:
        sys.exit(returncode)


# ==============================================================================

def run(core_dir):

    tests_dir = os.path.join(core_dir, 'tests')
    source_dir = os.path.join(core_dir, 'aql')
    run_tests = os.path.join(tests_dir, 'run.py')

    _run_cmd(['coverage', 'run', "--source=%s" % source_dir, run_tests], core_dir )

    # check for PEP8 violations, max complexity and other standards
    _run_cmd(["flake8", "--max-complexity=9", "--ignore=F403"] + _find_files( source_dir ))

    # check for PEP8 violations
    _run_cmd(["flake8"] + _find_files( tests_dir ))
    _run_cmd(["flake8"] + _find_files( os.path.join(core_dir, 'make'), recursive=False))
    _run_cmd(["flake8", os.path.join(core_dir, 'make', 'make.aql')])

    # test tools
    # _run_cmd(["git", "clone", "-b", "pytest", "--depth", "1", "https://github.com/aqualid/tools.git"])
    # tools_dir = os.path.join(core_dir, 'tools')
    tools_dir = "/home/me/work/src/aqualid/tools"

    _run_module(tools_dir, core_dir, tools_dir)


# ==============================================================================

def main():
    core_dir = os.path.abspath(os.path.dirname(__file__))
    run(core_dir)


# ==============================================================================

if __name__ == '__main__':
    main()
