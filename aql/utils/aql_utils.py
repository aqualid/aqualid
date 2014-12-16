#
# Copyright (c) 2011-2014 The developers of Aqualid project
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

__all__ = (
  'openFile', 'readBinFile', 'readTextFile', 'writeBinFile', 'writeTextFile', 'execFile', 'removeFiles',
  'newHash', 'dumpSimpleObject', 'simpleObjectSignature', 'objectSignature', 'dataSignature',
  'fileSignature', 'fileTimeSignature', 'fileChecksum',
  'loadModule',
  'getFunctionName', 'printStacks', 'equalFunctionArgs', 'checkFunctionArgs', 'getFunctionArgs',
  'executeCommand', 'ExecCommandResult', 'getShellScriptEnv', 
  'cpuCount', 'memoryUsage',
  'flattenList', 'simplifyValue',
  'Chrono', 'ItemsGroups', 'groupItems'
)

import io
import os
import re
import imp
import sys
import time
import types
import errno
import marshal
import hashlib
import inspect
import tempfile
import traceback
import threading
import subprocess
import multiprocessing

try:
  import cPickle as pickle
except ImportError:
  import pickle

from aql.util_types import uStr, isString, isUnicode, toUnicode, decodeBytes, encodeStr, UniqueList, toSequence, isSequence, \
                           AqlException, SIMPLE_TYPES_SET 

#//===========================================================================//

#noinspection PyUnusedLocal
class   ErrorInvalidExecCommand( AqlException ):
  def   __init__( self, arg ):
    msg = "Invalid type of command argument: %s(%s)" % (arg,type(arg))
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorFileName( AqlException ):
  def   __init__( self, filename ):
    msg = "Invalid file name: %s(%s)" % (filename,type(filename))
    super(type(self), self).__init__( msg )
#//===========================================================================//

class   ErrorUnmarshallableObject( AqlException ):
  def   __init__( self, obj ):
    msg = "Unmarshallable object: '%s'" % (obj, )
    super(type(self), self).__init__( msg )

#//===========================================================================//

if hasattr(os, 'O_NOINHERIT'):
  _O_NOINHERIT = os.O_NOINHERIT
else:
  _O_NOINHERIT = 0

if hasattr(os, 'O_SYNC'):
  _O_SYNC = os.O_SYNC
else:
  _O_SYNC = 0

if hasattr(os, 'O_BINARY'):
  _O_BINARY = os.O_BINARY
else:
  _O_BINARY = 0

#//---------------------------------------------------------------------------//

def   openFile( filename, read = True, write = False, binary = False, sync = False, encoding = None ):
  
  if not isString( filename ):
    raise ErrorFileName( filename )
  
  flags = _O_NOINHERIT | _O_BINARY
  mode = 'r'
  
  if not write:
    flags |= os.O_RDONLY
    sync = False
  else:
    flags |= os.O_CREAT
    mode += '+'
    
    if read:
      flags |= os.O_RDWR
    else:
      flags |= os.O_WRONLY
    
    if sync:
      flags |= _O_SYNC
    
  if binary:
    mode += 'b'

  fd = os.open( filename, flags )
  try:
    if sync:
      #noinspection PyTypeChecker
      return io.open( fd, mode, 0, encoding = encoding )
    else:
      #noinspection PyTypeChecker
      return io.open( fd, mode, encoding = encoding )
  except:
    os.close( fd )
    raise

#//===========================================================================//

def readTextFile( filename, encoding = 'utf-8' ):
  with openFile( filename, encoding = encoding ) as f:
    return f.read()

def readBinFile( filename ):
  with openFile( filename, binary = True ) as f:
    return f.read()

def writeTextFile( filename, data, encoding = 'utf-8' ):
  with openFile( filename, write = True, encoding = encoding ) as f:
    f.truncate()
    if isinstance( data, (bytearray, bytes) ):
      data = decodeBytes( data, encoding )
    f.write( data )

def writeBinFile( filename, data, encoding = None ):
  with openFile( filename, write = True, binary = True, encoding = encoding ) as f:
    f.truncate()
    if isUnicode( data ):
      data = encodeStr( data, encoding )

    f.write( data )

#//===========================================================================//

