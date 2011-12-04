
import os.path
import fnmatch

#//===========================================================================//

def     isSequence( value, iter = iter ):
  try:
    iter( value )
    return True
  except TypeEror:
    pass
  
  return False

#//===========================================================================//

def     toSequence( value, iter = iter, tuple = tuple ):
  
  try:
    iter( value )
    return value
  except TypeEror:
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

def     toList( value,
                isinstance = isinstance,
                list = list,
                tuple = tuple ):
    
    if isinstance( value, list ):
        return value
    
    if isinstance( value, tuple ):
        return list(value)
    
    if value is None:
        return []
    
    return [ value ]

#//===========================================================================//

def     appendToListUnique( values_list, values ):
    for v in values:
        if not v in values_list:
            values_list.append( v )

#//===========================================================================//

def     appendToList( values_list, values, isSequence = isSequence ):
    if isSequence( values ):
        values_list += values
    else:
        values_list.append( values )

#//===========================================================================//

def     removeFromList( values_list, values ):
    for v in values:
        while 1:
            try:
                values_list.remove( v )
            except ValueError:
                break

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
