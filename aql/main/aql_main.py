#
# Copyright (c) 2013-2015 The developers of Aqualid project
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
from aql.utils import eventStatus, eventError, EventSettings, setEventSettings, Chrono, Chdir, memoryUsage,\
                      splitPath, expandFilePath,\
                      logInfo, logError, setLogLevel, LOG_WARNING

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

def   _startMemoryTracing():
  try:
    import tracemalloc
  except ImportError:
    return
  
  tracemalloc.start()
  
#//===========================================================================//

def   _stopMemoryTracing():
  try:
    import tracemalloc
  except ImportError:
    return
  
  snapshot = tracemalloc.take_snapshot()
  
  _logMemoryTop( snapshot )
  
  tracemalloc.stop()

#//===========================================================================//

def _logMemoryTop( snapshot, group_by = 'lineno', limit = 30 ):
  
  try:
    import tracemalloc
    import linecache
  except ImportError:
    return

  snapshot = snapshot.filter_traces((
      tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
      tracemalloc.Filter(False, "<unknown>"),
  ))
  
  top_stats = snapshot.statistics( group_by )

  logInfo("Top %s lines" % limit)
  for index, stat in enumerate(top_stats[:limit], 1):
      frame = stat.traceback[0]
      # replace "/path/to/module/file.py" with "module/file.py"
      filename = os.sep.join(frame.filename.split(os.sep)[-2:])
      logInfo("#%s: %s:%s: %.1f KiB"
            % (index, filename, frame.lineno, stat.size / 1024))
      line = linecache.getline(frame.filename, frame.lineno).strip()
      if line:
          logInfo('    %s' % line)

  other = top_stats[limit:]
  if other:
      size = sum(stat.size for stat in other)
      logInfo("%s other: %.1f KiB" % (len(other), size / 1024))
  total = sum(stat.size for stat in top_stats)
  logInfo("Total allocated size: %.1f KiB" % (total / 1024))

#//===========================================================================//

def _printMemoryStatus():
  
  _stopMemoryTracing()
  
  mem_usage = memoryUsage()
  num_objects = len(gc.get_objects())
  
  obj_mem_usage = sum( sys.getsizeof(obj) for obj in gc.get_objects() )
  
  logInfo("GC objects: %s, size: %.1f KiB, heap memory usage: %s Kb" % (num_objects, obj_mem_usage / 1024, mem_usage))

#//===========================================================================//

def   _setBuildDir( options, makefile ):
    build_dir = options.build_dir.get()
    if os.path.isabs( build_dir ):
      return
    
    makefile_dir = os.path.abspath( os.path.dirname( makefile ) )
    options.build_dir = os.path.join( makefile_dir, build_dir )

#//===========================================================================//

def   _main( prj_cfg ):
  with Chrono() as total_elapsed:
    
    ev_settings = EventSettings( brief = not prj_cfg.verbose,
                                 with_output = not prj_cfg.no_output,
                                 trace_exec = prj_cfg.debug_exec )
    setEventSettings( ev_settings )
    
    with Chdir( prj_cfg.directory ):
      
      if prj_cfg.debug_memory:
        _startMemoryTracing()
      
      makefile = expandFilePath( prj_cfg.makefile )
      
      if prj_cfg.search_up:
        makefile = _findMakeScript( makefile )
      
      _setBuildDir( prj_cfg.options, makefile )
      
      prj = Project( prj_cfg )

      eventReadingScripts()
      
      with Chrono() as elapsed:
        prj.Script( makefile )
      
      eventReadingScriptsDone( elapsed )
      
      success = True
      
      if prj_cfg.clean:
        prj.Clear()
      
      elif prj_cfg.list_targets:
        text = prj.ListTargets()
        logInfo( '\n'.join( text ) )
      
      elif prj_cfg.list_options or prj_cfg.list_tool_options:
        text = []
        
        if prj_cfg.list_options:
          text += prj.ListOptions( brief = not prj_cfg.verbose )
        
        if prj_cfg.list_tool_options:
          text += prj.ListToolsOptions( prj_cfg.list_tool_options, brief = not prj_cfg.verbose )
        
        logInfo( '\n'.join( text ) )
      else:
        eventBuilding()
        
        with elapsed:
          success = prj.Build()
        
        eventBuildingDone( success, elapsed )
        
        if not success:
          prj.build_manager.printFails()
      
      if prj_cfg.debug_memory:
        _printMemoryStatus()
      
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
    
    if prj_cfg.silent:
      setLogLevel( LOG_WARNING )
    
    if not debug_profile:
      status = _main( prj_cfg )
    else:
      profiler = cProfile.Profile()
      
      status = profiler.runcall( _main, prj_cfg )
      
      profiler.dump_stats( debug_profile )
      
      p = pstats.Stats( debug_profile )
      p.strip_dirs()
      p.sort_stats('cumulative')
      p.print_stats( prj_cfg.debug_profile_top )
    
  except (Exception, KeyboardInterrupt) as ex:
    if with_backtrace:
      err = traceback.format_exc()
    else:
      if isinstance(ex, KeyboardInterrupt):
        err = "Keyboard Interrupt"
      else:
        err = toUnicode(ex)
  
    eventAqlError( err )
    status = 1
  
  return status
  
#//===========================================================================//
