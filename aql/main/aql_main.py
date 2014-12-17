#
# Copyright (c) 2013 The developers of Aqualid project
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
import sys
import cProfile
import pstats
import traceback

from aql.util_types import toUnicode
from aql.utils import eventStatus, eventError, EventSettings, setEventSettings, Chrono, Chdir, memoryUsage, splitPath, \
                      logInfo, logError, setLogLevel, LOG_DEBUG, LOG_INFO, LOG_WARNING

from .aql_project import Project, ProjectConfig
from .aql_info import getAqlInfo, dumpAqlInfo

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

def   _findMakeScript( script ):
  
  if os.path.isabs( script ):
    return script
  
  cwd = splitPath( os.path.abspath('.') )
  path_sep = os.path.sep
  
  while cwd:
    script_path = path_sep.join( cwd ) + path_sep + script
    if os.path.isfile( script_path ):
      return os.path.normpath( script_path )
    
    cwd.pop()
  
  return script

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

def   _main( prj_cfg ):
  with Chrono() as total_elapsed:
    
    ev_settings = EventSettings( brief = not prj_cfg.verbose, with_output = not prj_cfg.no_output )
    setEventSettings( ev_settings )
    
    with Chdir( prj_cfg.directory ):
      makefile = prj_cfg.makefile
      
      if prj_cfg.search_up:
        makefile = _findMakeScript( makefile )
      
      prj = Project( prj_cfg )

      eventReadingScripts()
      
      with Chrono() as elapsed:
        prj.Script( makefile )
      
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
          text = prj.ListTargets()
          logInfo( '\n'.join( text ) )
        
        elif prj_cfg.list_options:
          text = prj.ListOptions( brief = not prj_cfg.verbose )
          logInfo( '\n'.join( text ) )
          
        else:
          success = prj.Build()
          if not success:
            prj.build_manager.printFails()
      
      if prj_cfg.debug_memory:
        _printMemoryStatus()
      
      eventBuildingDone( success, elapsed )
        
  eventBuildSummary( total_elapsed )
  
  status = int(not success)
  
  return status

#//===========================================================================//

def _patchSysModules():
    aql_module = sys.modules.get( 'aql', None )
    if aql_module is not None:
      sys.modules.setdefault( getAqlInfo().module, aql_module )
    else:
      aql_module = sys.modules.get( getAqlInfo().module, None )
      if aql_module is not None:
        sys.modules.setdefault( 'aql', aql_module )

#//===========================================================================//

def   main():
  with_backtrace = True
  try:
    _patchSysModules()
    
    prj_cfg = ProjectConfig()
    with_backtrace = prj_cfg.debug_backtrace
    
    debug_profile = prj_cfg.debug_profile

    if prj_cfg.show_version:
      logInfo( dumpAqlInfo() )
      return 0

    if not debug_profile:
      status = _main( prj_cfg )
    else:
      profiler = cProfile.Profile()
      
      status = profiler.runcall( _main, prj_cfg )
      
      profiler.dump_stats( debug_profile )
      
      p = pstats.Stats( debug_profile )
      p.strip_dirs()
      p.sort_stats('cumulative')
      p.print_stats( 30 )
    
    return status
  except (Exception, KeyboardInterrupt) as ex:
    if with_backtrace:
      err = traceback.format_exc()
    else:
      if isinstance(ex, KeyboardInterrupt):
        err = "Keyboard Interrupt"
      else:
        err = toUnicode(ex)
  
    eventAqlError( err )
  
#//===========================================================================//
