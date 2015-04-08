import os
import sys
import time
import datetime
import subprocess

#//===========================================================================//

def   _getPageSize():
  return os.sysconf('SC_PAGE_SIZE')

#//===========================================================================//

def _memoryUsageSmaps( pid ):
  private = 0
  
  with open("/proc/{pid}/smaps".format( pid = pid )) as smaps:
    for line in smaps:
      if line.startswith("Private"):
        private += int(line.split()[1])
  
  return private

#//===========================================================================//

def _memoryUsageStatm( pid, page_size ):
  
  with open('/proc/{pid}/statm'.format( pid = pid )) as f: 
    mem_stat = f.readline().split()
    rss = int(mem_stat[1]) * page_size
    shared = int(mem_stat[2]) * page_size
    
    private = rss - shared
  
  return private // 1024

#//===========================================================================//

def   _runProcess( cmd ):
  return subprocess.Popen( cmd, shell = False )

#//===========================================================================//

def  monitorProcess( p, outfile, interval ):
  
  page_size = _getPageSize()
  
  max_usage = 0
  last_usage = 0
  start = time.time()
  
  with open( outfile, 'w' ) as f:
    while True:
      try:
        usage = _memoryUsageStatm( p.pid, page_size )
      except IOError:
        break
      
      max_usage = max( max_usage, usage )
      
      if last_usage != usage:
        elapsed = time.time() - start
        f.write( "%s,%s\n" % (elapsed, usage) )
        last_usage = usage
      
      time.sleep( interval )
      result = p.poll()
      if result is not None:
        break
  
  return max_usage

#//===========================================================================//

if __name__ == '__main__':
  
  cmd = sys.argv[1:]
  now = datetime.datetime.now().strftime( "%y-%m-%d_%H:%M:%S")
  mem_report_filename = 'mem_usage_%s_%s.txt' % (os.path.basename(cmd[0]), now )
  current_time = time.time()
  
  interval = 0.25
  
  p = _runProcess( cmd )
  mem_peak = monitorProcess( p, mem_report_filename, interval )
  
  elapsed = time.time() - current_time
  
  print( "Memory usage report: %s" % (mem_report_filename,))
  print( "Peak memory usage: %s" % (mem_peak,))
  print( "Time: %s" % (elapsed,))
