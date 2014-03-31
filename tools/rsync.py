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

class RemotePath( object ):
  
  __slots__ = ('path', 'host', 'user')
  
  def   __init__(self, remote_path, host, user ):
    # [USER@]HOST:DEST
    remote_path = remote_path.strip()
    user_pos = remote_path.find('@')
    if user_pos != -1:
      user = remote_path[:user_pos]
      remote_path = remote_path[user_pos + 1:]
    
    host_pos = remote_path.find(':')
    if host_pos != -1:
      host = remote_path[:host_pos]
      remote_path = remote_path[host_pos + 1:]
    
    if host:
      remote_path = _normRemotePath( remote_path )
    else:
      remote_path = _normLocalPath( remote_path )
    
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
  
  def   get(self):
    if self.host:
      if self.user:
        return "%s@%s:%s" % (self.user, self.host, self.path)
      
      return "%s:%s" % (self.host, self.path)
    
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
    self.remote_path = RemotePath( remote_path, host, login )
    
    self.cmd = self.__getCmd( options, self.remote_path, key_file, exclude )
    self.rsync = options.rsync.get()
    
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __getCmd( options, remote_path, key_file, excludes ):
    cmd = [ options.rsync.get() ]
    
    cmd += options.rsync_flags.get()
    
    if excludes:
      cmd += itertools.chain( *itertools.product( ['--exclude'], aql.toSequence( excludes ) ) )
    
    if remote_path.isRemote():
      ssh_flags = options.rsync_ssh_flags.get()
      if key_file:
        ssh_flags += [ '-i', key_file ]
      
      cmd += [ '-e', 'ssh %s' % ' '.join( ssh_flags ) ]
    
    return cmd
  
  #//-------------------------------------------------------//
  
  def   _getSources(self, node ):
    
    sources = list( map(_normLocalPath, node.getBatchSources()) )
    
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
    host = remote_path.host
    user = remote_path.user
    remote_path = remote_path.path
    
    source_base = self.source_base
    
    value_type = aql.SimpleValue if host else self.fileValueType()
    
    for src_value, src in zip( node.getBatchSourceValues(), sources ):
      
      if not source_base:
        src = os.path.basename( src )
      
      path = remote_path + '/' + src
      target_path = RemotePath( path, host, user ).get()
      
      target_value = value_type( target_path )
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
      
      cmd.append( self.remote_path.get() )
      
      out = self.execCmd( cmd, env = self.env, stdin = tmp_r )
    
    finally:
      if tmp_r: os.close( tmp_r )
      if tmp_w: os.close( tmp_w )
    
    self._setTargets( node, sources )
    
    return out
  
  #//-------------------------------------------------------//
  
  def   getBuildBatchStrArgs( self, node, brief ):
    
    sources = tuple( map( _normLocalPath, node.getBatchSources() ) )
    target = self.remote_path
    
    if brief:
      name    = os.path.splitext( os.path.basename(self.cmd[0]) )[0]
      sources = tuple( map( os.path.basename, sources ) )
    else:
      name    = ' '.join( self.cmd )
    
    return name, sources, target

#//===========================================================================//

