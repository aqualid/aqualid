import sys
import os.path
import itertools

import aql

#//===========================================================================//

class   ErrorNoCommonSourcesDir( Exception ):
  def   __init__( self, sources ):
    msg = "Can't rsync disjoined files: %s" % (sources,)
    super(ErrorNoCommonSourcesDir, self).__init__( msg )

#//===========================================================================//

def  _toCygwinPath( path ):
  
  if not path:
    return '.'
  
  path_sep = '/'
  drive, path = aql.splitDrive( path )
  if drive.find(':') == 1:
    drive = "/cygdrive/" + drive[0]
  path = drive + path
  
  if path[-1] in ('\\', '/'):
    last_sep = path_sep
  else:
    last_sep = ''
  
  path = path.replace('\\', '/')
  
  return path + last_sep


#//===========================================================================//

def  _normLocalPath( path ):
  
  if not path:
    return '.'
  
  path_sep = os.path.sep
  
  path = str(path)
  
  if path[-1] in (path_sep, os.path.altsep):
    last_sep = path_sep
  else:
    last_sep = ''
  
  path = os.path.normcase( os.path.normpath( path ) )
  
  return path + last_sep

#//===========================================================================//

def  _normRemotePath( path ):
  
  if not path:
    return '.'
  
  path_sep = '/'
  
  if path[-1] in (path_sep, os.path.altsep):
    last_sep = path_sep
  else:
    last_sep = ''
  
  path = os.path.normpath( path ).replace( '\\', path_sep )
  
  return path + last_sep

#//===========================================================================//

def   _splitRemotePath( remote_path ):
  if os.path.isabs( remote_path ):
    host = ''
    user = ''
  else:
    # [USER@]HOST:DEST
    remote_path = remote_path.strip()
    user_pos = remote_path.find('@')
    if user_pos == -1:
      user = ''
    else:
      user = remote_path[:user_pos]
      remote_path = remote_path[user_pos + 1:]

    host_pos = remote_path.find(':')
    if host_pos == -1:
      host = ''
    else:
      host = remote_path[:host_pos]
      remote_path = remote_path[host_pos + 1:]

  remote_path = _normRemotePath( remote_path )

  return user, host, remote_path

#//===========================================================================//

class RemotePath( object ):
  
  __slots__ = ('path', 'host', 'user')
  
  def   __init__(self, remote_path, user = None, host = None ):
    
    u, h, remote_path = _splitRemotePath( remote_path )
    if not user:
      user = u
    
    if not host:
      host = h
    
    self.path = remote_path
    self.host = host
    self.user = user
  
  #//-------------------------------------------------------//
  
  def   isRemote(self):
    return bool(self.host)
  
  #//-------------------------------------------------------//
  
  def   __str__(self):
    return self.get()
  
  #//-------------------------------------------------------//

  def   join( self, other ):
    if self.host:
      path = self.path + '/' + _normRemotePath( other )
    else:
      path = os.path.join( self.path, _normLocalPath( other ) )

    return RemotePath( path, self.user, self.host )

  #//-------------------------------------------------------//

  def   basename(self):
    if self.host:
      last_slash_pos = self.path.rfind('/')
      return self.path[ last_slash_pos + 1: ]
    else:
      return os.path.basename( self.path )

  #//-------------------------------------------------------//

  def   get( self, cygwin_path = False ):
    if self.host:
      if self.user:
        return "%s@%s:%s" % (self.user, self.host, self.path)

      return "%s:%s" % (self.host, self.path)
    else:
      if cygwin_path:
        return _toCygwinPath( self.path )

      return self.path

#//===========================================================================//

"""
env.RsyncGet( remote_path = '/work/cp/kh', local_path = src_dir )

prog = env.LinkProgram( target = 'test', obj_files )

env.RsyncPut( prog, local_path = '', remote_path = '/work/cp/bin/' )

"""

