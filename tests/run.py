#!/usr/bin/env python

if __name__ == '__main__':
    import sys
    import os
    import pytest

    curdir = os.path.abspath(os.path.dirname(__file__))
    aqldir = os.path.dirname(curdir)

    sys.path[0:0] = [aqldir, curdir]

    os.chdir(curdir)
    sys.exit(pytest.main())
