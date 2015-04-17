Aqualid [![Build Status](https://travis-ci.org/aqualid/aqualid.svg)](https://travis-ci.org/aqualid/aqualid)
=======

General purpose build tool.

Key features:
  - Flexible and scalable for large projects
  - Dynamic dependency graph
  - Batch build support
  - Distributed build scripts (no fixed project structure)
  - Support any build target types (files, strings, URLs, remote resources etc.)
  - Conditional options
  - Scons like build scripts (but don't compatible)

[Introduction](https://github.com/aqualid/aqualid/wiki/Introduction)

More information can be found in [Wiki](https://github.com/aqualid/aqualid/wiki)

Build System Shootout [results](https://github.com/aqualid/aqualid/tree/master/examples/build-shoutout)

Performance [benchmarks](https://github.com/aqualid/aqualid/wiki/Benchmark-results)
####Memory usage of full build of a synthetic project with 10k files:
![](https://github.com/menify/aqualid/blob/master/examples/benchmarks/results/10k_2/bench10k_full.png)

####Memory usage of up to date build of the project with 10k files:
![](https://github.com/menify/aqualid/blob/master/examples/benchmarks/results/10k_2/bench10k_none.png)

