Aqualid [![Linux Build Status](https://travis-ci.org/aqualid/aqualid.svg?branch=master)](https://travis-ci.org/aqualid/aqualid)  [![Windows Build status](https://ci.appveyor.com/api/projects/status/07s07rddxv9r3hgc?svg=true)](https://ci.appveyor.com/project/menify/aqualid) [![Code Health](https://landscape.io/github/aqualid/aqualid/master/landscape.svg?style=flat)](https://landscape.io/github/aqualid/aqualid/master) [![CoverageStatus](https://coveralls.io/repos/aqualid/aqualid/badge.svg?branch=pep8)](https://coveralls.io/r/aqualid/aqualid)
=======

General purpose build tool.

Key features:
  - Flexible and scalable for large projects
  - Dynamic dependency graph
  - Batch build support
  - Distributed build scripts (no fixed project structure)
  - Support any build target types (files, strings, URLs, remote resources etc.)
  - Conditional options
  - Scons like build scripts (but not compatible)

[Introduction](https://github.com/aqualid/aqualid/wiki/Introduction)

More information can be found in [Wiki](https://github.com/aqualid/aqualid/wiki)

Questions/Discussions can be posted to [Group](http://groups.google.com/d/forum/aqualid)

Build System Shootout [results](https://github.com/aqualid/aqualid/tree/master/examples/build-shoutout)

Performance [benchmarks](https://github.com/aqualid/aqualid/wiki/Benchmark-results)
####Memory usage of full build of a synthetic project with 10k files:
![](https://github.com/menify/aqualid/blob/master/examples/benchmarks/results/10k_2/bench10k_full.png)

####Memory usage of up to date build of the project with 10k files:
![](https://github.com/menify/aqualid/blob/master/examples/benchmarks/results/10k_2/bench10k_none.png)