class   RSyncPushBuilder( aql.FileBuilder ):
  # rsync -avzub --exclude-from=files.flt --delete-excluded -e "ssh -i dev.key" c4dev@dev:/work/cp/bp2_int/components .
  
  NAME_ATTRS = ('remote_path', 'source_base' )
  SIGNATURE_ATTRS = ( 'cmd', )
  
  def   __init__( self, options, remote_path, source_base = None, host = None, login = None, key_file = None, exclude = None ):
    
    self.rsync_cygwin = (sys.platform != 'cygwin') and options.rsync_cygwin.get()

    self.source_base = _normLocalPath( source_base ) if source_base else None
    self.remote_path = RemotePath( remote_path, login, host )
    
    self.cmd = self.__getCmd( options, key_file, exclude )
    self.rsync = options.rsync.get()
    
    self.file_value_type = aql.FileTimestampValue
    
  #//-------------------------------------------------------//
  
  def   __getCmd( self, options, key_file, excludes ):
    cmd = [ options.rsync.get() ]
    
    cmd += options.rsync_flags.get()
    
    if excludes:
      cmd += itertools.chain( *itertools.product( ['--exclude'], aql.toSequence( excludes ) ) )
    
    if self.remote_path.isRemote():
      ssh_flags = options.rsync_ssh_flags.get()
      if key_file:
        if self.rsync_cygwin:
          key_file = _toCygwinPath( key_file )
        ssh_flags += [ '-i', key_file ]
      
      cmd += [ '-e', 'ssh %s' % ' '.join( ssh_flags ) ]
    
    return cmd
  
  #//-------------------------------------------------------//
  
  def   _getSources(self, node ):
    
    sources = list( map(_normLocalPath, node.getSources()) )
    
    source_base = self.source_base
    if source_base:
      sources_base_len = len(source_base)
      for i, src in enumerate( sources ):
        if src.startswith( source_base ):
          src = src[sources_base_len:]
          if not src:
            src = '.'
          
          sources[i] = src
    
    return sources
  
  #//-------------------------------------------------------//
  
  def   _setTargets( self, node, sources ):
    
    remote_path = self.remote_path
    source_base = self.source_base
    
    value_type = aql.SimpleValue if remote_path.isRemote() else self.fileValueType()
    
    for src_value, src in zip( node.getSourceValues(), sources ):
      
      if not source_base:
        src = os.path.basename( src )

      target_path = remote_path.join( src )

      target_value = value_type( target_path.get() )
      node.setSourceTargets( src_value, target_value )
  
  #//-------------------------------------------------------//
  
  def   buildBatch( self, node ):
    sources = self._getSources( node )
    
    cmd = list( self.cmd )
    
    tmp_r, tmp_w = None, None
    try:
      if self.rsync_cygwin:
        sources = map( _toCygwinPath, sources ) 
      
      sorted_sources = sorted( sources )
      
      source_base = self.source_base
      
      if source_base:
        if self.rsync_cygwin:
          source_base = _toCygwinPath( source_base ) 
        
        tmp_r, tmp_w = os.pipe()
        os.write( tmp_w, '\n'.join( sorted_sources ).encode('utf-8') )
        os.close( tmp_w )
        tmp_w = None
        cmd += [ "--files-from=-", source_base ]
      else:
        cmd += sorted_sources

      remote_path = self.remote_path.get( self.rsync_cygwin )

      cmd.append( remote_path )
      
      out = self.execCmd( cmd, stdin = tmp_r )
    
    finally:
      if tmp_r: os.close( tmp_r )
      if tmp_w: os.close( tmp_w )
    
    self._setTargets( node, sources )
    
    return out
  
  #//-------------------------------------------------------//
  
  def   getTraceName( self, brief ):
    if brief:
      name = self.cmd[0]
      name = os.path.splitext( os.path.basename( name ) )[0]
    else:
      name = ' '.join( self.cmd )
    
    return name

#//===========================================================================//

