import os.path
import itertools

import aql

#//===========================================================================//

class   ErrorNoCommonSourcesDir( Exception ):
  def   __init__( self, sources ):
    msg = "Can't rsync disjoined files: %s" % (sources,)
    super(ErrorNoCommonSourcesDir, self).__init__( msg )

#//===========================================================================//

def  _normCygwinPath( path ):
  
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
  
  path = os.path.normcase( os.path.normpath( path ) )
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

def   _remoteHostPath( self, path, host, login ):
  if host:
    if login:
      return "%s@%s:%s" % (login, host, remote_path)
    
    return "%s:%s" % (host, remote_path)
  
  return path


#//===========================================================================//

"""
env.RsyncGet( remote_path = '/work/cp/kh', local_path = src_dir )

prog = env.LinkProgram( target = 'test', obj_files )

env.RsyncPut( prog, local_path = '', remote_path = '/work/cp/bin/' )

"""

class   RSyncPushBuilder( aql.FileBuilder ):
  # rsync -avzub --exclude-from=files.flt --delete-excluded -e "ssh -i dev.key" c4dev@dev:/work/cp/bp2_int/components .
  
  NAME_ATTRS = ('remote_path',)
  SIGNATURE_ATTRS = ( 'cmd', )
  
  def   __init__( self, options, remote_path, exclude = None ):
    
    normLocalPath = _normCygwinPath if options.rsync_cygwin.get() else _normLocalPath
    
    host = options.rsync_host.get()
    if host:
      login = options.rsync_login.get()
      remote_path = _normRemotePath( remote_path )
      self.remote_path = _remoteHostPath( remote_path, host, login )
    else:
      remote_path = normLocalPath( remote_path )
          
    self.cmd = self.__getCmd( options, exclude )
    self.normLocalPath = normLocalPath 
    
    self.rsync = options.rsync.get()
    
    #//-------------------------------------------------------//
    
    self.remote_path = remote_path
    
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __getCmd( options, excludes ):
    cmd = [ options.rsync.get() ]
    
    cmd += options.rsync_flags.get()
    
    if excludes:
      cmd += itertools.chain( *itertools.product( ['--exclude'], aql.toSequence( excludes ) ) )
    
    rsync_key_file = options.rsync_key_file.get()
    
    if rsync_key_file:
      cmd += [ '-e', 'ssh -o StrictHostKeyChecking=no -i ' + str(rsync_key_file) ]
    
    return cmd
  
  #//-------------------------------------------------------//
  
  def   buildBatch( self, node ):
    sources = sorted( map( _normLocalPath, node.getBatchSources() ) )
    
    sources_dir = aql.commonDirName( sources )
    if not sources_dir:
      raise ErrorNoCommonSourcesDir( sources )
    
    sources_dir_len = len(sources_dir)
    sources = [ src[sources_dir_len:] for src in sources ]
    
    if self.normLocalPath is not _normLocalPath: 
      sources = map( self.normLocalPath, sources )
      sources_dir = self.normLocalPath( sources_dir )
    
    cmd = list( self.cmd )
    
    tmp_r, tmp_w = None, None
    try:
      tmp_r, tmp_w = os.pipe()
      os.write( tmp_w, '\n'.join( sources ).encode('utf-8') )
      os.close( tmp_w )
      tmp_w = None
      cmd.append( "--files-from=-" )
      
      cmd += [ sources_dir, self.remote_path ]
      
      out = self.execCmd( cmd, env = self.env, stdin = tmp_r )
    
    finally:
      if tmp_r: os.close( tmp_r )
      if tmp_w: os.close( tmp_w )
    
    node.setNoTargets()
    
    return out
  
  #//-------------------------------------------------------//
  
  def   getBuildBatchStrArgs( self, node, brief ):
    
    sources = sorted( map( self.normLocalPath, node.getBatchSources() ) )
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
    
    options.rsync_host = aql.StrOptionType( description = "Rsync remote host." )
    options.rsync_login = aql.StrOptionType( description = "Rsync user's SSH login on the remote host." )
    options.rsync_key_file = aql.PathOptionType( description = "Rsync user's SSH key file for the remote host." )
    
    options.rsync_flags = aql.ListOptionType( description = "rsync tool flags", separators = None )
    
    options.rsync_flags = ['-a', '-v', '-z', '-s' ]
    
    options.setGroup( "rsync" )
    
    return options
    
  #//-------------------------------------------------------//
  
  def   Pull( self, options, target ):
    return RSyncPullBuilder( options, target )
  
  def   Push( self, options, target ):
    return aql.BuildBatch( RSyncPushBuilder( options, target ) )
