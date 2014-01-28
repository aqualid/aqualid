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
__all__ = ( 'main', )


import os
import cProfile

from aql.utils import eventStatus, logInfo, Chrono, Chdir, \
                      setLogLevel, LOG_DEBUG, LOG_INFO, LOG_WARNING
from .aql_project import Project, ProjectConfig

#//===========================================================================//

@eventStatus
def   eventReadingScripts():
  logInfo("Reading scripts..." )

@eventStatus
def   eventReadingScriptsDone( elapsed ):
  logInfo("Reading scripts finished (%s)" % elapsed)

#//===========================================================================//

@eventStatus
def   eventBuilding():
  logInfo("Building targets...")

@eventStatus
def   eventBuildingDone( elapsed ):
  logInfo("Building targets finished (%s)" % elapsed)

#//===========================================================================//

@eventStatus
def   eventBuildSummary( elapsed ):
  logInfo("Total time: %s" % elapsed)

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

def _setLogLevel( level ):
  
  if level <= 0:
    level = LOG_WARNING
  elif level == 1:
    level = LOG_INFO
  else:
    level = LOG_DEBUG
  
  setLogLevel( level )

#//===========================================================================//

def   _main( prj_cfg ):
  with Chrono() as total_elapsed:
    
    _setLogLevel( prj_cfg.log_level )
    
    with Chdir( prj_cfg.directory ):
      makefile = prj_cfg.makefile
      targets = prj_cfg.targets
      options = prj_cfg.options
      
      prj = Project( options, targets )
      
      eventReadingScripts()
      
      with Chrono() as elapsed:
        prj.Include( makefile )
      
      eventReadingScriptsDone( elapsed )
      
      eventBuilding()
      
      with elapsed:
        prj.Build( jobs = prj_cfg.jobs, keep_going = prj_cfg.keep_going, verbose = prj_cfg.verbose )
      
      eventBuildingDone( elapsed )
        
  eventBuildSummary( total_elapsed )


#//===========================================================================//

def   main():
  prj_cfg = ProjectConfig()
  
  profile = prj_cfg.profile
  
  if not profile:
    _main( prj_cfg )
  else:
    profiler = cProfile.Profile()
    
    profiler.runcall( _main, prj_cfg )
    
    profiler.dump_stats( profile )
  
  # from meliae import scanner
  # scanner.dump_all_objects('objs_dump.json')
  # import objgraph
  # objgraph.show_most_common_types( 20 )
    
    
  
#//===========================================================================//