class RSyncPullBuilder (aql.Builder):
  # rsync -avzub --exclude-from=files.flt --delete-excluded -e "ssh -i dev.key" c4dev@dev:/work/cp/bp2_int/components .
  
  NAME_ATTRS = ('local_path', 'remote_path')
  
  def   __init__( self, action, options, local_path, remote_path, exclude = None ):
    do_get = bool(action == 'get')
    
    host = options.rsync_host.get()
    if host:
      host = aql.RemoteHost( host, options.rsync_login, options.rsync_key_file )
      host_address = host.address
    else:
      host_address = ''
    
    env = options.env.get().copy( value_type = str )
    
    rsync = aql.Rsync( rsync = options.rsync.get(), host = host, rsync_cygwin = options.rsync_cygwin.get(), env = env )
    
    self.rsync = rsync
    
    #//-------------------------------------------------------//
    
    if do_get:
      self.local_path = local_path
      self.remote_path = aql.toSequence( remote_path )
    else:
      self.local_path = aql.toSequence( local_path )
      self.remote_path = remote_path
    
    self.exclude = aql.toSequence( exclude )
    
    #//-------------------------------------------------------//
    
    cls = self.__class__
    
    if do_get:
      self.name = '.'.join( [ cls.__module__, cls.__name__, str(local_path) ] )
      self.signature = (host_address + '.' + ','.join( self.remote_path ) + '.' +  ','.join( self.exclude )).encode('utf-8')
    else:
      self.name = '.'.join( [ cls.__module__, cls.__name__, host_address, str( self.remote_path ) ] )
      self.signature = (','.join( self.local_path ) + '.' +  ','.join( self.exclude )).encode('utf-8')
    
    #//-------------------------------------------------------//
    
    if do_get:
      self.build = self.get
      self.buildStr = self.getStr
    else:
      self.build = self.put
      self.buildStr = self.putStr
  
  #//-------------------------------------------------------//
  
  def   get( self, build_manager, vfile, node ):
    
    local_path = self.local_path
    
    self.rsync.get( local_path, self.remote_path, exclude = self.exclude )
    if os.path.isdir( local_path ):
      target = DirValue( local_path )
    else:
      target = FileChecksumValue( local_path )
    
    return self.nodeTargets( target )
  
  #//-------------------------------------------------------//
  
  def   getStr( self, node ):
    if self.rsync.host:
      remote_path = ' '.join( map( self.rsync.host.remotePath, self.remote_path ) )
    else:
      remote_path = ' '.join( self.remote_path )
    
    return self.rsync.cmd[0] + ': ' + remote_path + ' > ' + str(self.local_path)
  
  #//-------------------------------------------------------//
  
  def   put( self, build_manager, vfile, node ):
    
    local_files = FilePaths( node.getSources() )
    
    local_path = self.local_path
    
    self.rsync.put( local_path, self.remote_path, exclude = self.exclude, local_files = local_files )
    return self.nodeTargets()   # no output targets
  
  #//-------------------------------------------------------//
  
  def   putStr( self, node ):
    host = self.rsync.host
    
    if host:
      local_path = ' '.join( map( host.localPath, self.local_path ) )
    else:
      local_path = ' '.join( self.local_path )
    
    return self.rsync.cmd[0] + ': ' + local_path + ' > ' + str(self.remote_path)

#//===========================================================================//

@aql.tool('rsync')
class ToolRsync( aql.Tool ):
  
  @staticmethod
  def   setup( options, env ):
    
    rsync = aql.whereProgram( 'rsync', env )
    
    options.rsync = rsync
    if not options.rsync_cygwin.isSet():
      options.rsync_cygwin = rsync.find( 'cygwin' ) != -1
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   options():
    
    options = aql.Options()
    
    options.rsync = aql.PathOptionType( description = "File path to rsync program." )
    options.rsync_cygwin = aql.BoolOptionType( description = "Is rsync uses cygwin paths." )
    
    # options.rsync_host = aql.StrOptionType( description = "Rsync remote host." )
    # options.rsync_login = aql.StrOptionType( description = "Rsync user's SSH login on the remote host." )
    # options.rsync_key_file = aql.PathOptionType( description = "Rsync user's SSH key file for the remote host." )
    
    options.rsync_flags = aql.ListOptionType( description = "rsync tool flags", separators = None )
    
    options.rsync_flags = ['-a', '-v', '-z', '-s' ]
    options.rsync_ssh_flags = ['-o', 'StrictHostKeyChecking=no', '-o', 'BatchMode=yes' ]
    
    options.setGroup( "rsync" )
    
    return options
    
  #//-------------------------------------------------------//
  
  def   Pull( self, options, target ):
    return RSyncPullBuilder( options, target )
  
  def   Push( self, options, target ):
    return aql.BuildBatch( RSyncPushBuilder( options, target ) )
