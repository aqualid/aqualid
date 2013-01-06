#
# Copyright (c) 2011,2012 The developers of Aqualid project - http://aqualid.googlecode.com
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
  'isSequence', 'toSequence',
  'openFile', 'readBinFile', 'readTextFile', 'writeBinFile', 'writeTextFile', 'execFile',
  'fileSignature', 'fileChecksum', 'findFiles',
  'getFunctionName', 'printStacks', 'equalFunctionArgs', 'checkFunctionArgs', 'getFunctionArgs',
  'execCommand', 'ExecCommandResult', 'whereProgram', 'ErrorProgramNotFound', 'cpuCount',
)

import imp
import io
import os
import sys
import hashlib
import threading
import traceback
import inspect
import subprocess
import tempfile
import itertools

#//===========================================================================//

class   ErrorProgramNotFound( Exception ):
  def   __init__( self, program, env ):
    msg = "Program '%s' has not been found" % str(program)
    super(type(self), self).__init__( msg )

#//===========================================================================//

IS_WINDOWS = (os.name == 'nt')

#//===========================================================================//

def     isSequence( value, iter = iter, isinstance = isinstance, str = str ):
  try:
    if not isinstance( value, str ):
      iter( value )
      return True
  except TypeError:
    pass
  
  return False

#//===========================================================================//

def   toSequence( value, iter = iter, tuple = tuple, isinstance = isinstance, str = str ):
  
  try:
    if not isinstance( value, str ):
      iter( value )
      return value
  except TypeError:
    pass
  
  if value is None:
    return tuple()
  
  return ( value, )

#//===========================================================================//

if hasattr(os, 'O_NOINHERIT'):
  _O_NOINHERIT = os.O_NOINHERIT
else:
  _O_NOINHERIT = 0

if hasattr(os, 'O_SYNC'):
  _O_SYNC = os.O_SYNC
else:
  _O_SYNC = 0

def   openFile( filename, read = True, write = False, binary = False, sync = False, flags = _O_NOINHERIT ):
  
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
    flags |= os.O_BINARY
    
  fd = os.open( filename, flags )
  try:
    if sync:
      f = io.open( fd, mode, 0 )
    else:
      f = io.open( fd, mode )
  except:
    os.close( fd )
    raise
  
  return f

#//===========================================================================//

def readTextFile( filename ):
  with openFile( filename ) as f:
    return f.read()

def readBinFile( filename ):
  with openFile( filename, binary = True ) as f:
    return f.read()

def writeTextFile( filename, buf ):
  with openFile( filename, write = True ) as f:
    f.truncate()
    f.write( buf )

def writeBinFile( filename, buf ):
  with openFile( filename, write = True, binary = True ) as f:
    f.truncate()
    f.write( buf )

#//===========================================================================//

def   execFile( filename, locals ):
  source = readTextFile( filename )
  code = compile( source, filename, 'exec' )
  exec( code, {}, locals )

#//===========================================================================//

def   fileSignature( filename, chunk_size = hashlib.md5().block_size * (2 ** 12) ):
  
  checksum = hashlib.md5()
  
  with openFile( filename, binary = True ) as f:
    read = f.read
    checksum_update = checksum.update
    
    chunk = True
    
    while chunk:
      chunk = read( chunk_size )
      checksum_update( chunk )
  
  return checksum.digest()

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
  
  return "__not_avaiable__"
  
  #~ try:
    #~ raise Exception()
  #~ except Exception as err:
    #~ return err.__traceback__.tb_frame.f_back.f_code.co_name

#//===========================================================================//

def   printStacks():
  id2name = dict([(th.ident, th.name) for th in threading.enumerate()])
  
  for thread_id, stack in sys._current_frames().items():
    print("\n" + ("=" * 64) )
    print("Thread: %s (%s)" % (id2name.get(thread_id,""), thread_id))
    traceback.print_stack(stack)


#//===========================================================================//

try:
  _getargspec = inspect.getfullargspec
except AttributeError:
  _getargspec = inspect.getargspec

#//===========================================================================//

def   getFunctionArgs( function, getargspec = _getargspec ):
  return getargspec( function )[:4]

#//===========================================================================//

def   equalFunctionArgs( function1, function2, getargspec = _getargspec):
  if function1 is function2:
    return True
  
  return getargspec( function1 )[0:3] == getargspec( function2 )[0:3]

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

def  findFiles( paths = ".", prefixes = "", suffixes = "", ignore_dir_prefixes = ('__', '.') ):
  
  found_files = []
  
  paths = toSequence(paths)
  ignore_dir_prefixes = toSequence(ignore_dir_prefixes)
  
  prefixes = tuple( map( str, toSequence(prefixes) ) )
  suffixes = tuple( map( str, toSequence(suffixes) ) )
  ignore_dir_prefixes = tuple( map( str, toSequence(ignore_dir_prefixes) ) )
  
  prefixes = tuple( map( os.path.normcase, prefixes ) )
  suffixes = tuple( map( os.path.normcase, suffixes ) )
  ignore_dir_prefixes = tuple( map( os.path.normcase, ignore_dir_prefixes ) )
  
  if not prefixes: prefixes = ("", )
  if not suffixes: suffixes = ("", )
  
  for path in paths:
    for root, dirs, files in os.walk( path ):
      for file_name in files:
        file_name = os.path.normcase( file_name )
        for prefix, suffix in itertools.product( prefixes, suffixes ):
          if file_name.startswith( prefix ) and file_name.endswith( suffix ):
            found_files.append( os.path.abspath( os.path.join(root, file_name) ) )
      
      tmp_dirs = []
      
      for dir in dirs:
        ignore = False
        for dir_prefix in ignore_dir_prefixes:
          if dir.startswith( dir_prefix ):
            ignore = True
            break
        if not ignore:
          tmp_dirs.append( dir )
      
      dirs[:] = tmp_dirs
  
  return found_files

