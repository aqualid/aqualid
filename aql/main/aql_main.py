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

import gc
import os
import cProfile
import traceback

from aql.utils import eventStatus, eventError, EventSettings, setEventSettings, Chrono, Chdir, memoryUsage, \
                      logInfo, logError, setLogLevel, LOG_DEBUG, LOG_INFO, LOG_WARNING
from .aql_project import Project, ProjectConfig

AQL_VERSION = "0.1"

#//===========================================================================//

@eventStatus
def   eventReadingScripts( settings ):
  logInfo("Reading scripts..." )

@eventStatus
def   eventReadingScriptsDone( settings, elapsed ):
  logInfo("Reading scripts finished (%s)" % elapsed)

@eventError
def   eventAqlError( settings, error ):
  logError( error )

#//===========================================================================//

@eventStatus
def   eventBuilding( settings ):
  logInfo("Building targets...")

@eventStatus
def   eventBuildingDone( settings, success, elapsed ):
  status = "finished" if success else "failed"
  logInfo("Building targets %s (%s)" % (status, elapsed))

#//===========================================================================//

@eventStatus
def   eventBuildSummary( settings, elapsed ):
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

def   _printMemoryStatus():
  mem_usage = memoryUsage()
  num_objects = len(gc.get_objects())
  
  logInfo("Objects: %s, memory usage: %s Kb" % (num_objects, mem_usage))

#//===========================================================================//

def   _printTargets( targets ):
  text = ["  Targets:", "==================", ""]
  
  max_name = ""
  for names, is_built, description in targets:
    max_name = max( max_name, *names, key = len )
  
  name_format = "{is_built} {name:<%s}" % len(max_name)
  
  for names, is_built, description in targets:
    if len(names) > 1 and text[-1]:
      text.append('')
    
    is_built_mark = "*" if is_built else " "
    
    for name in names:
      text.append( name_format.format( name = name, is_built = is_built_mark ))
    
    text[-1] += ' :  ' + description
    
    if len(names) > 1:
      text.append('')
  
  text.append('')
  logInfo( '\n'.join(text) )

#//===========================================================================//

def   _main( prj_cfg ):
  with Chrono() as total_elapsed:
    
    ev_settings = EventSettings( brief = not prj_cfg.verbose, with_output = not prj_cfg.no_output )
    setEventSettings( ev_settings )
    
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
      
      success = True
      
      with elapsed:
        if prj_cfg.status:
          success = prj.Status( explain = prj_cfg.debug_explain )
          prj.build_manager.printStatusState()
          
        elif prj_cfg.clean:
          prj.Clean()
        
        elif prj_cfg.list_targets:
          targets = prj.ListTargets()
          _printTargets( targets )
        
        elif prj_cfg.list_options:
          options = prj.ListOptions()
          logInfo( '\n'.join( options ) )
          # _printOptions( options )
          
        else:
          success = prj.Build( jobs           = prj_cfg.jobs,
                               keep_going     = prj_cfg.keep_going,
                               build_always   = prj_cfg.build_always,
                               explain        = prj_cfg.debug_explain,
                               with_backtrace = prj_cfg.debug_backtrace )
          if not success:
            prj.build_manager.printFails()
      
      if prj_cfg.debug_memory:
        _printMemoryStatus()
      
      eventBuildingDone( success, elapsed )
        
  eventBuildSummary( total_elapsed )
  
  status = int(not success)
  
  return status


#//===========================================================================//

def   main():
  with_backtrace = True
  try:
    prj_cfg = ProjectConfig()
    with_backtrace = prj_cfg.debug_backtrace
    
    debug_profile = prj_cfg.debug_profile
    
    if not debug_profile:
      status = _main( prj_cfg )
    else:
      profiler = cProfile.Profile()
      
      status = profiler.runcall( _main, prj_cfg )
      
      profiler.dump_stats( debug_profile )
    
    return status
  except Exception as ex:
    if with_backtrace:
      err = traceback.format_exc()
    else:
      err = str(ex)

    eventAqlError( err )
  
#//===========================================================================//
