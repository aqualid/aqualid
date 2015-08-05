#!/usr/bin/env python

if __name__ == '__main__':
    import sys
    import os

    curdir = os.path.dirname(__file__)

    sys.path.insert(0, curdir)
    sys.path.insert(0, os.path.normpath(os.path.join(curdir, '..')))

    import pytest
    sys.exit( pytest.main() )