def   execFile( filename, file_locals ):
  
  if not file_locals:
    file_locals = {}

  source = readTextFile( filename )
  code = compile( source, filename, 'exec' )
  file_locals_orig = file_locals.copy()
  
  exec( code, file_locals )

  result = {}
  for key,value in file_locals.items():
    if key.startswith('_') or isinstance( value, types.ModuleType ):
      continue
    
    if key not in file_locals_orig:
      result[ key ] = value
  
  return result

#//===========================================================================//

def   dumpSimpleObject( obj ):
  
  if isinstance( obj, (bytes, bytearray) ):
    data = obj
  
  elif isinstance( obj, uStr ):
    data = obj.encode('utf-8')
  
  else:
    try:
      data = marshal.dumps( obj )
    except ValueError:
      raise ErrorUnmarshallableObject( obj )
  
  return data

#//===========================================================================//

def   dumpObject( obj ):
  return pickle.dumps( obj, protocol = pickle.HIGHEST_PROTOCOL )

#//===========================================================================//

def   simpleObjectSignature( obj, common_hash = None ):
  data = dumpSimpleObject( obj )
  return dataSignature( data, common_hash )

#//===========================================================================//

def   objectSignature( obj, common_hash = None ):
  data = dumpObject( obj )
  return dataSignature( data, common_hash )

#//===========================================================================//

def   newHash( data = b'' ):
  return hashlib.md5( data )

#//===========================================================================//

def   dataSignature( data, common_hash = None ):
  if common_hash is None:
    obj_hash = hashlib.md5( data )
  else:
    obj_hash = common_hash.copy()
    obj_hash.update( data )
  
  return obj_hash.digest()

#//===========================================================================//

def   fileSignature( filename ):
  
  checksum = hashlib.md5()
  chunk_size = checksum.block_size * 4096
  
  with openFile( filename, binary = True ) as f:
    read = f.read
    checksum_update = checksum.update
    
    chunk = True
    
    while chunk:
      chunk = read( chunk_size )
      checksum_update( chunk )

  # print("fileSignature: %s: %s" % (filename, checksum.hexdigest()) )
  return checksum.digest()

#//===========================================================================//

def   fileTimeSignature( filename ):
  stat = os.stat( filename )
  # print("fileTimeSignature: %s: %s" % (filename, (stat.st_size, stat.st_mtime)) )
  return simpleObjectSignature( (stat.st_size, stat.st_mtime) )

#//===========================================================================//

def   fileChecksum( filename, offset = 0, size = -1, alg = 'md5', chunk_size = 262144 ):
  
  checksum = hashlib.__dict__[alg]()
  
  with openFile( filename, binary = True ) as f:
    read = f.read
    f.seek( offset )
    checksum_update = checksum.update
    
    chunk = True
    
    while chunk:
      chunk = read( chunk_size )
      checksum_update( chunk )
      
      if size > 0:
        size -= len(chunk)
        if size <= 0:
          break
      
      checksum_update( chunk )
  
  return checksum

#//===========================================================================//

def   getFunctionName( currentframe = inspect.currentframe ):
  
  frame = currentframe()
  if frame:
    return frame.f_back.f_code.co_name
  
  return "__not_available__"
  
  #~ try:
    #~ raise Exception()
  #~ except Exception as err:
    #~ return err.__traceback__.tb_frame.f_back.f_code.co_name

#//===========================================================================//

def   printStacks():
  id2name = dict([(th.ident, th.name) for th in threading.enumerate()])

  #noinspection PyProtectedMember
  for thread_id, stack in sys._current_frames().items():
    print("\n" + ("=" * 64) )
    print("Thread: %s (%s)" % (id2name.get(thread_id,""), thread_id))
    traceback.print_stack(stack)


#//===========================================================================//

try:
  #noinspection PyUnresolvedReferences
  _getargspec = inspect.getfullargspec
except AttributeError:
  _getargspec = inspect.getargspec

#//===========================================================================//

def   getFunctionArgs( function, getargspec = _getargspec ):
  
  args = getargspec( function )[:4]
  
  if type(function) is types.MethodType:
    if function.__self__:
      args = tuple( [ args[0][1:] ] + list(args[1:]) ) 
  
  return args

#//===========================================================================//

