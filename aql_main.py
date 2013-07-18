#
# Copyright (c) 2013 The developers of Aqualid project - http://aqualid.googlecode.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import os

from aql.main import Project, ProjectConfig

#//===========================================================================//

def   _findMakeScript( start_dir, main_script, main_script_default ):
  if os.path.isdir( main_script ):
    main_script = os.path.join( main_script, main_script_default )
  else:
    script_dir, main_script = os.path.split( main_script )
    if script_dir:
      return script_dir, main_script
  
  script_dir = start_dir
  
  while True:
    main_script_path = os.path.join( script_dir, main_script )
    if os.path.isfile( main_script_path ):
      return main_script_path

#//===========================================================================//

def   main():
  prj_cfg = ProjectConfig()
  
  if prj_cfg.directory:
    os.chdir( prj_cfg.directory )
  
  makefile = prj_cfg.makefile
  targets = prj_cfg.targets
  options = prj_cfg.options
  
  prj = Project( options, targets )
  
  prj.Include( makefile )
  
  #~ import timeit
  
  #~ t = timeit.timeit( prj.Build, number = 1 )
  
  #~ print("build time: %s" % t)
  
  prj.Build()


#//===========================================================================//

if __name__ == "__main__":
  main()
