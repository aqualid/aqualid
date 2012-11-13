import sys
import os.path
import itertools
import tempfile

from aql_utils import execCommand, toSequence, findProgram
from aql_errors import ProgramNotFound

#//===========================================================================//

class RemoteHost (object):
  __slots__ = ('address', 'login', 'key_file')
  
  def   __init__( self, host, login, key_file ):
    self.address = address
    self.login = login
    self.key_file = key_file
  
  def   remotePath( self, path ):
    return "%s@%s:%s" % (self.login, self.address, path)

#//===========================================================================//

class   PathNormalizer( object ):
  __slots__ = (
    'local_path_sep',
    'remote_path_sep',
    'cygwin_paths'
  )
  
  #//-------------------------------------------------------//
  
  def   __init__(self, remote_path_sep = '/', local_path_sep = os.path.sep, cygwin_paths = False ):
    if cygwin_paths:
      local_path_sep = '/'
      remote_path_sep = '/'
    
    self.cygwin_paths = cygwin_paths
    self.local_path_sep = local_path_sep
    self.remote_path_sep = remote_path_sep
    
  #//-------------------------------------------------------//
  
  class _NormPath( str ):  pass
  
  def   __normPath( self, path, path_sep ):
    
    if isinstance( path, self._NormPath ):
      return path
    
    if not path:
      path = '.'
    
    if self.cygwin_paths:
      drive, path = os.path.splitdrive( path )
      if drive.find(':') == 1:
        drive = "/cygdrive/" + drive[0]
      path = drive + path
    
    path = path.replace('\\', '/')
    if path[-1] == '/':
      last_sep = path_sep
    else:
      last_sep = ''
    
    path = os.path.normcase( os.path.normpath( path ) )
    if path_sep != os.path.sep:
      if path_sep == '/':
        path = path.replace('\\', '/')
      else:
        path = path.replace('/', '\\')
    
    return self._NormPath( path + last_sep )
  
  #//-------------------------------------------------------//
  
  def   localPath( self, path ):
    path = self.__normPath( path, self.local_path_sep )
    return path
  
  def   remotePath( self, path ):
    path = self.__normPath( path, self.remote_path_sep )
    return path


#//===========================================================================//

class   RemotePathMapping (object):
    __slots__ = (
      'local_paths',
      'remote_paths',
      'local_path_sep',
      'remote_path_sep',
      'cygwin_paths'
      )
    
    #//-------------------------------------------------------//
    
    def   __normPath( self, path, path_sep ):
      if not path:
        path = '.'
      
      if self.cygwin_paths:
        drive, path = os.path.splitdrive( path )
        if drive.find(':') == 1:
          drive = "/cygdrive/" + drive[0]
        path = drive + path
      
      path = path.replace('\\', '/')
      if path[-1] == '/':
        last_sep = path_sep
      else:
        last_sep = ''
      
      path = os.path.normpath( path )
      if path_sep != os.path.sep:
        if path_sep == '/':
          path = path.replace('\\', '/')
        else:
          path = path.replace('/', '\\')
      
      return path + last_sep
    
    #//-------------------------------------------------------//
    
    @staticmethod
    def   __fixPathSep( path, paths, sep ):
      if path[-1] == sep:
        return path
      
      for p, other in paths:
        if path.startswith( p ):
          break
        
        if ((p[-1] == sep) and p[:-1] == path):
          return p
      
      return path
    
    #//-------------------------------------------------------//
    
    def   normLocalPath( self, path ):
      path = self.__normPath( path, self.local_path_sep )
      path = self.__fixPathSep( path, self.local_paths, self.local_path_sep )
      return path
    
    def   normRemotePath( self, path ):
      path = self.__normPath( path, self.remote_path_sep )
      path = self.__fixPathSep( path, self.remote_paths, self.remote_path_sep )
      return path
    
    #//-------------------------------------------------------//
    
    def   __init__(self, mappings = {}, remote_path_sep = '/', local_path_sep = os.path.sep, cygwin_paths = False ):
      
      self.local_paths = []
      self.remote_paths = []
      
      if cygwin_paths:
        local_path_sep = '/'
        remote_path_sep = '/'
      
      self.cygwin_paths = cygwin_paths
      self.local_path_sep = local_path_sep
      self.remote_path_sep = remote_path_sep
      
      try:
        mappings = mappings.items()
      except AttributeError:
        pass
      
      self.local_paths = []
      self.remote_paths = []
      
      for local_path, remote_path in mappings:
        self.add( local_path, remote_path )
    
    #//-------------------------------------------------------//
    
    def   add( self, local_path, remote_path ):
      local_path = self.normLocalPath( local_path )
      remote_path = self.normRemotePath( remote_path )
      
      if remote_path[-1] == self.remote_path_sep:
        if local_path[-1] != self.local_path_sep:
          local_path += self.local_path_sep
      
      remove_locals = []
      
      for lpaths in self.local_paths:
        if (lpaths[0] == local_path) or (lpaths[1] == remote_path):
          remove_locals.append( lpaths )
      
      for lpaths in remove_locals:
        self.local_paths.remove( lpaths )
      
      remove_remotes = []
      
      for rpaths in self.remote_paths:
        if (rpaths[1] == local_path) or (rpaths[0] == remote_path):
          remove_remotes.append( rpaths )
      
      for rpaths in remove_remotes:
        self.remote_paths.remove( rpaths )
      
      self.local_paths.append( (local_path, remote_path) )
      self.remote_paths.append( (remote_path, local_path) )
      
      self.local_paths.sort( key = lambda v: len(v[0]), reverse = True )
      self.remote_paths.sort( key = lambda v: len(v[0]), reverse = True )
    
    #//-------------------------------------------------------//
    
    @staticmethod
    def   __mapPath( src_path, src_paths, norm_dstpath ):
      for spath, dpath in src_paths:
        if src_path.startswith( spath ) or ((spath[-1] in ['/', '\\']) and spath[:-1] == src_path):
          common_path = src_path[len(spath):]
          if common_path:
            return norm_dstpath( dpath + '/' + common_path )
          return dpath
      
      return ''
    
    #//-------------------------------------------------------//
    
    def   localPaths( self ):
      return tuple( map( lambda v: v[0], self.local_paths) )
    
    #//-------------------------------------------------------//
    
    def   remotePaths( self ):
      return tuple( map( lambda v: v[0], self.remote_paths) )
    
    #//-------------------------------------------------------//
    
    def   localPath( self, remote_path ):
      remote_path = self.normRemotePath( remote_path )
      return self.__mapPath( remote_path, self.remote_paths, self.normLocalPath )
    
    def   remotePath( self, local_path ):
      local_path = self.normLocalPath( local_path )
      return self.__mapPath( local_path, self.local_paths, self.normRemotePath )
    
    def   _localPath( self, remote_path ):
      return self.__mapPath( remote_path, self.remote_paths, self.normLocalPath )
    
    def   _remotePath( self, local_path ):
      return self.__mapPath( local_path, self.local_paths, self.normRemotePath )