def   equalFunctionArgs( function1, function2 ):
  if function1 is function2:
    return True
  
  return getFunctionArgs( function1 )[0:3] == getFunctionArgs( function2 )[0:3]

#//===========================================================================//

def   checkFunctionArgs( function, args, kw, getargspec = _getargspec):
  
  f_args, f_varargs, f_varkw, f_defaults = getargspec( function )[:4]
  
  current_args_num = len(args) + len(kw)
  
  args_num = len(f_args)
  
  if not f_varargs and not f_varkw:
    if current_args_num > args_num:
      return False
  
  if f_defaults:
    def_args_num = len(f_defaults)
  else:
    def_args_num = 0
  
  min_args_num = args_num - def_args_num
  if current_args_num < min_args_num:
    return False
  
  kw = set(kw)
  unknown_args = kw - set(f_args)
  
  if unknown_args and not f_varkw:
    return False
  
  def_args = f_args[args_num - def_args_num:]
  non_def_kw = kw - set(def_args)
  
  non_def_args_num = len(args) + len(non_def_kw)
  if non_def_args_num < min_args_num:
    return False
  
  twice_args = set(f_args[:len(args)]) & kw
  if twice_args:
    return False
  
  return True

#//===========================================================================//

def   removeFiles( files ):
  
  for f in toSequence( files ):
    try:
      os.remove( f )
    except OSError as ex:
      if ex.errno != errno.ENOENT:
        raise

#//===========================================================================//

def _decodeData( data ):
  if not data:
    return str()
  
  data = toUnicode( data )
    
  data = data.replace('\r\n', '\n')
  data = data.replace('\r', '\n')
  
  return data

#//===========================================================================//

class   ExecCommandException( AqlException ):
  __slots__ = ('exception',)

  def   __init__( self, cmd, exception ):
    
    msg = ' '.join( toSequence(cmd) )
    msg += '\n%s' % (exception,)
    
    self.exception = exception
    
    super(type(self), self).__init__( msg )
  
  def   failed( self ):
    return True
  
  def   __bool__( self ):
    return self.failed()
  
  def   __nonzero__( self ):
    return self.failed()

  
class   ExecCommandResult( AqlException ):
  __slots__ = ('cmd', 'status', 'output' )
  
  def   __init__( self, cmd, status = None, stdout = None, stderr = None ):
    
    self.cmd = tuple(toSequence(cmd))
    self.status = status
    
    if not stdout:
      stdout = str()
    
    if stderr:
      stdout += '\n' + stderr
    
    self.output = stdout
    
    super(type(self), self).__init__()
  
  #//-------------------------------------------------------//
  
  def   __str__(self):
    msg = ' '.join( self.cmd )
    
    if self.output:
      msg += '\n' + self.output
    
    if self.status:
      msg += "\nExit status: %s" % (self.status,)
    
    return msg
  
  #//-------------------------------------------------------//
  
  def   failed( self ):
    return self.status != 0
  
  def   __bool__( self ):
    return self.failed()
  
  def   __nonzero__( self ):
    return self.failed()


try:
  _MAX_CMD_LENGTH = os.sysconf('SC_ARG_MAX')
except AttributeError:
  _MAX_CMD_LENGTH = 32000  # 32768 default for windows

#//===========================================================================//

def executeCommand( cmd, cwd = None, env = None, stdin = None, file_flag = None, max_cmd_length = _MAX_CMD_LENGTH ):
  
  cmd_file = None
  if isString(cmd):
    cmd = [ cmd ]
  
  for v in toSequence( cmd ):
    if not isString( v ):
      raise ErrorInvalidExecCommand( v )
  
  if file_flag:
    cmd_length = sum( map(len, cmd ) ) + len(cmd) - 1
    
    if cmd_length > max_cmd_length:
      args_str = subprocess.list2cmdline( cmd[1:] ).replace('\\', '\\\\')
      
      cmd_file = tempfile.NamedTemporaryFile( mode = 'w+', suffix = '.args', delete = False )
      
      cmd_file.write( args_str )
      cmd_file.close()
      
      cmd = [cmd[0], file_flag + cmd_file.name]
  
  try:
    
    try:
      p = subprocess.Popen( cmd, cwd = cwd, env = env,
                            stdin = stdin, stdout = subprocess.PIPE, stderr = subprocess.PIPE, universal_newlines = False )
      stdout, stderr = p.communicate()
      returncode = p.poll()
    except Exception as ex:
      raise ExecCommandException( cmd, exception = ex )
    
    stdout = _decodeData( stdout )
    stderr = _decodeData( stderr )
    
    return ExecCommandResult( cmd, status = returncode, stdout = stdout, stderr = stderr )
    
  finally:
    if cmd_file is not None:
      cmd_file.close()
      removeFiles( cmd_file.name )

