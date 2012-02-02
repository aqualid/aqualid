
import sys
import os.path
import fnmatch
import hashlib
import threading
import traceback
import inspect

#//===========================================================================//

def     isSequence( value, iter = iter ):
  try:
    iter( value )
    return True
  except TypeError:
    pass
  
  return False

#//===========================================================================//

def     toSequence( value, iter = iter, tuple = tuple ):
  
  try:
    iter( value )
    return value
  except TypeError:
    pass
  
  if value is None:
      return tuple()
  
  return ( value, )

#//===========================================================================//

def     flattenList( values, isSequence = isSequence ):
  
  flatten_list = []
  for v in values:
    if isSequence( v ):
      flatten_list += flattenList( v )
    else:
      flatten_list.append( v )
  
  return flatten_list

#//===========================================================================//

def   fileChecksum( filename, offset = 0, size = -1, alg = 'md5', chunk_size = 262144 ):
  
  checksum = hashlib.__dict__[alg]()
  
  with open( filename, mode = 'rb' ) as f:
    read = f.read
    f.seek( offset )
    checksum_update = checksum.update
    while True:
      chunk = read( chunk_size )
      if not chunk:
        break
      
      if size > 0:
        size -= len(chunk)
        if size <= 0:
          break
      
      checksum_update( chunk )
  
  return checksum

#//===========================================================================//

def   getFunctionName( level = 1, getframe = sys._getframe ):
  return getframe( level ).f_code.co_name

#//===========================================================================//

def   printStacks():
  id2name = dict([(th.ident, th.name) for th in threading.enumerate()])
  
  for thread_id, stack in sys._current_frames().items():
    print("\n" + ("=" * 64) )
    print("Thread: %s (%s)" % (id2name.get(thread_id,""), thread_id))
    traceback.print_stack(stack)

#//===========================================================================//

def   equalFunctionArgs( function1, function2, getfullargspec = inspect.getfullargspec):
  fs1 = getfullargspec( function1 )
  fs2 = getfullargspec( function2 )
  
  return (fs1.args == fs2.args) and (fs1.varargs == fs2.varargs) and (fs1.varkw == fs2.varkw)

#//===========================================================================//

def   checkFunctionArgs( function, args, kw, getfullargspec = inspect.getfullargspec):
  fs = getfullargspec( function )
  current_args_num = len(args) + len(kw)
  
  args_num = len(fs.args)
  
  if not fs.varargs and not fs.varkw:
    if current_args_num > args_num:
      print("current_args_num: %s" % current_args_num )
      print("max_args_num: %s" % args_num )
      return False
  
  if fs.defaults:
    def_args_num = len(fs.defaults)
  else:
    def_args_num = 0
  
  min_args_num = args_num - def_args_num
  if current_args_num < min_args_num:
    print("current_args_num: %s" % current_args_num )
    print("min_args_num: %s" % min_args_num )
    return False
  
  kw = set(kw)
  unknown_args = kw - set(fs.args)
  
  if unknown_args and not fs.varkw:
    print("unknown_args: %s" % str(unknown_args))
    return False
  
  def_args = fs.args[args_num - def_args_num:]
  non_def_kw = kw - set(def_args)
  
  non_def_args_num = len(args) + len(non_def_kw)
  if non_def_args_num < min_args_num:
    print("non_def_args_num < min_args_num: %s" % str(non_def_args_num - min_args_num))
    return False
  
  twice_args = set(fs.args[:len(args)]) & kw
  if twice_args:
    print("twice_args: %s" % str(twice_args))
    return False
  
  return True


#//===========================================================================//

def     getShellScriptEnv( os_env, script ):
    
    import sys
    import os
    import popen2
    import re
    
    os_environ = os.environ
    
    if (sys.platform == "win32"):
        shell = os_environ.get("COMSPEC", "cmd.exe")
        script = 'call "' + script + '"'
    else:
        shell = '/bin/sh'
        script = '. ' + script
    
    cmdout, cmdin = popen2.popen2( shell )
    cmdin.write( script + "\n" )
    cmdin.write( "set\n" )
    cmdin.close()
    env = cmdout.readlines()
    cmdout.close()
    
    for arg in env:
        
        match = re.search(r'^\w+=', arg )
        
        if match:
            index = arg.find('=')
            name = arg[:index].upper()
            value = arg[index + 1:].rstrip('\n \t\r')
            
            current = os_environ.get( name )
            if (current is None) or (value != current):
                os_env[ name ] = value


#//===========================================================================//

def     normPath( path,
                  _os_path_normpath = os.path.normpath,
                  _os_path_normcase = os.path.normcase ):
    
    return _os_path_normcase( _os_path_normpath( path ) )

#//===========================================================================//

def     prependPath( oldpaths, newpaths, sep = os.pathsep,
                     normPath = normPath,
                     toSequence = toSequence,
                     isSequence = isSequence ):
    
    newpaths = map( normPath, toSequence( newpaths, sep ) )
    
    for p in toSequence( oldpaths, sep ):
        if p:
            p = normPath( p )
            if p not in newpaths:
                newpaths.append( p )
    
    if isSequence( oldpaths ):
        return newpaths
    
    return sep.join( newpaths )

#//===========================================================================//

def appendPath( oldpaths, newpaths, sep = os.pathsep,
                normPath = normPath,
                toSequence = toSequence,
                isSequence = isSequence ):
    
    newpaths = map( normPath, toSequence( newpaths, sep ) )
    
    unique_oldpaths = []
    for p in toSequence( oldpaths, sep ):
        if p:
            p = normPath( p )
            if (p not in newpaths) and (p not in unique_oldpaths):
                unique_oldpaths.append( p )
    
    paths = unique_oldpaths + newpaths
    
    if isSequence( oldpaths ):
        return paths
    
    return sep.join( paths )

#//===========================================================================//

def     appendEnvPath( os_env, names, value, sep = os.pathsep,
                       appendPath = appendPath,
                       toSequence = toSequence ):
    
    for name in toSequence( names ):
        os_env[ name ] = appendPath( os_env.get( name, '' ), value, sep )

#//===========================================================================//

def     prependEnvPath( os_env, names, value, sep = os.pathsep,
                        prependPath = prependPath,
                        toSequence = toSequence ):
    
    for name in toSequence( names ):
        os_env[ name ] = prependPath( os_env.get( name, '' ), value, sep )

#//===========================================================================//

def     findFiles( root, path, pattern, recursive = True ):
    
    abs_path = 1
    
    path = os.path.normpath( path )
    
    if not os.path.isabs( path ):
        abs_path = 0
        path = os.path.join( root, path )
    
    def     _walker( files, dirname, names ):
        
        match_files = fnmatch.filter( names, pattern )
        match_files = [ os.path.join( dirname, f) for f in match_files ]
        
        files += match_files
        
        if not recursive:
            del names[:]
    
    files = []
    os.path.walk( path, _walker, files )
    
    if not abs_path:
        strip_len = len(root)
        files = [ f[ strip_len : ].lstrip( os.path.sep ) for f in files ]
    
    files = map( os.path.normpath, files )
    return files