#//===========================================================================//

class   Rsync( object ):
  
  __slots__ = (
    'cmd',
    'host',
    'path_normalizer',
    'env',
  )
  
  def   __init__( self, rsync, host, cygwin_paths = False, env = None ):
    
    if not rsync:
      rsync = findProgram( 'rsync', env )
      if rsync is None:
        raise ProgramNotFound( 'rsync', env )
    
    self.cmd = (rsync, '-avzubsX')
    self.host = host if host else None
    self.path_normalizer = PathNormalizer( cygwin_paths = cygwin_paths )
    self.env = env
  
  #//-------------------------------------------------------//
  
  def   __sync( self, local_files, local_path, remote_path, sync_local, exclude ):
    
    remote_path = self.normRemotePath( remote_path )
    local_path = self.normLocalPath( local_path )
    if local_files:
      local_files = self.__normLocalFiles( local_files, local_path[0] )
    
    cmd = list( self.cmd )
    
    excludes = []
    
    for args in itertools.product( ['--exclude'], toSequence( exclude ) ):
      excludes += args
    
    if excludes:
      cmd += excludes
      cmd.append('--delete-excluded')
    
    host = self.host
    if host:
      remote_path = map( host.remotePath, remote_path )
      cmd += [ '-e', 'ssh -o StrictHostKeyChecking=no -i ' + str(self.host.key_file) ]
    
    tmp_r, tmp_w = None, None
    try:
      if sync_local:
        cmd += remote_path
        cmd += local_path
      else:
        if local_files:
          tmp_r, tmp_w = os.pipe()
          os.write( tmp_w, '\n'.join( local_files ).encode('utf-8') )
          os.close( tmp_w )
          tmp_w = None
          cmd.append( "--files-from=-" )
        
        cmd += local_path
        cmd += remote_path
      
      result = execCommand( cmd, env = self.env, stdin = tmp_r )
      if result.failed():
        raise result
    
    finally:
      if tmp_r: os.close( tmp_r )
      if tmp_w: os.close( tmp_w )
    
  #//-------------------------------------------------------//
  
  def   __normLocalFiles( self, local_files, local_path ):
    
    norm_lpath = self.path_normalizer.localPath
    
    files = []
    
    for file in toSequence( local_files ):
      file = norm_lpath( file )
      if file.startswith( local_path ):
        file = file[len(local_path):]
      
      files.append( file )
    
    return files
  
  #//-------------------------------------------------------//
  
  def   normLocalPath( self, local_path ):
    norm_path = self.path_normalizer.localPath
    return tuple( norm_path(path) for path in toSequence(local_path) )
  
  #//-------------------------------------------------------//
  
  def   normRemotePath( self, remote_path ):
    norm_path = self.path_normalizer.remotePath
    return tuple( norm_path(path) for path in toSequence( remote_path ) )
  
  #//-------------------------------------------------------//
  
  def   get( self, local_path, remote_path, exclude = None ):
    self.__sync( None, local_path, remote_path, sync_local = True, exclude = exclude )
  
  #//-------------------------------------------------------//
  
  def   put( self, local_path, remote_path, exclude = None, local_files = None ):
    self.__sync( local_files, local_path, remote_path, sync_local = False, exclude = exclude )

#//===========================================================================//
