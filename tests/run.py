#!/usr/bin/env python

if __name__ == '__main__':
    import sys
    import os
    import pytest

    curdir = os.path.dirname(__file__)
    os.chdir(curdir)

    sys.path.insert(0, curdir)
    sys.path.insert(0, os.path.normpath(os.path.join(curdir, '..')))

    sys.exit(pytest.main())
