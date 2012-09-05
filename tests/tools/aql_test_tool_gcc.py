import os
import sys

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_utils import fileChecksum, printStacks
from aql_temp_file import Tempfile, Tempdir
from aql_path_types import FilePath, FilePaths
from aql_file_value import FileValue, FileContentTimeStamp, FileContentChecksum
from aql_values_file import ValuesFile
from aql_node import Node
from aql_build_manager import BuildManager
from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_builtin_options import builtinOptions

from gcc import GccCompileCppBuilder, gccOptions

#//===========================================================================//

SRC_FILE_TEMPLATE = """
#include <cstdio>
#include "%s.h"

void  %s()
{}
"""

HDR_FILE_TEMPLATE = """
#ifndef HEADER_%s_INCLUDED
#define HEADER_%s_INCLUDED

extern void  %s();

#endif
"""

#//===========================================================================//

def   _generateSrcFile( dir, name ):
  src_content = SRC_FILE_TEMPLATE % ( name, 'foo_' + name )
  hdr_content = HDR_FILE_TEMPLATE % ( name.upper(), name.upper(), 'foo_' + name )
  
  src_file = dir.join( name + '.cpp' )
  hdr_file = dir.join( name + '.h' )
  
  with open( src_file, 'wb' ) as f:
    f.write( src_content )
  
  with open( hdr_file, 'wb' ) as f:
    f.write( hdr_content )
  
  return src_file, hdr_file

#//===========================================================================//

def   _generateSrcFiles( dir, name, count ):
  src_files = FilePaths()
  hdr_files = FilePaths()
  for i in range( count ):
    src_file, hdr_file = _generateSrcFile( dir, name + str(i) )
    src_files.append( src_file )
    hdr_files.append( hdr_file )
  
  return src_files, hdr_files

#//===========================================================================//

class TestToolGcc( AqlTestCase ):

  def test_gcc_compile(self):
    
      event_manager.setHandlers( EventHandler() )
    
    #~ with Tempdir() as tmp_dir:
      
      tmp_dir = Tempdir()
      
      root_dir = FilePath(tmp_dir)
      build_dir = root_dir.join('build')
      
      src_dir   = root_dir.join('src')
      os.makedirs( src_dir )
      
      src_files, hdr_files = _generateSrcFiles( src_dir, 'foo', 5 )
      
      options = builtinOptions()
      options.update( gccOptions() )
      
      options.cxx = "C:\\MinGW32\\bin\\g++.exe"
      
      options.build_dir_prefix = build_dir
      
      cpp_compiler = GccCompileCppBuilder( None, options )
      
      vfilename = Tempfile( dir = root_dir, suffix = '.aql.values' ).name
      
      vfile = ValuesFile( vfilename )
      try:
        
        obj = Node( cpp_compiler, map( FileValue, src_files ) )
        obj.build( None, vfile )
        
        vfile.close(); vfile.open( vfilename )
        
        obj = Node( cpp_compiler, map( FileValue, src_files ) )
        self.assertTrue( obj.actual( vfile ) )
        
        vfile.close(); vfile.open( vfilename )
        
        with open( hdr_files[0], 'a' ) as f:
          f.write("// end of file")
        
        obj = Node( cpp_compiler, map( FileValue, src_files ) )
        self.assertFalse( obj.actual( vfile, use_cache = False ) )
        obj.build( None, vfile )
        
        vfile.close(); vfile.open( vfilename )
        
        obj = Node( cpp_compiler, map( FileValue, src_files ) )
        self.assertTrue( obj.actual( vfile ) )
        
      finally:
        vfile.close()
  
#//===========================================================================//

from time import time
import threading
import sys
from collections import deque
try:
    from resource import getrusage, RUSAGE_SELF
except ImportError:
    RUSAGE_SELF = 0
    def getrusage(who=0):
        return [0.0, 0.0] # on non-UNIX platforms cpu_time always 0.0

p_stats = None
p_start_time = None

def profiler(frame, event, arg):
    if event not in ('call','return'): return profiler
    #### gather stats ####
    rusage = getrusage(RUSAGE_SELF)
    t_cpu = rusage[0] + rusage[1] # user time + system time
    code = frame.f_code 
    fun = (code.co_name, code.co_filename, code.co_firstlineno)
    #### get stack with functions entry stats ####
    ct = threading.currentThread()
    try:
        p_stack = ct.p_stack
    except AttributeError:
        ct.p_stack = deque()
        p_stack = ct.p_stack
    #### handle call and return ####
    if event == 'call':
        p_stack.append((time(), t_cpu, fun))
    elif event == 'return':
        try:
            t,t_cpu_prev,f = p_stack.pop()
            assert f == fun
        except IndexError: # TODO investigate
            t,t_cpu_prev,f = p_start_time, 0.0, None
        call_cnt, t_sum, t_cpu_sum = p_stats.get(fun, (0, 0.0, 0.0))
        p_stats[fun] = (call_cnt+1, t_sum+time()-t, t_cpu_sum+t_cpu-t_cpu_prev)
    return profiler


def profile_on():
    global p_stats, p_start_time
    p_stats = {}
    p_start_time = time()
    threading.setprofile(profiler)
    sys.setprofile(profiler)


def profile_off():
    threading.setprofile(None)
    sys.setprofile(None)

def get_profile_stats():
    """
    returns dict[function_tuple] -> stats_tuple
    where
      function_tuple = (function_name, filename, lineno)
      stats_tuple = (call_cnt, real_time, cpu_time)
    """
    return p_stats

@skip
class TestToolGccSpeed( AqlTestCase ):

  def test_gcc_compiler_speed(self):
    
    #~ profile_on()
    
    event_manager.setHandlers( EventHandler() )
    
    root_dir = FilePath("D:\\build_bench")
    build_dir = root_dir.join('build')
    
    #//-------------------------------------------------------//
    
    options = builtinOptions()
    options.update( gccOptions() )
    
    options.cxx = "C:\\MinGW32\\bin\\g++.exe"
    
    options.build_dir_prefix = build_dir
    
    cpp_compiler = GccCompileCppBuilder( None, options )
  
    #//-------------------------------------------------------//
    
    vfilename = root_dir.join( '.aql.values' )
    
    bm = BuildManager( vfilename, 4, True )
    
    options.cpppath += root_dir
    
    for i in range(200):
      src_files = [root_dir + '/lib_%d/class_%d.cpp' % (i, j) for j in range(20)]
      for src_file in src_files:
        obj = Node( cpp_compiler, FileValue( src_file ) )
        bm.addNodes( obj )
    
    bm.build()
    
    event_manager.finish()
    
    #~ profile_off()
    
    #~ stats = list( get_profile_stats().copy().items() )
    #~ stats.sort( key = lambda location: location[1][1], reverse = True )
    
    #~ for location, times in stats[:40]:
      #~ print( ' {location:<70}:  {times}'.format(location = str(location), times = str(times)) )

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