#//===========================================================================//

def   getShellScriptEnv( script, args = None, _var_re = re.compile( r'^\w+=' ) ):
  
  args = toSequence( args )
  
  script = os.path.abspath( os.path.expanduser( os.path.expandvars(script) ) )
  
  os_env = os.environ
  
  cwd, script = os.path.split( script )
  
  if os.name == "nt":
    cmd = ['call', script ]
  else:
    cmd = ['.', script ]
  
  cmd += args
  cmd += ['&&', 'set']
  
  try:
    p = subprocess.Popen( cmd, cwd = cwd, shell = True, env = os_env,
                          stdin = None, stdout = subprocess.PIPE, stderr = subprocess.PIPE, universal_newlines = False )
    stdout, stderr = p.communicate()
    status = p.poll()
  except Exception as ex:
    raise ExecCommandException( cmd, exception = ex )
  
  stdout = _decodeData( stdout )
  stderr = _decodeData( stderr )
  
  if status != 0:
    raise ExecCommandResult( cmd, status, stdout, stderr )
  
  script_env = {}
  
  for line in stdout.split('\n'):
    match = _var_re.match( line )
    
    if match:
      name, sep, value = line.partition('=')
      value = value.strip()
      
      current = os_env.get( name, None )
      if (current is None) or (value != current.strip()):
        script_env[ name ] = value
  
  return script_env

#//===========================================================================//

def   cpuCount():
  
  try:
    return multiprocessing.cpu_count()
  except NotImplementedError:
    pass
  
  cpu_count = int(os.environ.get('NUMBER_OF_PROCESSORS', 0))
  if cpu_count:
    return cpu_count
  
  try:
    if 'SC_NPROCESSORS_ONLN' in os.sysconf_names:
      cpu_count = os.sysconf('SC_NPROCESSORS_ONLN')
    elif 'SC_NPROCESSORS_CONF' in os.sysconf_names:
      cpu_count = os.sysconf('SC_NPROCESSORS_CONF')
    if cpu_count:
      return cpu_count
  
  except AttributeError:
    pass
  
  cpu_count = 1 # unable to detect number of CPUs
  
  return cpu_count

#//===========================================================================//

def _memoryUsageSmaps():
  private = 0
  
  with open("/proc/self/smaps") as smaps:
    for line in smaps:
      if line.startswith("Private"):
        private += int(line.split()[1])
  
  return private

#//===========================================================================//

def _memoryUsageStatm():
  PAGESIZE = os.sysconf("SC_PAGE_SIZE")
  
  with open('/proc/self/statm') as f: 
    mem_stat = f.readline().split()
    rss = int(mem_stat[1]) * PAGESIZE  
    shared = int(mem_stat[2]) * PAGESIZE  
    
    private = rss - shared
  
  return private // 1024

#//===========================================================================//

def   memoryUsageLinux():
  try:
    return _memoryUsageSmaps()
  except IOError:
    try:
      return _memoryUsageStatm()
    except IOError:
      return memoryUsageUnix()

#//===========================================================================//

def memoryUsageUnix():
  res = resource.getrusage(resource.RUSAGE_SELF)
  return res.ru_maxrss

#//===========================================================================//

def memoryUsageWindows():
  process_handle = win32api.GetCurrentProcess()
  memory_info = win32process.GetProcessMemoryInfo( process_handle )
  return memory_info['PeakWorkingSetSize']

try:
  import resource
  
  if sys.platform[:5] == "linux":
    memoryUsage = memoryUsageLinux
  else:
    memoryUsage = memoryUsageUnix

except ImportError:
  try:
    import win32process
    import win32api
    
    memoryUsage = memoryUsageWindows
    
  except ImportError:
    def memoryUsage():
      return 0

#//===========================================================================//