class   RSyncPullBuilder( aql.Builder ):
  # rsync -avzub --exclude-from=files.flt --delete-excluded -e "ssh -i dev.key" c4dev@dev:/work/cp/bp2_int/components .
  
  NAME_ATTRS = ('target_path', )
  SIGNATURE_ATTRS = ( 'cmd', )
  
  def   __init__( self, options, target, host = None, login = None, key_file = None, exclude = None ):
    
    self.rsync_cygwin = (sys.platform != 'cygwin') and options.rsync_cygwin.get()

    self.target_path = _normLocalPath( target )
    self.host = host
    self.login = login
    
    self.cmd = self.__getCmd( options, key_file, exclude )
    self.rsync = options.rsync.get()
    
    self.file_value_type = aql.FileTimestampValue
    
  #//-------------------------------------------------------//

  def   makeValue(self, value, use_cache = False ):
    if aql.isString( value ):
      remote_path = RemotePath( value, self.login, self.host )
      if not remote_path.isRemote():
        return self.makeFileValue( value )

    return super( self, RSyncPullBuilder ).makeValue( value )

  #//-------------------------------------------------------//

  def   __getCmd( self, options, key_file, excludes ):
    cmd = [ options.rsync.get() ]
    
    cmd += options.rsync_flags.get()
    
    if excludes:
      cmd += itertools.chain( *itertools.product( ['--exclude'], aql.toSequence( excludes ) ) )
    
    if self.host:
      ssh_flags = options.rsync_ssh_flags.get()
      if key_file:
        if self.rsync_cygwin:
          key_file = _toCygwinPath( key_file )
        ssh_flags += [ '-i', key_file ]
      
      cmd += [ '-e', 'ssh %s' % ' '.join( ssh_flags ) ]
    
    return cmd
  
  #//-------------------------------------------------------//
  
  def   _getSourcesAndTargets( self, node ):
    
    sources = []
    targets = []
    target_path = self.target_path
    
    host = self.host
    login = self.login

    cygwin_path = self.rsync_cygwin

    for src in node.getSources():
      remote_path = RemotePath( src, login, host )

      path = os.path.join( target_path, remote_path.basename() )
      targets.append( path )
      sources.append( remote_path.get( cygwin_path ) )
          
    sources.sort()

    return sources, targets
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    sources, targets = self._getSourcesAndTargets( node )
    
    cmd = list( self.cmd )
    
    target_path = self.target_path
    
    if self.rsync_cygwin:
      target_path = _toCygwinPath( target_path ) 
      
    cmd += sources
      
    cmd.append( target_path )
      
    out = self.execCmd( cmd )
    
    node.setFileTargets( targets )
    
    return out
  
  #//-------------------------------------------------------//
  
  def   getTraceName( self, brief ):
    if brief:
      name = self.cmd[0]
      name = os.path.splitext( os.path.basename( name ) )[0]
    else:
      name = ' '.join( self.cmd )
    
    return name

#//===========================================================================//

@aql.tool('rsync')
class ToolRsync( aql.Tool ):
  
  @classmethod
  def   setup( cls, options, env ):
    
    rsync = aql.whereProgram( 'rsync', env )
    
    options.rsync = rsync
    if not options.rsync_cygwin.isSet():
      options.rsync_cygwin = rsync.find( 'cygwin' ) != -1
  
  #//-------------------------------------------------------//
  
  @classmethod
  def   options( cls ):
    options = aql.Options()
    
    options.rsync         = aql.PathOptionType( description = "File path to rsync program." )
    options.rsync_cygwin  = aql.BoolOptionType( description = "Is rsync uses cygwin paths." )
    
    options.rsync_flags = aql.ListOptionType( description = "rsync tool flags", separators = None )
    options.rsync_ssh_flags = aql.ListOptionType( description = "rsync tool SSH flags", separators = None )
    
    return options
  
  #//-------------------------------------------------------//
  
  def   __init__( self, options ):
    super(ToolRsync, self).__init__(options)
    
    options.rsync_flags = ['-a', '-v', '-z' ]
    options.rsync_ssh_flags = ['-o', 'StrictHostKeyChecking=no', '-o', 'BatchMode=yes' ]
    
    options.setGroup( "rsync" )

  
  #//-------------------------------------------------------//
  
  def   Pull( self, options, target, host = None, login = None, key_file = None, exclude = None ):
    return RSyncPullBuilder( options, target,
                             host = host, login = login,
                             key_file = key_file, exclude = exclude )

  
  def   Push( self, options, target, source_base = None, host = None, login = None, key_file = None, exclude = None ):
    
    builder = RSyncPushBuilder( options, target,
                                source_base = source_base,
                                host = host, login = login,
                                key_file = key_file, exclude = exclude )
    
    builder.setBatch()
    return builder
