#!/usr/bin/env python

import sys
import os
import pytest


def run():
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    aql_dir = os.path.dirname(cur_dir)

    sys.path[0:0] = [aql_dir, cur_dir]

    os.chdir(cur_dir)
    return pytest.main()

if __name__ == '__main__':
    sys.exit(run())