def   loadModule( module_file, update_sys_path = True ):
  
  module_file = os.path.abspath( module_file )
  
  module_dir = os.path.dirname( module_file )
  module_name = os.path.splitext( os.path.basename( module_file ) )[0]
  
  fp, pathname, description = imp.find_module( module_name, [ module_dir ] )
  
  m = imp.load_module( module_name, fp, pathname, description )
  if update_sys_path:
    sys_path = sys.path
    try:
      sys_path.remove( module_dir )
    except ValueError:
      pass
    sys_path.insert( 0, module_dir )

  return m

#//===========================================================================//

def   flattenList( seq ):
  
  out_list = list( toSequence( seq ) )
  
  i = 0
  
  while i < len(out_list):
    
    value = out_list[i]
    
    if isSequence( value ):
      if value:
        out_list[i: i + 1] = value
      else:
        del out_list[i]
      
      continue
    
    i += 1
  
  return out_list

#//===========================================================================//

_SIMPLE_SEQUENCES = (list, tuple, UniqueList, set, frozenset)

def  simplifyValue( value, simple_types = SIMPLE_TYPES_SET, simple_lists = _SIMPLE_SEQUENCES ):
  
  if value is None:
    return None
  
  value_type = type(value)
  
  if value_type in simple_types:
    return value
  
  for simple_type in simple_types:
    if isinstance( value, simple_type ):
      return simple_type(value)
  
  if isinstance( value, simple_lists ):
    return [ simplifyValue( v ) for v in value ]
  
  if isinstance( value, dict ):
    return dict( (key, simplifyValue( v )) for key,v in value.items() )
  
  try:
    return simplifyValue( value.get() )
  except Exception:
    pass
  
  return value

#//===========================================================================//

class   Chrono (object):
  __slots__ = ('elapsed', )
  
  def   __init__(self):
    self.elapsed = 0
  
  def   __enter__(self):
    self.elapsed = time.time()
    return self
  
  def   __exit__(self, exc_type, exc_val, exc_tb):
    self.elapsed = time.time() - self.elapsed
    
    return False
  
  def   get(self):
    return self.elapsed
  
  def   __str__(self):
    elapsed = self.elapsed
    
    minutes = int(elapsed / 60)
    seconds = int(elapsed - minutes * 60)
    milisecs = int((elapsed - int(elapsed)) * 1000)
    
    result = []
    if minutes:
      result.append("%s min" % minutes)
      milisecs = 0
    
    if seconds:   result.append("%s sec" % seconds)
    if milisecs:  result.append("%s ms" % milisecs)
    
    return ' '.join( result )

#//===========================================================================//

class   ItemsGroups( object ):
  __slots__ = (
    'wish_groups',
    'max_group_size',
    'group_size',
    'tail_size',
    'groups',
  )
  
  def   __init__(self, size, wish_groups, max_group_size ):
    wish_groups = max( 1, wish_groups )
    
    group_size = size // wish_groups
    
    if max_group_size < 0:
      max_group_size = size
    elif max_group_size == 0:
      max_group_size = group_size + 1
    
    group_size = max( 1, group_size )
    
    self.wish_groups = wish_groups
    self.group_size = min( max_group_size, group_size )
    self.max_group_size = max_group_size
    self.tail_size = size
    self.groups = [[]]
  
  #//-------------------------------------------------------//
  
  def   addGroup( self ):
    
    groups = self.groups
    if not groups[0]:
      return
    
    group_size = max( 1, self.tail_size // max(1, self.wish_groups - len(self.groups) ) )
    self.group_size = min( self.max_group_size, group_size )
    
    group_files = []
    self.groups.append( group_files )
    return group_files
  
  #//-------------------------------------------------------//
  
  def   add(self, item ):
    group_files = self.groups[-1]
    if len(group_files) >= self.group_size:
      group_files = self.addGroup()
    
    group_files.append( item )
    self.tail_size -= 1
  
  #//-------------------------------------------------------//
  
  def   get(self):
    groups = self.groups
    if not groups[-1]:
      del groups[-1]
    
    return groups

#//===========================================================================//

def   groupItems( items, wish_groups = 1, max_group_size = -1 ):
  
  groups = ItemsGroups( len(items), wish_groups, max_group_size )
  for item in items:
    groups.add( item )
  
  return groups.get()