#//===========================================================================//

def _decodeData( data ):
  if not data:
    return str()
  
  try:
    codec = sys.stdout.encoding
  except AttributeError:
    codec = None
  
  if not codec:
    codec = 'utf-8'
  
  if not isinstance(data, str):
    data = data.decode( codec )
  
  return data

#//===========================================================================//

class   ExecCommandResult( Exception ):
  __slots__ = ('result', 'out', 'err', 'exception')
  
  def   __init__( self, cmd, exception = None, result = None, out = None, err = None ):
    msg = str()
    
    if exception:
      msg += str(exception) + ', '
    
    if result:
      msg += 'result: ' + str(result) + ', '
    
    cmd = ' '.join( toSequence(cmd) )
    
    if msg:
      msg = "Command failed: %s%s" % (msg, cmd)
      
      if err:
        msg += '\n' + err
      elif out:
        msg += '\n' + out
    
    self.exception = exception
    self.result = result
    self.out = out
    self.err = err
    
    super(type(self), self).__init__( msg )
  
  def   failed( self ):
    return (self.result != 0) or self.exception;
  
  def   __bool__( self ):
    return self.failed();
  
  def   __nonzero__( self ):
    return self.failed();

try:
  _MAX_CMD_LENGTH = os.sysconf('SC_ARG_MAX')
except AttributeError:
  _MAX_CMD_LENGTH = 32000  # 32768 default for windows

#//===========================================================================//

def execCommand( cmd, cwd = None, env = None, file_flag = None, max_cmd_length = _MAX_CMD_LENGTH, stdin = None ):
  
  cmd_file = None
  
  if file_flag:
    cmd_length = sum( map(len, cmd ) ) + len(cmd) - 1
    
    if cmd_length > max_cmd_length:
      args_str = subprocess.list2cmdline( cmd[1:] ).replace('\\', '\\\\')
      
      cmd_file = tempfile.NamedTemporaryFile( mode = 'w+', suffix = '.args', delete = False )
      
      cmd_file.write( args_str )
      cmd_file.close()
      
      cmd = [cmd[0], file_flag + cmd_file.name ]
  
  try:
    try:
      p = subprocess.Popen( cmd, stdin = stdin, stdout = subprocess.PIPE, stderr = subprocess.PIPE, cwd = cwd, env = env )
      (stdoutdata, stderrdata) = p.communicate()
      result = p.returncode
    except Exception as ex:
      raise ExecCommandResult( cmd, exception = ex )
    
    stdoutdata = _decodeData( stdoutdata )
    stderrdata = _decodeData( stderrdata )
    
    return ExecCommandResult( cmd, result = result, out = stdoutdata, err = stderrdata )
    
  finally:
    if cmd_file is not None:
      cmd_file.close()
      try:
        os.remove( cmd_file.name )
      except OSError as ex:
        if ex.errno != errno.ENOENT:
          raise

#//===========================================================================//

def   whereProgram( prog, env = None ):
  
  if env is None:
    env = os.environ
    paths = env.get('PATH', '')
    path_exts = env.get('PATHEXT', '' )
  else:
    paths = env.get('PATH', '')
    path_exts = env.get('PATHEXT', None )
    if not path_exts:
      path_exts = os.environ.get('PATHEXT', '')
  
  paths = paths.split( os.pathsep )
  
  #//-------------------------------------------------------//
  
  if path_exts:
    path_exts = path_exts.split( os.pathsep )
    if '' not in path_exts:
      if IS_WINDOWS:
        path_exts.append('')
      else:
        path_exts.insert(0,'')
  else:
    if IS_WINDOWS:
      path_exts = ('.exe','.cmd','.bat','.com', '')
    else:
      path_exts = ('','.sh','.py','.pl')
  
  #//-------------------------------------------------------//
  
  prog = tuple( toSequence( prog ) )
  
  for path in itertools.product( prog, path_exts, paths ):
    prog_path = os.path.normcase( os.path.expanduser( os.path.join( path[2], path[0] + path[1] ) ) )
    if os.path.isfile( prog_path ):
      return prog_path
  
  raise ErrorProgramNotFound( prog, env )

#//===========================================================================//

def   cpuCount():
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

def   loadModule( module_file, update_sys_path = True ):
  
  module_file = os.path.abspath( module_file )
  module_dir = os.path.dirname( module_file )
  module_name = os.path.splitext( os.path.basename( module_file ) )[0]
  
  fp, pathname, description = imp.find_module( module_name, [ module_dir ] )
  
  with fp:
    m = imp.load_module( module_name, fp, pathname, description )
    if update_sys_path:
      sys_path = sys.path
      try:
        sys_path.remove( module_dir )
      except ValueError:
        pass
      sys_path.insert( 0, module_dir )
    
    return m
